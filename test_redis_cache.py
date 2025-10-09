#!/usr/bin/env python3
"""
Test Redis Cache Performance for Neo4j Queries
Mesure l'amélioration des performances avec le cache Redis
"""
import time
import sys
from typing import Dict, List
from redis_cache import get_cache
from neo4j_client import Neo4jClient
from neo4j_queries import KnowledgeGraphAnalytics


def measure_time(func, *args, **kwargs):
    """Mesure le temps d'exécution d'une fonction"""
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    return result, (end - start) * 1000  # en millisecondes


def test_cache_performance():
    """Test des performances du cache Redis"""
    
    print("=" * 80)
    print(" TEST DE PERFORMANCE DU CACHE REDIS")
    print("=" * 80)
    
    # Initialiser les clients
    cache = get_cache()
    client = Neo4jClient()
    analytics = KnowledgeGraphAnalytics(client)
    
    # Vérifier la connectivité Redis
    print("\n1. Vérification de la connectivité Redis...")
    if cache.enabled and cache.client:
        try:
            cache.client.ping()
            print("    Redis connecté et fonctionnel")
        except Exception as e:
            print(f"    Erreur Redis : {e}")
            sys.exit(1)
    else:
        print("     Redis désactivé - Le cache ne sera pas utilisé")
        print("   Pour activer Redis, définissez REDIS_ENABLED=true dans .env")
        return
    
    # Tests de performance
    tests: List[Dict] = []
    
    print("\n2. Test des statistiques Neo4j...")
    print("-" * 80)
    
    # Vider le cache avant le test
    cache.clear_pattern('neo4j:*')
    
    # Premier appel (sans cache)
    _, time1 = measure_time(client.get_stats)
    print(f"   Premier appel (MISS) : {time1:.2f} ms")
    
    # Deuxième appel (avec cache)
    _, time2 = measure_time(client.get_stats)
    print(f"   Deuxième appel (HIT)  : {time2:.2f} ms")
    
    improvement = ((time1 - time2) / time1) * 100
    print(f"    Amélioration : {improvement:.1f}% plus rapide")
    tests.append({
        'test': 'get_stats',
        'miss': time1,
        'hit': time2,
        'improvement': improvement
    })
    
    print("\n3. Test des top organismes étudiés...")
    print("-" * 80)
    
    cache.clear_pattern('neo4j:top_organisms*')
    
    _, time1 = measure_time(analytics.top_studied_organisms, limit=10)
    print(f"   Premier appel (MISS) : {time1:.2f} ms")
    
    _, time2 = measure_time(analytics.top_studied_organisms, limit=10)
    print(f"   Deuxième appel (HIT)  : {time2:.2f} ms")
    
    improvement = ((time1 - time2) / time1) * 100
    print(f"    Amélioration : {improvement:.1f}% plus rapide")
    tests.append({
        'test': 'top_studied_organisms',
        'miss': time1,
        'hit': time2,
        'improvement': improvement
    })
    
    print("\n4. Test des phénomènes les plus investigués...")
    print("-" * 80)
    
    cache.clear_pattern('neo4j:top_phenomena*')
    
    _, time1 = measure_time(analytics.top_investigated_phenomena, limit=10)
    print(f"   Premier appel (MISS) : {time1:.2f} ms")
    
    _, time2 = measure_time(analytics.top_investigated_phenomena, limit=10)
    print(f"   Deuxième appel (HIT)  : {time2:.2f} ms")
    
    improvement = ((time1 - time2) / time1) * 100
    print(f"    Amélioration : {improvement:.1f}% plus rapide")
    tests.append({
        'test': 'top_investigated_phenomena',
        'miss': time1,
        'hit': time2,
        'improvement': improvement
    })
    
    print("\n5. Test des gaps de recherche...")
    print("-" * 80)
    
    cache.clear_pattern('neo4j:research_gaps*')
    
    _, time1 = measure_time(analytics.research_gaps_by_system)
    print(f"   Premier appel (MISS) : {time1:.2f} ms")
    
    _, time2 = measure_time(analytics.research_gaps_by_system)
    print(f"   Deuxième appel (HIT)  : {time2:.2f} ms")
    
    improvement = ((time1 - time2) / time1) * 100
    print(f"    Amélioration : {improvement:.1f}% plus rapide")
    tests.append({
        'test': 'research_gaps_by_system',
        'miss': time1,
        'hit': time2,
        'improvement': improvement
    })
    
    # Statistiques du cache
    print("\n6. Statistiques du cache Redis...")
    print("-" * 80)
    
    stats = cache.get_stats()
    if stats.get('connected'):
        print(f"   Total de commandes : {stats.get('total_commands', 0)}")
        print(f"   Cache hits         : {stats.get('keyspace_hits', 0)}")
        print(f"   Cache misses       : {stats.get('keyspace_misses', 0)}")
        print(f"   Taux de hits       : {stats.get('hit_rate', 0):.2f}%")
    
    # Résumé global
    print("\n" + "=" * 80)
    print(" RÉSUMÉ DES PERFORMANCES")
    print("=" * 80)
    
    total_miss_time = sum(t['miss'] for t in tests)
    total_hit_time = sum(t['hit'] for t in tests)
    avg_improvement = sum(t['improvement'] for t in tests) / len(tests)
    
    print(f"\n   Temps total sans cache : {total_miss_time:.2f} ms")
    print(f"   Temps total avec cache : {total_hit_time:.2f} ms")
    print(f"   Amélioration moyenne   : {avg_improvement:.1f}%")
    print(f"   Gain de temps          : {total_miss_time - total_hit_time:.2f} ms")
    
    print("\n   Détails par test :")
    print("   " + "-" * 76)
    for test in tests:
        print(f"   {test['test']:<30} | Gain: {test['improvement']:>6.1f}%")
    
    print("\n" + "=" * 80)
    print("  Test terminé avec succès!")
    print("=" * 80)
    
    # Cleanup
    client.close()


def test_cache_invalidation():
    """Test de l'invalidation du cache"""
    
    print("\n\n" + "=" * 80)
    print(" TEST D'INVALIDATION DU CACHE")
    print("=" * 80)
    
    cache = get_cache()
    
    if not cache.enabled:
        print("     Redis désactivé - Test ignoré")
        return
    
    print("\n1. Nettoyage des clés Neo4j...")
    deleted = cache.clear_pattern('neo4j:*')
    print(f"     {deleted} clés supprimées")
    
    print("\n2. Nettoyage des clés API...")
    deleted = cache.clear_pattern('api:graph:*')
    print(f"     {deleted} clés supprimées")
    
    print("\n3. Nettoyage des clés RAG...")
    deleted = cache.clear_pattern('rag:*')
    print(f"     {deleted} clés supprimées")
    
    print("\n Cache vidé avec succès!")


def main():
    """Main function"""
    print("\n")
    print("" + "=" * 78 + "")
    print("" + " " * 20 + "TEST CACHE REDIS - NASA KNOWLEDGE GRAPH" + " " * 19 + "")
    print("" + "=" * 78 + "")
    
    try:
        # Test de performance
        test_cache_performance()
        
        # Test d'invalidation
        test_cache_invalidation()
        
    except KeyboardInterrupt:
        print("\n\n  Test interrompu par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
