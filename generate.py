import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DOCS = ROOT
PYQS_PATH = ROOT / "pyqs.json"
OUT_PATH = DOCS / "daily.json"
HF_TOKEN = os.getenv("GEMINI_API_KEY", "").strip()
HF_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
HF_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

def load_pyqs():
    if not PYQS_PATH.exists():
        return []
    try:
        items = json.loads(PYQS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Could not parse {PYQS_PATH}: {exc}")
    valid = []
    for q in items:
        url = str(q.get("official_source_url", "")).strip()
        question = str(q.get("question", "")).strip()
        answer = str(q.get("answer", "")).strip()
        if (question and answer and url.startswith("https://")
                and "REPLACE" not in url.upper()
                and "REPLACE" not in question.upper()):
            valid.append(q)
    return valid

def call_model(prompt):
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN secret is missing.")
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": HF_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You create careful educational content. Do not fabricate sources, "
                    "quotes, current news, statistics, or official exam questions. "
                    "If uncertain, state uncertainty. Return only valid JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 1800,
    }
    response = requests.post(HF_URL, headers=headers, json=payload, timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Hugging Face API returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )
    data = response.json()
    return data["choices"][0]["message"]["content"]

def parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise

def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    date_label = now.strftime("%Y-%m-%d")
    weekday = now.strftime("%A")
    pyqs = load_pyqs()

    chosen = None
    if pyqs:
        # Rotate deterministically by date so the same question is not selected every day.
        chosen = pyqs[now.timetuple().tm_yday % len(pyqs)]

    pyq_context = "No verified GATE question is configured. Return a clear placeholder, not an invented PYQ."
    if chosen:
        pyq_context = json.dumps(chosen, ensure_ascii=False)

    weekly = weekday == "Sunday"
    prompt = f"""
Create a concise daily personal-growth digest for {date_label} ({weekday}).
Audience: an Indian ECE engineering student who wants practical psychology, charisma,
better conversations, disciplined learning, and GATE EC preparation.

Return one JSON object with exactly these keys:
date, quote, psychology, charisma_drill, briefing, gate_pyq, weekly_review.

Requirements:
- quote: a short original quote (do not attribute it to a real person).
- psychology: title, explanation (3-5 short paragraphs), real-life example, one exercise.
  Teach evidence-informed psychology. Avoid pop-psych certainty or manipulation tactics.
- charisma_drill: one specific conversation exercise with a sample line and a reflection question.
  Focus on listening, clarity, confidence and respect, not coercion.
- briefing: an evergreen engineering/decision-making insight with a practical takeaway.
  This is NOT live news; do not claim it is current research or include invented citations.
- gate_pyq: use only the verified record supplied below. Explain the supplied answer step by step.
  Preserve year, paper, topic, question, options, answer and official_source_url exactly.
  Do not change the correct answer. If no verified record is supplied, clearly say the user
  must add a question from an official GATE paper and answer key; do not invent a PYQ.
- weekly_review: on Sunday, provide a 5-question reflection/revision review. On other days,
  return an empty string.
- Keep it useful, concise, readable on a phone. Return JSON only.
- Do not include Markdown fences.

Verified GATE record (source of truth):
{pyq_context}

Is Sunday: {weekly}
"""
    try:
        content = call_model(prompt)
        digest = parse_json(content)
        digest["date"] = date_label
        digest["generated_at_utc"] = now.isoformat()
        digest["model"] = HF_MODEL
        digest["weekly_review"] = digest.get("weekly_review", "") if weekly else ""
        if chosen:
            # Enforce source metadata from our local verified bank.
            digest["gate_pyq"]["year"] = chosen.get("year")
            digest["gate_pyq"]["paper"] = chosen.get("paper", "EC")
            digest["gate_pyq"]["topic"] = chosen.get("topic", "")
            digest["gate_pyq"]["question"] = chosen["question"]
            digest["gate_pyq"]["options"] = chosen.get("options", {})
            digest["gate_pyq"]["answer"] = chosen["answer"]
            digest["gate_pyq"]["official_source_url"] = chosen["official_source_url"]
            digest["gate_pyq"]["id"] = chosen.get("id", "")
        else:
            digest["gate_pyq"] = {
                "title": "Verified GATE PYQ not configured",
                "explanation": "Add a real question and official answer-key source to data/pyqs.json. The system deliberately will not fabricate an official PYQ.",
                "official_source_url": "",
            }
        OUT_PATH.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {OUT_PATH} for {date_label}")
    except Exception as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        # Do not overwrite the last good digest on a failure.
        sys.exit(1)

if __name__ == "__main__":
    main()
