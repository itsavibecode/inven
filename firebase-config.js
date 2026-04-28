// ============================================================
// Firebase configuration + auth bridge
// Modular SDK (v12). Loaded as <script type="module">.
// Exposes a small surface on window for the non-module app.js
// to call into without needing the whole codebase to become
// modules.
// ============================================================

import { initializeApp } from "https://www.gstatic.com/firebasejs/12.12.1/firebase-app.js";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/12.12.1/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyAzKrob4KDq_BNe-cz7-9pI2Zib7yvTvKs",
  authDomain: "inventorysys-f80aa.firebaseapp.com",
  projectId: "inventorysys-f80aa",
  storageBucket: "inventorysys-f80aa.firebasestorage.app",
  messagingSenderId: "592655196273",
  appId: "1:592655196273:web:8042049aab5917b7f9fbd0"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

window.firebaseAuth = auth;

window.firebaseSignIn = async function() {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    return result.user;
  } catch (err) {
    console.error('Sign-in failed:', err);
    window.dispatchEvent(new CustomEvent('firebaseAuthError', {
      detail: { code: err.code, message: err.message }
    }));
    throw err;
  }
};

window.firebaseSignOut = async function() {
  try {
    await signOut(auth);
  } catch (err) {
    console.error('Sign-out failed:', err);
    throw err;
  }
};

onAuthStateChanged(auth, (user) => {
  window.dispatchEvent(new CustomEvent('firebaseAuthChanged', { detail: user }));
});

window.dispatchEvent(new CustomEvent('firebaseReady'));
