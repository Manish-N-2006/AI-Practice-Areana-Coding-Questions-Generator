from flask import Flask, request, jsonify, render_template, session, redirect
import requests
import firebase_admin
from firebase_admin import auth, credentials
from time import time
from extensions import db
from models.user import User
from datetime import date
from flask_migrate import Migrate
from dotenv import load_dotenv
load_dotenv()

FREE_DAILY_QUOTA = 4
app = Flask(__name__)

@app.before_request
def init_limits():
    session.setdefault("regen_limit", 3)       
    session.setdefault("solution_limit", 4)    
    session.setdefault("hint_limit", 2)        
    session.setdefault("review_limit", 5)      
  


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///arena.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
migrate = Migrate(app, db)   
app.secret_key = "secret"
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)
question_cache = []

JUDGE0_URL = "https://ce.judge0.com/submissions?base64_encoded=false&wait=true"
LANGUAGE_MAP = {
    "python": 71,
    "cpp": 54,
    "c": 50,
    "java": 62,
    "javascript": 63
}

def check_and_reset_quota(user):
    today = date.today()
    if user.quota_date != today:
        user.quota_date = today
        user.daily_quota_used = 0
        db.session.commit()

from generate import generate_coding_question, generate_ai_code_review


@app.route("/generate", methods=["POST"])
def generate():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = db.session.get(User, session["user_id"])
    check_and_reset_quota(user)

    if user.daily_quota_used >= FREE_DAILY_QUOTA:
        return jsonify({
            "error": "Daily free quota exhausted",
            "remaining": 0
        }), 429

    
    user.daily_quota_used += 1
    db.session.commit()

    data = request.json
    topic = data.get("topic")
    difficulty = data.get("difficulty")
    language = data.get("language")

    question = generate_coding_question(topic, difficulty, language)
    if not question:
        return jsonify({"error": "AI generation failed"}), 500

    remaining = FREE_DAILY_QUOTA - user.daily_quota_used
    session["current_question"] = question
    session.pop("solution_seen", None)
    session.pop("hint_seen", None)
    session["solution_used_for_current"] = False
    session["review_seen"] = False

 

    return jsonify({
        **question,
        "ai_remaining": remaining 
    })

@app.route("/ai/code-review", methods=["POST"])
def ai_code_review():
    data = request.json or {}

    if "current_question" not in session:
        frontend_q = data.get("question")
        if frontend_q:
            session["current_question"] = frontend_q
        else:
            return jsonify({
                "review": "⚠️ No active question. Please regenerate."
            })

    if session.get("review_limit", 0) <= 0:
        return jsonify({
            "review": "❌ AI Code Review limit reached."
        })

    if not session.get("review_seen"):
        session["review_seen"] = True
        return jsonify({
            "review": "👀 Try debugging once. Click again if still stuck."
        })

    session["review_limit"] -= 1   # ✅ FIX

    question = session["current_question"]
    problem = question["problem_statement"]
    code = data.get("code", "")
    language = data.get("language", "python")

    review = generate_ai_code_review(problem, code, language)
    return jsonify({"review": review})



@app.route("/ai/solution", methods=["POST"])
def ai_solution():
    data = request.json or {}

    # ✅ restore from frontend if session lost
    if "current_question" not in session:
        frontend_q = data.get("question")
        if frontend_q:
            session["current_question"] = frontend_q
        else:
            return jsonify({
                "solution": "⚠️ No active question. Please regenerate.",
                "remaining": session.get("solution_limit", 0)
            })

    question = session["current_question"]

    if session["solution_limit"] <= 0:
        return jsonify({
            "solution": "❌ AI Solution limit reached.",
            "remaining": 0
        })

    if not session.get("solution_used_for_current"):
        session["solution_used_for_current"] = True
        return jsonify({
            "solution": "😄 Bro… first try solving it yourself. Click again if needed.",
            "remaining": session["solution_limit"]
        })

    session["solution_limit"] -= 1

    sol = question.get("solution", {})
    content = (
        f"🧠 Explanation:\n{sol.get('explanation','')}\n\n"
        f"💻 Code:\n{sol.get('code','')}"
    )

    return jsonify({
        "solution": content,
        "remaining": session["solution_limit"]
    })




@app.route("/practice")
def practice():
    return render_template("index.html")

@app.route("/api/limits")
def api_limits():
    return jsonify({
        "regen": session.get("regen_limit", 0),
        "solution": session.get("solution_limit", 0),
        "review": session.get("review_limit", 0),
        "hint": session.get("hint_limit", 0),
    })


@app.route("/submit", methods=["POST"])
def submit():
    data = request.json or {}

    language = data.get("language")
    code = data.get("code")
    testcases = data.get("testcases")

    if not language or not code:
        return jsonify({
            "status": "error",
            "message": "Language or code missing"
        }), 400

    if not testcases:
        return jsonify({
            "status": "error",
            "message": "No testcases available. Please regenerate the question."
        }), 400

    result = run_multiple_tests(language, code, testcases)

    if result["status"] != "ok":
        return jsonify(result)

    outputs = result["outputs"]
    results = []

    for i, tc in enumerate(testcases):
        got = outputs[i] if i < len(outputs) else ""
        passed = got.strip() == tc["output"].strip()

        results.append({
            "input": tc["input"],
            "expected": tc["output"],
            "got": got,
            "pass": passed
        })

    return jsonify({
        "status": "ok",
        "results": results
    })



def indent_code(code):
    return "\n".join("    " + line for line in code.splitlines())

def run_multiple_tests(language, code, testcases):
    outputs = []

    for tc in testcases:
        payload = {
            "language_id": LANGUAGE_MAP[language],
            "source_code": code,
            "stdin": normalize_input(tc["input"])

        }

        res = requests.post(JUDGE0_URL, json=payload, timeout=20)
        result = res.json()

        if result.get("compile_output"):
            return {"status": "compile_error", "message": result["compile_output"]}

        if result.get("stderr"):
            return {"status": "runtime_error", "message": result["stderr"]}

        outputs.append((result.get("stdout") or "").strip())

    return {
        "status": "ok",
        "outputs": outputs
    }

def run_code(language, code, user_input=""):
    language = language.lower()

    if language not in LANGUAGE_MAP:
        return "Unsupported language"

    payload = {
        "language_id": LANGUAGE_MAP[language],
        "source_code": code,
        "stdin": user_input
    }

    try:
        res = requests.post(JUDGE0_URL, json=payload, timeout=15)
        data = res.json()

        if data.get("stderr"):
            return data["stderr"].strip()

        if data.get("compile_output"):
            return data["compile_output"].strip()

        return data.get("stdout", "").strip()

    except Exception as e:
        return f"Execution Error: {str(e)}"

last_run = {}

def can_run(uid):
    now = time()
    if uid in last_run and now - last_run[uid] < 2:
        return False
    last_run[uid] = now
    return True

def normalize_input(inp: str) -> str:
    
    if not inp:
        return ""
    inp = inp.strip()
    if inp.startswith("[") and inp.endswith("]"):
        inp = inp[1:-1].replace(",", " ")
    return inp


@app.route("/run", methods=["POST"])
def run():
    uid = session.get("uid", "guest")

    if not can_run(uid):
        return jsonify({"status": "rate_limited"}), 429

    data = request.json or {}
    language = data.get("language")
    code = data.get("code")
    testcases = data.get("testcases", [])

    if not language or not code:
        return jsonify({
            "status": "error",
            "message": "language and code are required"
        }), 400

    if not testcases:
        return jsonify({
            "status": "error",
            "message": "No testcases found"
        }), 400

   
    tc = testcases[0]
    user_input = normalize_input(tc.get("input", ""))
    expected = tc.get("output", "").strip()

    output = run_code(language, code, user_input).strip()

    return jsonify({
        "status": "ok",
        "input": user_input,
        "your_output": output,
        "expected_output": expected,
        "pass": output == expected
    })

@app.route("/home")
def home():
    return render_template("main.html")


@app.route("/")
def login_page():
    return render_template("login.html")

from services.user_services import get_or_create_user

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    name = data.get("name")
    provider = data.get("provider")

    if not email:
        return jsonify({"error": "Email required"}), 400

    user = get_or_create_user(email, provider, name)

    session["user_id"] = user.id
    return jsonify({"success": True})


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/mark_solved", methods=["POST"])
def mark_solved():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = db.session.get(User, session["user_id"])

    user.questions_solved += 1
    user.xp += 10 

    db.session.commit()
    return jsonify({"success": True})

@app.route("/plans")
def plans():
    return render_template("plans.html")

@app.route("/arena")
def arena():
    if "user_id" not in session:
        return redirect("/")

    user = db.session.get(User, session["user_id"])

    # Reset daily quota if needed
    check_and_reset_quota(user)

    # Calculate remaining daily quota
    remaining = max(0, FREE_DAILY_QUOTA - user.daily_quota_used)

    # Initialize session limits if not present
    session.setdefault("regen_limit", 3)
    session.setdefault("solution_limit", 3)   # keep consistent
    session.setdefault("hint_limit", 2)
    session.setdefault("review_limit", 5)

    # 🔥 CRITICAL FIX: sync display limits with remaining quota
    if remaining == 0:
        regen_limit = 0
        solution_limit = 0
        hint_limit = 0
        review_limit = 0
    else:
        regen_limit = session["regen_limit"]
        solution_limit = session["solution_limit"]
        hint_limit = session["hint_limit"]
        review_limit = session["review_limit"]

    return render_template(
        "main.html",
        name=user.name,
        email=user.email,
        xp=user.xp,
        solved=user.questions_solved,

        remaining=remaining,
        regen_limit=regen_limit,
        solution_limit=solution_limit,
        hint_limit=hint_limit,
        review_limit=review_limit,
    )



if __name__ == "__main__":
    app.run(debug=True)
