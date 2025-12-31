import json
import re
import uuid
import time
from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))



def clean_text(s):
    if not s:
        return ""
    s = s.replace("`", "")
    s = s.replace("\n", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def normalize_ai_output(raw):
    try:
        data = json.loads(raw)
    except:
        return None

    raw_samples = data.get("sample_test_cases") or data.get("samples") or []
    raw_tests = data.get("hidden_test_cases") or data.get("testcases") or []

    samples = [{"input": s.get("input", ""), "output": s.get("output", "")}
               for s in raw_samples]

    testcases = [{"input": t.get("input", ""), "output": t.get("output", "")}
                 for t in raw_tests]

    title = data.get("title")
    if not title:
        stmt = data.get("problem_statement", "")
        title = stmt.split(".")[0][:60] or "Coding Problem"

    return {
        "title": title,
        "problem_statement": clean_text(data.get("problem_statement", "")),
        "input_format": clean_text(data.get("input_format", "")),
        "output_format": clean_text(data.get("output_format", "")),
        "samples": samples[:3],
        "testcases": testcases[:6]
    }


def generate_coding_question(topic, difficulty, language):
    request_id = str(uuid.uuid4())
    timestamp = int(time.time())

    prompt = f"""
SYSTEM NOTE:
Request ID: {request_id}
Timestamp: {timestamp}

Create ONE VERY SIMPLE coding problem.

Topic: {topic}
Difficulty: {difficulty}
Language: {language}

Difficulty Rules:
EASY:
- One loop only
- No tricky logic
- Beginner friendly

MEDIUM:
- Two loops allowed
- Simple conditions

HARD:
- Advanced logic allowed

Formatting Rules:
- No LaTeX
- No explanations
- Short problem statement
- Return JSON ONLY

JSON FORMAT:
{{
  "problem_statement": "",
  "input_format": "",
  "output_format": "",
  "sample_test_cases": [
    {{ "input": "", "output": "" }}
  ],
  "hidden_test_cases": [
    {{ "input": "", "output": "" }}
  ]
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=prompt
        )

        normalized = normalize_ai_output(response.text)

        if not normalized:
            return {
                "title": "AI Error",
                "problem_statement": "AI returned invalid format. Please click Regenerate.",
                "input_format": "",
                "output_format": "",
                "samples": [],
                "testcases": []
            }

        return normalized

    except Exception as e:
        print("🔥 GENERATE FAILED 🔥", e)
        return {
            "title": "AI Error",
            "problem_statement": "AI generation failed. Please click Regenerate.",
            "input_format": "",
            "output_format": "",
            "samples": [],
            "testcases": []
        }
