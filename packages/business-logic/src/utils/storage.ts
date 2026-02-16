export interface AuthTokens {
  accessToken?: string | null;
  refreshToken?: string | null;
  sessionToken?: string | null;
}

export interface TokenStorage {
  getTokens(): Promise<AuthTokens>;
  setTokens(tokens: AuthTokens): Promise<void>;
  clearTokens(): Promise<void>;
}

export interface WebTokenStorageOptions {
  readonly storage?: Storage;
  readonly accessTokenKey?: string;
  readonly refreshTokenKey?: string;
  readonly sessionTokenKey?: string;
}

export interface SecureStoreAdapter {
  getItemAsync(key: string): Promise<string | null>;
  setItemAsync(key: string, value: string): Promise<void>;
  deleteItemAsync(key: string): Promise<void>;
}

const ACCESS_TOKEN_KEY = "foundation.auth.access";
const REFRESH_TOKEN_KEY = "foundation.auth.refresh";
const SESSION_TOKEN_KEY = "foundation.auth.session";

export function createMemoryTokenStorage(initialTokens?: AuthTokens): TokenStorage {
  let tokens: AuthTokens = { ...initialTokens };

  return {
    async getTokens() {
      return { ...tokens };
    },
    async setTokens(update) {
      tokens = mergeTokens(tokens, update);
    },
    async clearTokens() {
      tokens = {};
    },
  } satisfies TokenStorage;
}

export function createWebTokenStorage(options: WebTokenStorageOptions = {}): TokenStorage {
  const storage = options.storage ?? resolveBrowserStorage();
  if (!storage) {
    return createMemoryTokenStorage();
  }

  const accessKey = options.accessTokenKey ?? ACCESS_TOKEN_KEY;
  const refreshKey = options.refreshTokenKey ?? REFRESH_TOKEN_KEY;
  const sessionKey = options.sessionTokenKey ?? SESSION_TOKEN_KEY;

  return {
    async getTokens() {
      return {
        accessToken: storage.getItem(accessKey) ?? undefined,
        refreshToken: storage.getItem(refreshKey) ?? undefined,
        sessionToken: storage.getItem(sessionKey) ?? undefined,
      } satisfies AuthTokens;
    },
    async setTokens(update) {
      updateValue(storage, accessKey, update.accessToken);
      updateValue(storage, refreshKey, update.refreshToken);
      updateValue(storage, sessionKey, update.sessionToken);
    },
    async clearTokens() {
      storage.removeItem(accessKey);
      storage.removeItem(refreshKey);
      storage.removeItem(sessionKey);
    },
  } satisfies TokenStorage;
}

export function createSecureStoreTokenStorage(
  adapter: SecureStoreAdapter,
  options: Omit<WebTokenStorageOptions, "storage"> = {},
): TokenStorage {
  const accessKey = options.accessTokenKey ?? ACCESS_TOKEN_KEY;
  const refreshKey = options.refreshTokenKey ?? REFRESH_TOKEN_KEY;
  const sessionKey = options.sessionTokenKey ?? SESSION_TOKEN_KEY;

  return {
    async getTokens() {
      const [accessToken, refreshToken, sessionToken] = await Promise.all([
        adapter.getItemAsync(accessKey),
        adapter.getItemAsync(refreshKey),
        adapter.getItemAsync(sessionKey),
      ]);
      return {
        accessToken: accessToken ?? undefined,
        refreshToken: refreshToken ?? undefined,
        sessionToken: sessionToken ?? undefined,
      } satisfies AuthTokens;
    },
    async setTokens(update) {
      await Promise.all([
        syncSecureStoreValue(adapter, accessKey, update.accessToken),
        syncSecureStoreValue(adapter, refreshKey, update.refreshToken),
        syncSecureStoreValue(adapter, sessionKey, update.sessionToken),
      ]);
    },
    async clearTokens() {
      await Promise.all([
        adapter.deleteItemAsync(accessKey),
        adapter.deleteItemAsync(refreshKey),
        adapter.deleteItemAsync(sessionKey),
      ]);
    },
  } satisfies TokenStorage;
}

export const noopTokenStorage: TokenStorage = {
  async getTokens() {
    return {};
  },
  async setTokens() {
    return undefined;
  },
  async clearTokens() {
    return undefined;
  },
};

function resolveBrowserStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function updateValue(storage: Storage, key: string, value: string | null | undefined) {
  if (value === undefined) {
    return;
  }
  if (value === null) {
    storage.removeItem(key);
    return;
  }
  storage.setItem(key, value);
}

async function syncSecureStoreValue(
  adapter: SecureStoreAdapter,
  key: string,
  value: string | null | undefined,
) {
  if (value === undefined) {
    return;
  }
  if (value === null) {
    await adapter.deleteItemAsync(key);
    return;
  }
  await adapter.setItemAsync(key, value);
}

function mergeTokens(current: AuthTokens, update: AuthTokens): AuthTokens {
  const next: AuthTokens = { ...current };
  if (update.accessToken !== undefined) {
    next.accessToken = update.accessToken ?? undefined;
  }
  if (update.refreshToken !== undefined) {
    next.refreshToken = update.refreshToken ?? undefined;
  }
  if (update.sessionToken !== undefined) {
    next.sessionToken = update.sessionToken ?? undefined;
  }
  return next;
}
