import type { LocalProfile } from "./dynamicProfile";


const DATABASE_NAME = "gangnam-change-agent";
const STORE_NAME = "local-profile";
const HIDDEN_POLICY_STORE = "hidden-policies";
const PROFILE_KEY = "current";


export async function loadProfile(): Promise<LocalProfile> {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const request = database.transaction(STORE_NAME).objectStore(STORE_NAME).get(PROFILE_KEY);
    request.onsuccess = () => resolve(request.result ?? {});
    request.onerror = () => reject(request.error);
  });
}


export async function saveProfile(profile: LocalProfile): Promise<void> {
  const database = await openDatabase();
  await new Promise<void>((resolve, reject) => {
    const request = database
      .transaction(STORE_NAME, "readwrite")
      .objectStore(STORE_NAME)
      .put(profile, PROFILE_KEY);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}


function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
  const request = indexedDB.open(DATABASE_NAME, 2);
  request.onupgradeneeded = () => {
    if (!request.result.objectStoreNames.contains(STORE_NAME)) {
      request.result.createObjectStore(STORE_NAME);
    }
    if (!request.result.objectStoreNames.contains(HIDDEN_POLICY_STORE)) {
      request.result.createObjectStore(HIDDEN_POLICY_STORE);
    }
  };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
