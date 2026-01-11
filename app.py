from flask import Flask, request, jsonify, render_template, session, redirect
import requests
import firebase_admin
from firebase_admin import auth, credentials
from time import time
from extensions import db
from models.user import User
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///arena.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
app.secret_key = "secret"
firebase_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
cred_dict = json.loads(firebase_json)
cred = credentials.Certificate(cred_dict)
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

from generate import generate_coding_question

@app.route("/generate", methods=["POST"])
def genreate():
    if "regen_count" not in session:
        session["regen_count"] = 0

    if session["regen_count"] >= 3:
        return jsonify({
            "error": "Regeneration limit reached (3/3)"
        }), 429

    session["regen_count"] += 1
    try:
        if question_cache:
            return jsonify(question_cache[-1])
        data = request.json
        topic = data.get("topic")
        difficulty = data.get("difficulty")
        language = data.get("language")

        question = generate_coding_question(topic, difficulty, language)
        if not question:
            return jsonify({
        "error": "AI failed to generate question"}), 500
        remaining = 3 - session["regen_count"]
        return jsonify({
        **question,
        "remaining": remaining
    })

    except Exception as e:
        import traceback
        print("GENERATE FAILED ")
        traceback.print_exc() 
        return jsonify({"error": "server error"}), 500

@app.route("/practice")
def practice():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    language = data["language"]
    code = data["code"]
    testcases = data["testcases"]

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
            "stdin": normalize_input(tc["input"]) or " "

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

    if not language or not code:
        return jsonify({
            "status": "error",
            "message": "language and code are required"
        }), 400

    
    user_input = data.get("input", "")
    user_input = normalize_input(user_input)

    
    if not user_input:
        user_input = " "   

    output = run_code(language, code, user_input)

    return jsonify({
        "status": "ok",
        "mode": "single",
        "input_used": user_input,
        "output": output
    })


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

@app.route("/arena")
def arena():
    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    return render_template(
        "main.html",
        name=user.name,
        email=user.email,
        xp=user.xp,
        solved=user.questions_solved
    )


if __name__ == "__main__":
    app.run(debug=True)


