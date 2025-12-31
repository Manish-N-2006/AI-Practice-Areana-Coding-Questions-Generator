import { initializeApp } from "https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup } from
"https://www.gstatic.com/firebasejs/9.23.0/firebase-auth.js";

// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDZN2RjYcgtCVET0Nu-l0n5aJd2z_JiVfY",
  authDomain: "ai-coding---practice-arena.firebaseapp.com",
  projectId: "ai-coding---practice-arena",
  storageBucket: "ai-coding---practice-arena.firebasestorage.app",
  messagingSenderId: "822882822502",
  appId: "1:822882822502:web:0ab13e43ca584ce9c900a7",
  measurementId: "G-WJNL1SSM5G"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

async function loginWithGoogle() {
  const result = await signInWithPopup(auth, provider);
  const user = result.user;

  const name = user.displayName;
  const email = user.email;

  const res = await fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: email,
      name: name,
      provider: "firebase"
    })
  });

  const data = await res.json();

  if (data.success) {
    window.location.href = "/arena";
  } else {
    alert("Google login failed");
  }
}

window.loginWithGoogle = loginWithGoogle;

