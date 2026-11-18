function getBrowserStorage() {
	if (typeof window === 'undefined') return null;
	return window.localStorage;
}

export const storage = {
	getItem(key) {
		try {
			return getBrowserStorage()?.getItem(key) ?? null;
		} catch {
			return null;
		}
	},

	setItem(key, value) {
		try {
		const browserStorage = getBrowserStorage();
			if (!browserStorage) return false;
			browserStorage.setItem(key, String(value));
			return true;
		} catch {
			return false;
		}
	},

	removeItem(key) {
		try {
		const browserStorage = getBrowserStorage();
			if (!browserStorage) return false;
			browserStorage.removeItem(key);
			return true;
		} catch {
			return false;
		}
	},

	getJSON(key, fallback = null) {
		const value = this.getItem(key);
		if (value === null) return fallback;
		try {
			return JSON.parse(value);
		} catch {
			return fallback;
		}
	},

	setJSON(key, value) {
		try {
			return this.setItem(key, JSON.stringify(value));
		} catch {
			return false;
		}
	},
};
