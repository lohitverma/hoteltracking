const CACHE_PREFIX = 'hotel_tracker_';
const DEFAULT_EXPIRY = 30 * 60 * 1000; // 30 minutes

class Cache {
  static set(key, value, expiryMs = DEFAULT_EXPIRY) {
    const item = {
      value,
      timestamp: Date.now(),
      expiry: expiryMs,
    };
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(item));
  }

  static get(key) {
    const item = localStorage.getItem(CACHE_PREFIX + key);
    if (!item) return null;

    const { value, timestamp, expiry } = JSON.parse(item);
    if (Date.now() - timestamp > expiry) {
      this.remove(key);
      return null;
    }

    return value;
  }

  static remove(key) {
    localStorage.removeItem(CACHE_PREFIX + key);
  }

  static clear() {
    Object.keys(localStorage)
      .filter(key => key.startsWith(CACHE_PREFIX))
      .forEach(key => localStorage.removeItem(key));
  }
}

export default Cache;
