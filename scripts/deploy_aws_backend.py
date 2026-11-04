import json
import os
import tarfile
import tempfile
import time
from ipaddress import ip_network

import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-south-1")


admin_cidr = os.getenv("AWS_ADMIN_CIDR", "").strip()
if not admin_cidr or ip_network(admin_cidr).prefixlen == 0:
    raise SystemExit("Set AWS_ADMIN_CIDR to a trusted network before provisioning the API server.")

BUCKET_NAME = os.getenv("AWS_S3_BUCKET", "").strip()
if not BUCKET_NAME:
    raise SystemExit("Set AWS_S3_BUCKET before deploying the backend.")

print("=" * 60)
print(f"Deploying Application Backend to AWS EC2 [{REGION}]")
print("=" * 60)

# 1. AWS Clients
sts = boto3.client("sts", region_name=REGION)
account_id = sts.get_caller_identity()["Account"]
print(f"[AWS] Authenticated as Account: {account_id}")

s3 = boto3.client("s3", region_name=REGION)
ec2 = boto3.client("ec2", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)
ssm = boto3.client("ssm", region_name=REGION)

# 2. Package Backend Bundle
print("\n[Step 1/5] Packaging backend code bundle...")
tar_dir = os.path.join(tempfile.gettempdir(), "backend_deploy")
os.makedirs(tar_dir, exist_ok=True)
tar_path = os.path.join(tar_dir, "backend-backend.tar.gz")


def exclude_filter(tarinfo):
    name = tarinfo.name
    if any(
        x in name
        for x in ["__pycache__", ".pytest_cache", ".git", "venv", "node_modules", ".ds_store"]
    ):
        return None
    return tarinfo


with tarfile.open(tar_path, "w:gz") as tar:
    for item in ["src", "config", "requirements.txt", "pyproject.toml", ".env", "frontend/dist"]:
        if os.path.exists(item):
            print(f"  Adding: {item}")
            tar.add(item, arcname=item, filter=exclude_filter)

file_size_mb = os.path.getsize(tar_path) / (1024 * 1024)
print(f"  -> Created bundle: {tar_path} ({file_size_mb:.2f} MB)")

# Upload to S3
s3_key = "deploy/backend-backend.tar.gz"
print(f"  -> Uploading bundle to s3://{BUCKET_NAME}/{s3_key}...")
s3.upload_file(tar_path, BUCKET_NAME, s3_key)
print("  -> Upload completed successfully.")

# 3. Setup IAM Role & Instance Profile for EC2
print("\n[Step 2/5] Configuring EC2 IAM Role & Instance Profile...")
role_name = "ApplicationEC2Role"
profile_name = "ApplicationEC2Profile"

trust_doc = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}

try:
    iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_doc),
        Description="Role for Application Backend EC2 instance",
    )
    print(f"  -> Created IAM Role: {role_name}")
except iam.exceptions.EntityAlreadyExistsException:
    print(f"  -> IAM Role already exists: {role_name}")

# Attach standard managed policies
policies = [
    "arn:aws:iam::aws:policy/AmazonSQSFullAccess",
    "arn:aws:iam::aws:policy/AmazonSNSFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
]
for p in policies:
    try:
        iam.attach_role_policy(RoleName=role_name, PolicyArn=p)
    except Exception:
        pass

try:
    iam.create_instance_profile(InstanceProfileName=profile_name)
    print(f"  -> Created Instance Profile: {profile_name}")
except iam.exceptions.EntityAlreadyExistsException:
    print(f"  -> Instance Profile already exists: {profile_name}")

try:
    iam.add_role_to_instance_profile(InstanceProfileName=profile_name, RoleName=role_name)
    print(f"  -> Added {role_name} to {profile_name}")
    time.sleep(5)
except iam.exceptions.LimitExceededException:
    pass
except Exception as e:
    if "Cannot perform the operation on the role" not in str(e) and "already exists" not in str(e):
        print(f"  -> Note: {e}")

# 4. Security Group Configuration
print("\n[Step 3/5] Configuring Security Groups in Default VPC...")
vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
if not vpcs:
    vpcs = ec2.describe_vpcs()["Vpcs"]
default_vpc_id = vpcs[0]["VpcId"]
print(f"  -> VPC ID: {default_vpc_id}")

sg_name = "backend-backend-sg"
backend_sg_id = None
try:
    sg_res = ec2.create_security_group(
        GroupName=sg_name,
        Description="Security Group for Application Backend API & Inference Worker",
        VpcId=default_vpc_id,
    )
    backend_sg_id = sg_res["GroupId"]
    print(f"  -> Created Security Group: {backend_sg_id}")

    # Ingress rules: 80, 8080, 22
    ec2.authorize_security_group_ingress(
        GroupId=backend_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [{"CidrIp": admin_cidr, "Description": "HTTP"}],
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 8080,
                "ToPort": 8080,
                "IpRanges": [{"CidrIp": admin_cidr, "Description": "FastAPI Port"}],
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": admin_cidr, "Description": "SSH"}],
            },
        ],
    )
except ec2.exceptions.ClientError as e:
    if "InvalidGroup.Duplicate" in str(e):
        sgs = ec2.describe_security_groups(
            Filters=[
                {"Name": "group-name", "Values": [sg_name]},
                {"Name": "vpc-id", "Values": [default_vpc_id]},
            ]
        )["SecurityGroups"]
        backend_sg_id = sgs[0]["GroupId"]
        print(f"  -> Security Group already exists: {backend_sg_id}")
    else:
        raise e

# 5. Launch EC2 Instance
print("\n[Step 4/5] Launching Amazon Linux 2023 EC2 Instance...")
# Get latest AL2023 AMI
ami_param = ssm.get_parameter(
    Name="/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
)
ami_id = ami_param["Parameter"]["Value"]
print(f"  -> AMI: {ami_id} (Amazon Linux 2023 x86_64)")

# Check if there's already an active instance
existing_instances = ec2.describe_instances(
    Filters=[
        {"Name": "tag:Project", "Values": ["Application"]},
        {"Name": "instance-state-name", "Values": ["pending", "running"]},
    ]
)

instance_id = None
public_ip = None
public_dns = None

for res in existing_instances.get("Reservations", []):
    for inst in res.get("Instances", []):
        instance_id = inst["InstanceId"]
        public_ip = inst.get("PublicIpAddress")
        public_dns = inst.get("PublicDnsName")
        print(f"  -> Found existing running instance: {instance_id} at {public_ip}")
        break
    if instance_id:
        break

user_data_script = f"""#!/bin/bash
set -e
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "=== Starting Application Cloud Backend Deployment ==="

dnf update -y
dnf install -y gcc gcc-c++ git tar gzip iptables || true

if dnf install -y python3.11 python3.11-pip python3.11-devel; then
    PY_CMD=python3.11
else
    dnf install -y python3 python3-pip python3-devel
    PY_CMD=python3
fi
echo "Using Python: $PY_CMD"

# Port 80 redirect to 8080
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080 || true

mkdir -p /opt/backend
cd /opt/backend

echo "Fetching deployment bundle from S3..."
command -v aws >/dev/null 2>&1 || dnf install -y awscli
aws s3 cp s3://{BUCKET_NAME}/{s3_key} /tmp/backend-backend.tar.gz --region {REGION}
tar -xzf /tmp/backend-backend.tar.gz -C /opt/backend

echo "Setting up Python virtual environment..."
$PY_CMD -m venv /opt/backend/venv
source /opt/backend/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Create FastAPI Systemd Service
cat << 'EOF' > /etc/systemd/system/backend-api.service
[Unit]
Description=Application FastAPI REST API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/backend
Environment="PYTHONPATH=/opt/backend/src"
EnvironmentFile=/opt/backend/.env
ExecStart=/opt/backend/venv/bin/python -m uvicorn backend.api.routes:app --app-dir src --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create SQS Inference Worker Systemd Service
cat << 'EOF' > /etc/systemd/system/backend-inference.service
[Unit]
Description=Application Real-time SQS Spoilage Inference Worker
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/backend
Environment="PYTHONPATH=/opt/backend/src"
EnvironmentFile=/opt/backend/.env
ExecStart=/opt/backend/venv/bin/python -m backend.inference_service
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable backend-api
systemctl restart backend-api

systemctl enable backend-inference
systemctl restart backend-inference

touch /opt/backend/PROVISIONING_COMPLETE
echo "=== Application Cloud Backend Deployment Finished Successfully ==="
"""


if not instance_id:
    print(f"  -> Launching new t3.small instance in VPC {default_vpc_id}...")
    run_res = None
    for attempt in range(10):
        try:
            run_res = ec2.run_instances(
                ImageId=ami_id,
                InstanceType="t3.small",
                MinCount=1,
                MaxCount=1,
                SecurityGroupIds=[backend_sg_id],
                IamInstanceProfile={"Name": profile_name},
                UserData=user_data_script,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": "backend-backend-server"},
                            {"Key": "Project", "Value": "Application"},
                        ],
                    }
                ],
            )
            break
        except ec2.exceptions.ClientError as e:
            if "iamInstanceProfile" in str(e) and attempt < 9:
                print(f"  -> Waiting for IAM instance profile propagation ({attempt + 1}/10)...")
                time.sleep(6)
            else:
                raise e

    instance_id = run_res["Instances"][0]["InstanceId"]
    print(f"  -> Instance launched: {instance_id}. Waiting for instance to be running...")

    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])

    inst_desc = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]
    public_ip = inst_desc.get("PublicIpAddress")
    public_dns = inst_desc.get("PublicDnsName")
else:
    print(f"  -> Updating existing instance {instance_id} with new deployment...")
    command = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [user_data_script], "executionTimeout": ["900"]},
    )
    command_id = command["Command"]["CommandId"]
    print(f"  -> Updating backend services via SSM command {command_id}")
    ssm.get_waiter("command_executed").wait(
        CommandId=command_id,
        InstanceId=instance_id,
        WaiterConfig={"Delay": 10, "MaxAttempts": 90},
    )

print(f"\n[Step 5/5] Waiting for Backend API service to initialize at http://{public_ip}:8080 ...")
api_url = f"http://{public_ip}:8080"

# Poll health endpoint
max_attempts = 30
success = False
for attempt in range(1, max_attempts + 1):
    try:
        r = requests.get(f"{api_url}/health", timeout=5)
        if r.status_code == 200:
            print(f"  -> Backend API is LIVE! (Attempt {attempt}): {r.json()}")
            success = True
            break
    except Exception as e:
        print(f"  -> Provisioning in progress... attempt {attempt}/{max_attempts} ({e})")
    time.sleep(10)

if success:
    print("\n" + "=" * 60)
    print("APP CLOUD BACKEND SUCCESSFULLY DEPLOYED!")
    print(f"  Public API Base URL: {api_url}")
    print(f"  Health Check:       {api_url}/health")
    print(f"  Device Status:      {api_url}/devices/Device-01/status")
    print("=" * 60)

    # Save backend endpoint to a local file for frontend deployment
    with open("backend_endpoint.json", "w") as f:
        json.dump(
            {
                "api_url": api_url,
                "public_ip": public_ip,
                "public_dns": public_dns,
                "instance_id": instance_id,
            },
            f,
            indent=2,
        )
else:
    print("\n[WARN] Instance is running, but /health has not yet responded. Check cloud-init logs.")
    print(f"Instance ID: {instance_id}, IP: {public_ip}")
