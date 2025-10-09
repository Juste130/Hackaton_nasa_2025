import { Request, Response, NextFunction } from 'express';
import { cacheService } from '../services/cache';

export interface CacheOptions {
  ttl?: number; // TTL en secondes
  keyPrefix?: string; // Préfixe pour la clé de cache
  skipCache?: boolean; // Option pour désactiver le cache
  includeHeaders?: string[]; // Headers à inclure dans la clé de cache
}

/**
 * Middleware de cache Redis pour Express
 */
export function cacheMiddleware(options: CacheOptions = {}) {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Skip cache pour les méthodes autres que GET
    if (req.method !== 'GET') {
      return next();
    }

    // Skip cache si explicitement demandé
    if (options.skipCache) {
      return next();
    }

    // Skip cache si paramètre nocache=true
    if (req.query.nocache === 'true') {
      return next();
    }

    try {
      // Générer la clé de cache
      const route = req.path;
      const queryParams = { ...req.query };
      
      // Supprimer les paramètres de cache de la clé
      delete queryParams.nocache;
      delete queryParams._t; // timestamp pour forcer refresh
      
      // Inclure certains headers si spécifié
      const headerParams: Record<string, string> = {};
      if (options.includeHeaders) {
        options.includeHeaders.forEach(header => {
          const value = req.get(header);
          if (value) {
            headerParams[`header_${header}`] = value;
          }
        });
      }

      const allParams = { ...queryParams, ...headerParams };
      const keyPrefix = options.keyPrefix || 'cache';
      const cacheKey = `${keyPrefix}:${cacheService.generateKey(route, allParams)}`;

      // Tenter de récupérer depuis le cache
      const cachedData = await cacheService.get(cacheKey);
      
      if (cachedData) {
        console.log(`Cache HIT: ${cacheKey}`);
        
        // Ajouter des headers pour indiquer que la réponse vient du cache
        res.set({
          'X-Cache': 'HIT',
          'X-Cache-Key': cacheKey,
          'Cache-Control': 'public, max-age=3600'
        });
        
        return res.json(cachedData);
      }

      console.log(`Cache MISS: ${cacheKey}`);

      // Intercepter la réponse pour la mettre en cache
      const originalSend = res.json;
      
      res.json = function(data: any) {
        // Sauvegarder dans le cache seulement si la requête est réussie
        if (res.statusCode >= 200 && res.statusCode < 300) {
          cacheService.set(cacheKey, data, options.ttl).catch(err => {
            console.error('Failed to cache response:', err);
          });
        }

        // Ajouter des headers pour indiquer que la réponse n'est pas du cache
        res.set({
          'X-Cache': 'MISS',
          'X-Cache-Key': cacheKey,
          'Cache-Control': 'public, max-age=3600'
        });

        // Appeler la méthode originale
        return originalSend.call(this, data);
      };

      next();

    } catch (error) {
      console.error('Cache middleware error:', error);
      // En cas d'erreur de cache, continuer sans cache
      next();
    }
  };
}

/**
 * Middleware pour invalider le cache sur certaines routes
 */
export function invalidateCacheMiddleware(patterns: string[] = ['api:*']) {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Intercepter la réponse pour invalider le cache après une opération réussie
    const originalSend = res.json;
    
    res.json = function(data: any) {
      // Invalider le cache seulement si l'opération est réussie
      if (res.statusCode >= 200 && res.statusCode < 300) {
        patterns.forEach(pattern => {
          cacheService.delPattern(pattern).catch(err => {
            console.error('Failed to invalidate cache pattern:', pattern, err);
          });
        });
      }

      return originalSend.call(this, data);
    };

    next();
  };
}

/**
 * Raccourci pour le cache par défaut (10h TTL)
 */
export const defaultCache = cacheMiddleware({
  ttl: 36000, // 10 heures
  keyPrefix: 'api'
});

/**
 * Cache court terme (1h TTL)
 */
export const shortCache = cacheMiddleware({
  ttl: 3600, // 1 heure
  keyPrefix: 'api-short'
});

/**
 * Cache long terme (24h TTL)
 */
export const longCache = cacheMiddleware({
  ttl: 86400, // 24 heures
  keyPrefix: 'api-long'
});