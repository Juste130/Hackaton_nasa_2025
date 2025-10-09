import { createClient, RedisClientType } from 'redis';

export class CacheService {
  private client: RedisClientType;
  private defaultTTL: number = 36000; // 10 heures en secondes
  private connected: boolean = false;

  constructor() {
    const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
    this.client = createClient({
      url: redisUrl
    });

    this.client.on('error', (err) => {
      console.error('Redis Client Error:', err);
      this.connected = false;
    });

    this.client.on('connect', () => {
      console.log('Redis Client Connected');
      this.connected = true;
    });

    this.client.on('disconnect', () => {
      console.log('Redis Client Disconnected');
      this.connected = false;
    });
  }

  async connect(): Promise<void> {
    try {
      if (!this.connected) {
        await this.client.connect();
      }
    } catch (error) {
      console.error('Failed to connect to Redis:', error);
      this.connected = false;
    }
  }

  async disconnect(): Promise<void> {
    try {
      if (this.connected) {
        await this.client.disconnect();
      }
    } catch (error) {
      console.error('Failed to disconnect from Redis:', error);
    }
  }

  /**
   * Récupère une valeur du cache
   */
  async get<T>(key: string): Promise<T | null> {
    if (!this.connected) {
      console.warn('Redis not connected, skipping cache get');
      return null;
    }

    try {
      const value = await this.client.get(key);
      if (value) {
        return JSON.parse(value) as T;
      }
      return null;
    } catch (error) {
      console.error('Cache get error:', error);
      return null;
    }
  }

  /**
   * Stocke une valeur dans le cache avec TTL
   */
  async set(key: string, value: any, ttl?: number): Promise<boolean> {
    if (!this.connected) {
      console.warn('Redis not connected, skipping cache set');
      return false;
    }

    try {
      const serializedValue = JSON.stringify(value);
      const expireTime = ttl || this.defaultTTL;
      
      await this.client.setEx(key, expireTime, serializedValue);
      return true;
    } catch (error) {
      console.error('Cache set error:', error);
      return false;
    }
  }

  /**
   * Supprime une valeur du cache
   */
  async del(key: string): Promise<boolean> {
    if (!this.connected) {
      console.warn('Redis not connected, skipping cache delete');
      return false;
    }

    try {
      const result = await this.client.del(key);
      return result > 0;
    } catch (error) {
      console.error('Cache delete error:', error);
      return false;
    }
  }

  /**
   * Supprime toutes les clés correspondant à un pattern
   */
  async delPattern(pattern: string): Promise<number> {
    if (!this.connected) {
      console.warn('Redis not connected, skipping pattern delete');
      return 0;
    }

    try {
      const keys = await this.client.keys(pattern);
      if (keys.length > 0) {
        return await this.client.del(keys);
      }
      return 0;
    } catch (error) {
      console.error('Cache delete pattern error:', error);
      return 0;
    }
  }

  /**
   * Vérifie si une clé existe
   */
  async exists(key: string): Promise<boolean> {
    if (!this.connected) {
      return false;
    }

    try {
      const result = await this.client.exists(key);
      return result === 1;
    } catch (error) {
      console.error('Cache exists error:', error);
      return false;
    }
  }

  /**
   * Génère une clé de cache basée sur la route et les paramètres
   */
  generateKey(route: string, params?: Record<string, any>): string {
    const baseKey = `api:${route.replace(/\//g, ':')}`;
    
    if (!params || Object.keys(params).length === 0) {
      return baseKey;
    }

    // Trie les paramètres pour avoir une clé consistante
    const sortedParams = Object.keys(params)
      .sort()
      .filter(key => params[key] !== undefined && params[key] !== null)
      .map(key => `${key}:${params[key]}`)
      .join(':');

    return sortedParams ? `${baseKey}:${sortedParams}` : baseKey;
  }

  /**
   * Vide tout le cache
   */
  async flush(): Promise<boolean> {
    if (!this.connected) {
      return false;
    }

    try {
      await this.client.flushAll();
      return true;
    } catch (error) {
      console.error('Cache flush error:', error);
      return false;
    }
  }

  /**
   * Retourne le statut de connexion
   */
  isConnected(): boolean {
    return this.connected;
  }
}

// Instance singleton
export const cacheService = new CacheService();