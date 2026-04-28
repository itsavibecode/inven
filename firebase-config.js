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
import {
  getStorage,
  ref as storageRef,
  uploadString,
  getDownloadURL,
  deleteObject,
  listAll
} from "https://www.gstatic.com/firebasejs/12.12.1/firebase-storage.js";

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
const storage = getStorage(app);
const googleProvider = new GoogleAuthProvider();

window.firebaseAuth = auth;
window.firebaseDb = db;
window.firebaseStorage = storage;

// Photos in items are either base64 data URLs (newly added, awaiting
// upload) or https download URLs (already uploaded to Cloud Storage).
// Base64 strings can blow past Firestore's 1 MiB document cap, so we drop
// them before any Firestore write. URLs are tiny and pass through.
function stripForCloud(item) {
  const photos = Array.isArray(item.photos)
    ? item.photos.filter(p => typeof p === 'string' && !p.startsWith('data:'))
    : [];
  return { ...item, photos };
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

// ============================================================
// Storage bridge — photos
// ============================================================

window.firebaseStorageApi = {
  // Upload a single base64 data URL, return the public download URL.
  uploadPhoto: async (uid, itemId, dataUrl) => {
    const photoId = Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
    const path = `users/${uid}/items/${itemId}/${photoId}`;
    const ref = storageRef(storage, path);
    const snapshot = await uploadString(ref, dataUrl, 'data_url');
    const url = await getDownloadURL(snapshot.ref);
    return url;
  },

  // Delete every photo under an item's folder. Best-effort: errors are
  // logged, not thrown, so a partial cleanup still removes most of them.
  deleteItemPhotos: async (uid, itemId) => {
    const folderRef = storageRef(storage, `users/${uid}/items/${itemId}`);
    try {
      const list = await listAll(folderRef);
      await Promise.all(list.items.map(item =>
        deleteObject(item).catch(err => console.warn('delete photo failed:', err))
      ));
    } catch (err) {
      console.warn('listAll for item photos failed:', err);
    }
  },

  // Delete a single photo by its full https download URL.
  deletePhotoByUrl: async (url) => {
    try {
      // Storage download URLs encode the path between /o/ and ?
      const m = url.match(/\/o\/([^?]+)/);
      if (!m) return;
      const path = decodeURIComponent(m[1]);
      const ref = storageRef(storage, path);
      await deleteObject(ref);
    } catch (err) {
      console.warn('deletePhotoByUrl failed:', err);
    }
  }
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
