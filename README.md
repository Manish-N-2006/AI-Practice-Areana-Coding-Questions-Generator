# 🚀 AI Practice Arena

**AI Practice Arena** is an AI-powered coding practice platform that generates programming problems dynamically and evaluates user code in real time, offering a LeetCode-style practice experience enhanced with AI.

> 🚧 **Status:** This project is actively under development and is being evolved toward real-world, production-ready usage.

---

## 🎯 One-Line Goal

**An AI-generated coding practice platform where users can practice, run, and submit coding problems with real-time evaluation.**

---

## ✨ Features

- 🧠 **AI-Generated Coding Problems**  
  Problems are generated dynamically based on topic, difficulty, and programming language.

- 💻 **Interactive Code Editor**  
  Integrated Monaco Editor (VS Code engine) for a smooth coding experience.

- ▶️ **Run & Submit Workflow**  
  Users can run code against sample test cases and submit for full evaluation.

- ⚡ **Real-Time Code Execution**  
  Secure execution of user code using Judge0 execution service.

- 🔐 **User Authentication**  
  Firebase Authentication for secure login and session management.

- 🧪 **Sample & Hidden Test Cases**  
  Accurate judging using multiple test cases.

- 🎨 **Modern UI Flow**  
  Chat-style problem generation followed by a LeetCode-style coding arena.

---

## 🛠️ Tech Stack

### Backend:
- **Flask** – Web framework
- **SQLAlchemy** – ORM for database handling
- **Gemini API** – AI-based coding question generation
- **Gemini Model** - gemini-flash-lite-latest
- **Judge0** – Code execution using Judge0 service endpoint  
  

### Frontend:
- **HTML, CSS, JavaScript**
- **Monaco Editor** – Code editor used in VS Code

### Authentication:
- **Firebase Authentication**

---

## 🧩 How It Works (High-Level Flow)

1. User selects topic, difficulty, and language
2. AI generates a coding problem and test cases
3. Problem is displayed in the practice arena
4. User writes code in Monaco Editor
5. Code is executed via Judge0 service URL
6. Output is compared with expected results
7. Verdict is displayed to the user

---

### Gemini API Setup

This project uses the Gemini API for AI-powered problem generation.

1. Create a `.env` file
2. Add your API key:

```env
GEMINI_API_KEY=your_api_key_here
```

## 📁 Project Structure

```text
AI-Practice-Arena/
├── app.py                  # Main Flask application
├── generate.py             # AI question generation logic
├── models.py               # Database models (SQLAlchemy)
├── templates/              # HTML templates
├── static/                 # CSS, JavaScript, assets
├── firebase-key.json       # Firebase credentials
├── requirements.txt        # Python dependencies
└── README.md
``` 
---


---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Manish-N-2006/AI-Practice-Arena-Coding-Questions-Generator.git
cd AI-Practice-Arena
```

### 2️⃣ Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 5️⃣ Run the Application
```bash
python app.py
```

---

## 🚧 Development Status

- ✅ Core backend implemented
- ✅ AI question generation working
- ✅ Code execution via Judge0 URL
- ✅ Firebase authentication integrated
- 🔄 UI/UX improvements in progress
- 🔄 Scalability & security enhancements ongoing
> This project is being developed with real-world deployment and scalability in mind.

---

## 🤝 Contributing

- Contributions are welcome.
- Fork the repository and submit a pull request.

---

## 📬 Author

- Manish N
- GitHub: Manish-N-2006
- 💼 LinkedIn: https://www.linkedin.com/in/manish-n-b397a0331/
