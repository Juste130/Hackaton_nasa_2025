import { cacheService } from './services/cache';

async function manageCacheScript() {
  const command = process.argv[2];
  const parameter = process.argv[3];

  try {
    await cacheService.connect();
    console.log('✅ Connexion à Redis établie');

    switch (command) {
      case 'flush':
        await cacheService.flush();
        console.log('🗑️  Cache vidé complètement');
        break;

      case 'delete':
        if (!parameter) {
          console.error('❌ Veuillez spécifier une clé ou un pattern à supprimer');
          process.exit(1);
        }
        if (parameter.includes('*')) {
          const count = await cacheService.delPattern(parameter);
          console.log(`🗑️  ${count} clés supprimées avec le pattern: ${parameter}`);
        } else {
          const deleted = await cacheService.del(parameter);
          console.log(deleted ? `✅ Clé supprimée: ${parameter}` : `❌ Clé non trouvée: ${parameter}`);
        }
        break;

      case 'get':
        if (!parameter) {
          console.error('❌ Veuillez spécifier une clé à récupérer');
          process.exit(1);
        }
        const value = await cacheService.get(parameter);
        if (value) {
          console.log(`📄 Valeur pour ${parameter}:`);
          console.log(JSON.stringify(value, null, 2));
        } else {
          console.log(`❌ Clé non trouvée: ${parameter}`);
        }
        break;

      case 'keys':
        const pattern = parameter || '*';
        // Note: keys() n'est pas implémenté dans notre CacheService, mais on peut l'ajouter
        console.log(`🔍 Recherche des clés avec le pattern: ${pattern}`);
        // TODO: Implémenter la méthode keys dans CacheService si nécessaire
        break;

      case 'stats':
        console.log('📊 Statistiques du cache:');
        console.log(`- Connecté: ${cacheService.isConnected()}`);
        console.log('- URL Redis:', process.env.REDIS_URL || 'redis://localhost:6379');
        console.log('- TTL par défaut: 10 heures (36000 secondes)');
        break;

      case 'test':
        console.log('🧪 Test du cache...');
        const testKey = 'test:' + Date.now();
        const testData = { message: 'Test cache', timestamp: new Date().toISOString() };
        
        await cacheService.set(testKey, testData, 60); // TTL de 60 secondes pour le test
        console.log(`✅ Données sauvegardées avec la clé: ${testKey}`);
        
        const retrieved = await cacheService.get(testKey);
        if (retrieved && JSON.stringify(retrieved) === JSON.stringify(testData)) {
          console.log('✅ Test de lecture réussi');
          
          await cacheService.del(testKey);
          console.log('✅ Test de suppression réussi');
          console.log('🎉 Cache fonctionne correctement !');
        } else {
          console.log('❌ Erreur lors du test de lecture');
        }
        break;

      default:
        console.log('🔧 Gestionnaire de cache NASA Hackathon 2025');
        console.log('');
        console.log('Usage: npx ts-node src/cache-manager.ts <command> [parameter]');
        console.log('');
        console.log('Commandes disponibles:');
        console.log('  flush                 - Vide complètement le cache');
        console.log('  delete <key>          - Supprime une clé spécifique');
        console.log('  delete <pattern>      - Supprime toutes les clés correspondant au pattern (avec *)');
        console.log('  get <key>             - Affiche la valeur d\'une clé');
        console.log('  stats                 - Affiche les statistiques du cache');
        console.log('  test                  - Test la fonctionnalité du cache');
        console.log('');
        console.log('Exemples:');
        console.log('  npx ts-node src/cache-manager.ts flush');
        console.log('  npx ts-node src/cache-manager.ts delete "api:*"');
        console.log('  npx ts-node src/cache-manager.ts get "api:publications:title:microgravity"');
        console.log('  npx ts-node src/cache-manager.ts test');
        break;
    }

  } catch (error) {
    console.error('❌ Erreur:', error);
  } finally {
    await cacheService.disconnect();
    process.exit(0);
  }
}

// Gestion graceful du shutdown
process.on('SIGINT', async () => {
  await cacheService.disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await cacheService.disconnect();
  process.exit(0);
});

manageCacheScript();