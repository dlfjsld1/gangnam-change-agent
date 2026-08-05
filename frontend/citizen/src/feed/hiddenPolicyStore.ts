const DATABASE_NAME = "gangnam-change-agent";
const HIDDEN_POLICY_STORE = "hidden-policies";
const FAVORITE_POLICY_STORE = "favorite-policies";
const PROFILE_STORE = "local-profile";
const DATABASE_VERSION = 3;


export async function loadHiddenPolicyIds(): Promise<string[]> {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const request = database.transaction(HIDDEN_POLICY_STORE).objectStore(HIDDEN_POLICY_STORE).getAll();
    request.onsuccess = () => resolve(request.result as string[]);
    request.onerror = () => reject(request.error);
  });
}


export async function hidePolicy(policyId: string): Promise<void> {
  const database = await openDatabase();
  await new Promise<void>((resolve, reject) => {
    const request = database
      .transaction(HIDDEN_POLICY_STORE, "readwrite")
      .objectStore(HIDDEN_POLICY_STORE)
      .put(policyId, policyId);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}


export async function restoreHiddenPolicies(): Promise<void> {
  const database = await openDatabase();
  await new Promise<void>((resolve, reject) => {
    const request = database
      .transaction(HIDDEN_POLICY_STORE, "readwrite")
      .objectStore(HIDDEN_POLICY_STORE)
      .clear();
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}


function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(PROFILE_STORE)) {
        request.result.createObjectStore(PROFILE_STORE);
      }
      if (!request.result.objectStoreNames.contains(HIDDEN_POLICY_STORE)) {
        request.result.createObjectStore(HIDDEN_POLICY_STORE);
      }
      if (!request.result.objectStoreNames.contains(FAVORITE_POLICY_STORE)) {
        request.result.createObjectStore(FAVORITE_POLICY_STORE);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
