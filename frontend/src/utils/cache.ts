interface CacheItem<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

export class Cache {
  private static instance: Cache;
  private storage: Map<string, CacheItem<any>> = new Map();
  private readonly DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes

  static getInstance(): Cache {
    if (!Cache.instance) {
      Cache.instance = new Cache();
    }
    return Cache.instance;
  }

  /**
   * Set cache item with TTL
   */
  set<T>(key: string, data: T, ttl: number = this.DEFAULT_TTL): void {
    const now = Date.now();
    this.storage.set(key, {
      data,
      timestamp: now,
      expiresAt: now + ttl,
    });

    // Clean up expired items periodically
    this.cleanup();
  }

  /**
   * Get cache item if not expired
   */
  get<T>(key: string): T | null {
    const item = this.storage.get(key);
    
    if (!item) {
      return null;
    }

    if (Date.now() > item.expiresAt) {
      this.storage.delete(key);
      return null;
    }

    return item.data as T;
  }

  /**
   * Check if key exists and is not expired
   */
  has(key: string): boolean {
    return this.get(key) !== null;
  }

  /**
   * Delete cache item
   */
  delete(key: string): boolean {
    return this.storage.delete(key);
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.storage.clear();
  }

  /**
   * Get cache statistics
   */
  getStats(): { size: number; keys: string[] } {
    return {
      size: this.storage.size,
      keys: Array.from(this.storage.keys()),
    };
  }

  /**
   * Clean up expired items
   */
  private cleanup(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, item] of this.storage.entries()) {
      if (now > item.expiresAt) {
        expiredKeys.push(key);
      }
    }

    expiredKeys.forEach(key => this.storage.delete(key));
  }

  /**
   * Create cache key from parameters
   */
  static createKey(prefix: string, ...params: (string | number)[]): string {
    return `${prefix}:${params.join(':')}`;
  }
}

// Response cache specifically for API responses
export class ResponseCache {
  private cache = Cache.getInstance();
  private readonly TRANSCRIPTION_TTL = 10 * 60 * 1000; // 10 minutes
  private readonly CHAT_TTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Cache transcription result
   */
  cacheTranscription(audioHash: string, transcript: string): void {
    const key = Cache.createKey('transcription', audioHash);
    this.cache.set(key, transcript, this.TRANSCRIPTION_TTL);
  }

  /**
   * Get cached transcription
   */
  getCachedTranscription(audioHash: string): string | null {
    const key = Cache.createKey('transcription', audioHash);
    return this.cache.get<string>(key);
  }

  /**
   * Cache chat response
   */
  cacheChatResponse(messageHash: string, response: string): void {
    const key = Cache.createKey('chat', messageHash);
    this.cache.set(key, response, this.CHAT_TTL);
  }

  /**
   * Get cached chat response
   */
  getCachedChatResponse(messageHash: string): string | null {
    const key = Cache.createKey('chat', messageHash);
    return this.cache.get<string>(key);
  }

  /**
   * Create hash from content for caching
   */
  async createHash(content: string | Blob): Promise<string> {
    let data: string;
    
    if (content instanceof Blob) {
      data = await content.text();
    } else {
      data = content;
    }

    // Simple hash function (for production, consider using crypto.subtle.digest)
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      const char = data.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(36);
  }

  /**
   * Clear all response cache
   */
  clearAll(): void {
    this.cache.clear();
  }
}

export const responseCache = new ResponseCache();
