"""
Real estate AI calling agent — conversation engine (Gemini version).

This is the "brain" of the calling agent: persona, project knowledge,
lead-capture via tool calls, and call-summary generation. It runs here
as a text chat so you can test and refine the conversation logic before
wiring it into a voice platform (Vapi / Bland.ai / Twilio).

Get a free API key at https://aistudio.google.com/apikey (no card needed).

Usage:
    export GEMINI_API_KEY=AIza...
    python3 agent.py

Wiring into a voice platform later just means: the platform's STT feeds
the customer's spoken text into `Agent.turn()`, and the returned text is
sent to TTS. The tool-calling logic (capture_lead / end_call_summary)
stays identical — most voice platforms let you register these as
"function tools" that call a webhook, which can just import this module.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
LEADS_FILE = DATA_DIR / "leads.json"
MODEL = "gemini-flash-lite-latest"

TOOL_DECLARATIONS = [
    {
        "name": "capture_lead",
        "description": (
            "Save or update the customer's requirements and contact details as they "
            "emerge in conversation. Call this multiple times as you learn more — "
            "only include fields you actually know, omit the rest."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string"},
                "phone_number": {"type": "string"},
                "intent": {"type": "string", "enum": ["self-use", "investment", "undecided"]},
                "preferred_location": {"type": "string"},
                "property_type": {"type": "string"},
                "configuration": {
                    "type": "string",
                    "description": "e.g. 2 BHK, 3 BHK, 4 BHK, plot, commercial",
                },
                "budget_range_inr_lakh": {"type": "string"},
                "purchase_timeline": {"type": "string"},
                "notes": {"type": "string"},
            },
        },
    },
    {
        "name": "end_call_summary",
        "description": "Call once, at the natural end of the conversation, to record a structured call summary.",
        "parameters": {
            "type": "object",
            "properties": {
                "outcome": {
                    "type": "string",
                    "enum": ["qualified_lead", "not_interested", "callback_requested", "incomplete"],
                },
                "summary": {"type": "string", "description": "3-5 sentence summary of the call"},
                "next_step": {"type": "string"},
            },
            "required": ["outcome", "summary"],
        },
    },
]


def load_system_prompt() -> str:
    persona = (DATA_DIR / "system_prompt.md").read_text()
    project = json.loads((DATA_DIR / "project.json").read_text())
    return (
        persona
        + "\n\n## Project data (only source of truth for project facts)\n```json\n"
        + json.dumps(project, indent=2, ensure_ascii=False)
        + "\n```"
    )


def append_lead_record(record: dict, call_id: str):
    LEADS_FILE.parent.mkdir(exist_ok=True)
    leads = json.loads(LEADS_FILE.read_text()) if LEADS_FILE.exists() else []
    existing = next((l for l in leads if l.get("call_id") == call_id), {})
    merged = {**existing, **record, "call_id": call_id, "updated_at": datetime.utcnow().isoformat()}
    leads = [l for l in leads if l.get("call_id") != call_id] + [merged]
    LEADS_FILE.write_text(json.dumps(leads, indent=2, ensure_ascii=False))


class Agent:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.system_prompt = load_system_prompt()
        tool = types.Tool(function_declarations=TOOL_DECLARATIONS)
        self.chat = self.client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                tools=[tool],
                # Manual function calling: we want to run our own side effects
                # (writing lead records) rather than the SDK auto-executing.
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        self.call_id = datetime.utcnow().strftime("call_%Y%m%d_%H%M%S")

    def turn(self, user_text: str) -> str:
        response = self.chat.send_message(user_text)
        return self._process_response(response)

    def _process_response(self, response) -> str:
        text_parts = []
        parts = response.candidates[0].content.parts or []
        for part in parts:
            if getattr(part, "text", None):
                text_parts.append(part.text)

        function_calls = response.function_calls or []
        if function_calls:
            response_parts = []
            for fc in function_calls:
                result = self._handle_tool(fc.name, dict(fc.args or {}))
                response_parts.append(
                    types.Part.from_function_response(name=fc.name, response={"result": result})
                )
            follow_up = self.chat.send_message(response_parts)
            more_text = self._process_response(follow_up)
            if more_text:
                text_parts.append(more_text)

        return "\n".join(t for t in text_parts if t).strip()

    def _handle_tool(self, name: str, tool_input: dict) -> str:
        if name == "capture_lead":
            append_lead_record(tool_input, self.call_id)
            return "Lead record saved."
        if name == "end_call_summary":
            LOGS_DIR.mkdir(exist_ok=True)
            log_path = LOGS_DIR / f"{self.call_id}_summary.json"
            log_path.write_text(json.dumps(tool_input, indent=2, ensure_ascii=False))
            append_lead_record({"call_summary": tool_input}, self.call_id)
            return "Call summary recorded."
        return "Unknown tool."


def main():
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        print("Set GEMINI_API_KEY before running (export GEMINI_API_KEY=AIza...)")
        print("Get a free key at https://aistudio.google.com/apikey")
        sys.exit(1)

    agent = Agent()
    print("Meera (Orchid Meadows) — text chat test. Type 'quit' to exit.\n")
    opener = agent.turn("(the call has just connected)")
    print(f"Meera: {opener}\n")

    while True:
        try:
            user_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_text.lower() in {"quit", "exit"}:
            break
        reply = agent.turn(user_text)
        print(f"\nMeera: {reply}\n")


if __name__ == "__main__":
    main()
