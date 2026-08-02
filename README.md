# Orchid Meadows — AI Real Estate Calling Agent

Conversation engine for a bilingual (Hindi/Hinglish/English) real estate
sales agent, built to be voice-platform-agnostic: the LLM logic, persona,
project knowledge, and lead-capture live here; a voice platform (Vapi,
Bland.ai, or Twilio + STT/TTS) sits on top to handle the actual phone call.

## What's here

- `data/system_prompt.md` — persona and conversation flow instructions
- `data/project.json` — dummy project knowledge (Orchid Meadows, Gurugram)
- `agent.py` — conversation engine with tool-based lead capture, runnable
  as a text chat right now
- `dashboard.py` — Streamlit dashboard showing captured leads live
- `lead_store_sheets.py` — optional Google Sheets sync (template, needs
  your own service account credentials)
- `data/leads.json` — local lead store, created automatically on first run

## 1. Test the conversation logic today (no voice platform needed)

Get a free API key at https://aistudio.google.com/apikey (Google account,
no card required — Gemini's free tier is generous enough for this whole
testing phase).

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=AIza...
python3 agent.py
```

This runs the full persona, project Q&A, and lead-capture logic as a text
chat. Test it in English, Hindi, and Hinglish, throw objections at it,
change your mind mid-conversation — this is where you'll actually shape
conversation quality before it ever touches audio.

Then view captured leads:

```bash
streamlit run dashboard.py
```

## 2. Wire into a voice platform (Vapi.ai recommended)

1. Sign up at vapi.ai, create an assistant.
2. Set the assistant's system prompt to the contents of
   `data/system_prompt.md` + `data/project.json` (Vapi lets you paste this
   directly, or point it at a webhook that returns it — see
   `load_system_prompt()` in `agent.py`).
3. Choose an STT provider with Hindi support (Deepgram nova-2 or Whisper)
   and a TTS voice with Hindi/Hinglish support (ElevenLabs multilingual
   voices work well).
4. In Vapi's "Functions" / tools config, register `capture_lead` and
   `end_call_summary` with the same JSON schemas defined in
   `TOOL_DECLARATIONS` in `agent.py`, pointed at a webhook endpoint.
5. Stand up a tiny webhook (FastAPI/Flask) that receives Vapi's function-call
   payload and calls `_handle_tool()` — this reuses all the logic already
   built and tested in step 1.
6. Vapi gives you both a phone number and an embeddable web call widget —
   covers the "phone call demo" and "browser-based voice demo" deliverables
   in one setup.

## 3. Move lead storage to Google Sheets (optional, for the "show where
   leads are stored" demo ask)

Follow the setup comment at the top of `lead_store_sheets.py`, then swap
the `append_lead_record` call in `agent.py` for `append_lead_row`.

## Known limitations to disclose in your submission doc

- Project data is fictional — created for this assignment.
- STT/TTS Hindi-English code-switch quality depends entirely on the chosen
  provider and isn't perfect out of the box; expect to tune prompts/voice
  settings.
- Interruption handling quality is bounded by the voice platform's barge-in
  support, not by this conversation engine.
- Gemini's free tier is rate-limited (requests per minute/day) — fine for
  iterative text-chat testing, but if you hit 429 errors during heavy
  testing, slow down or add basic retry/backoff.
