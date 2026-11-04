"""Keep offline tests independent of the developer's credentials."""

import pytest


@pytest.fixture(autouse=True)
def isolate_provider_credentials(monkeypatch):
    # Blank values also prevent dotenv from introducing a real key later in a test.
    monkeypatch.setenv("MODEL_API_KEY", "")
    monkeypatch.setenv("AWS_SQS_QUEUE_URL", "")
    monkeypatch.setenv("AWS_SNS_TOPIC_ARN", "")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
