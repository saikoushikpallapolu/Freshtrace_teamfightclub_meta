"""Read-only planning integration to verify a bounded real model/tool round trip."""

import json

from backend.meta.client import WONDER_MODEL

HISTORY_TOOL = {
    "type": "function",
    "name": "get_batch_history",
    "description": "Read the supplied batch evidence and protocol status. Does not measure hardware.",
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {"batch_id": {"type": "string"}},
        "required": ["batch_id"],
        "additionalProperties": False,
    },
}


def plan_with_history(client, batch_id: str, history: dict, max_rounds: int = 3):
    """Caller supplies real history or an explicitly labeled fixture; no writes allowed."""
    if not 1 <= max_rounds <= 3:
        raise ValueError("Planning requires 1-3 bounded rounds.")
    context = [
        {
            "role": "user",
            "content": (
                f"Read get_batch_history for batch {batch_id} before proposing the next inspection step. "
                "Respect missing evidence and the supplied protocol status. Do not invent measurements, "
                "recovery durations, sensor cleaning procedures or a food-safety decision. "
                "If protocol timing is uncharacterized, request characterization instead of an exact schedule. "
                "This is a read-only plan: do not claim any action was performed."
            ),
        }
    ]
    responses, trace = [], []
    for turn in range(max_rounds):
        response = client.responses.create(
            model=WONDER_MODEL,
            input=context,
            tools=[HISTORY_TOOL],
            # Meta currently accepts only auto; require a completed tool trace in code.
            tool_choice="auto",
            max_output_tokens=4096,
        )
        responses.append(response)
        if response.status != "completed":
            raise ValueError("Planner response did not complete.")
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            if not trace or not response.output_text.strip():
                raise ValueError("Planner did not complete a history-tool round trip.")
            return responses, trace
        # Replay all output items, including reasoning, into the following tool turn.
        context.extend(item.model_dump(mode="json") for item in response.output)
        for call in calls:
            args = json.loads(call.arguments)
            if call.name != "get_batch_history" or args != {"batch_id": batch_id}:
                raise ValueError("Planner attempted an unauthorized tool or batch lookup.")
            trace.append(
                {
                    "name": call.name,
                    "arguments": args,
                    "status": "completed",
                    "data_source": history.get("data_source", "caller_supplied"),
                }
            )
            context.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(history),
                }
            )
    raise ValueError("Planner exhausted its bounded tool-round budget.")
