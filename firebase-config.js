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
import {
  getFirestore,
  collection,
  doc,
  setDoc,
  deleteDoc,
  onSnapshot,
  query,
  orderBy,
  getDocs
} from "https://www.gstatic.com/firebasejs/12.12.1/firebase-firestore.js";

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
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

window.firebaseAuth = auth;
window.firebaseDb = db;

// Strip the photos array from items before writing to Firestore — photos
// can blow past Firestore's 1 MiB document cap. They are handled separately
// by Firebase Storage in a later commit. Until then photos remain device-
// local in localStorage even when signed in.
function stripForCloud(item) {
  const { photos, ...rest } = item;
  return rest;
}

window.firestoreApi = {
  saveItem: (uid, item) => setDoc(
    doc(db, 'users', uid, 'items', item.id),
    stripForCloud(item)
  ),
  deleteItem: (uid, itemId) => deleteDoc(doc(db, 'users', uid, 'items', itemId)),
  saveBeanie: (uid, key, entry) => setDoc(doc(db, 'users', uid, 'beanieDb', key), entry),
  deleteBeanie: (uid, key) => deleteDoc(doc(db, 'users', uid, 'beanieDb', key)),
  fetchAllItems: async (uid) => {
    const snap = await getDocs(collection(db, 'users', uid, 'items'));
    return snap.docs.map(d => d.data());
  },
  subscribeItems: (uid, cb, errCb) => onSnapshot(
    query(collection(db, 'users', uid, 'items'), orderBy('created_at', 'desc')),
    (snap) => cb(snap.docs.map(d => d.data())),
    (err) => { if (errCb) errCb(err); else console.error('items snapshot error:', err); }
  ),
  subscribeBeanies: (uid, cb, errCb) => onSnapshot(
    collection(db, 'users', uid, 'beanieDb'),
    (snap) => cb(snap.docs.map(d => d.data())),
    (err) => { if (errCb) errCb(err); else console.error('beanies snapshot error:', err); }
  )
};

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
