#!/usr/bin/env python3
"""
Test Redis Cache Performance for Neo4j Queries
Measures performance improvements with Redis cache
"""
import time
import sys
from typing import Dict, List
from src.utils.redis_cache import get_cache
from src.database.neo4j_client import Neo4jClient
from src.database.neo4j_queries import KnowledgeGraphAnalytics


def measure_time(func, *args, **kwargs):
    """Measure execution time of a function"""
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    return result, (end - start) * 1000  # in milliseconds


def test_cache_performance():
    """Test Redis cache performance"""
    
    print("=" * 80)
    print(" REDIS CACHE PERFORMANCE TEST")
    print("=" * 80)
    
    # Initialize clients
    cache = get_cache()
    client = Neo4jClient()
    analytics = KnowledgeGraphAnalytics(client)
    
    # Check Redis connectivity
    print("\n1. Checking Redis connectivity...")
    if cache.enabled and cache.client:
        try:
            cache.client.ping()
            print("    Redis connected and functional")
        except Exception as e:
            print(f"    Redis error: {e}")
            sys.exit(1)
    else:
        print("     Redis disabled - Cache will not be used")
        print("   To enable Redis, set REDIS_ENABLED=true in .env")
        return
    
    # Performance tests
    tests: List[Dict] = []
    
    print("\n2. Testing Neo4j statistics...")
    print("-" * 80)
    
    # Clear cache before test
    cache.clear_pattern('neo4j:*')
    
    # First call (without cache)
    _, time1 = measure_time(client.get_stats)
    print(f"   First call (MISS) : {time1:.2f} ms")
    
    # Second call (with cache)
    _, time2 = measure_time(client.get_stats)
    print(f"   Second call (HIT)  : {time2:.2f} ms")
    
    improvement = ((time1 - time2) / time1) * 100
    print(f"    Improvement : {improvement:.1f}% faster")
    tests.append({
        'test': 'get_stats',
        'miss': time1,
        'hit': time2,
        'improvement': improvement
    })
    
    print("\n3. Test of top studied organisms...")
    print("-" * 80)
    
    cache.clear_pattern('neo4j:top_organisms*')
    
    _, time1 = measure_time(analytics.top_studied_organisms, limit=10)
    print(f"   First call (MISS) : {time1:.2f} ms")
    
    _, time2 = measure_time(analytics.top_studied_organisms, limit=10)
    print(f"   Second call (HIT)  : {time2:.2f} ms")
    
    improvement = ((time1 - time2) / time1) * 100
    print(f"    Improvement : {improvement:.1f}% faster")
    tests.append({
        'test': 'top_studied_organisms',
        'miss': time1,
        'hit': time2,
        'improvement': improvement
    })
    
    print("\n4. Test of most investigated phenomena...")
    print("-" * 80)
    
    cache.clear_pattern('neo4j:top_phenomena*')
    
    _, time1 = measure_time(analytics.top_investigated_phenomena, limit=10)
    print(f"   First call (MISS) : {time1:.2f} ms")
    
    _, time2 = measure_time(analytics.top_investigated_phenomena, limit=10)
    print(f"   Second call (HIT)  : {time2:.2f} ms")
    
    improvement = ((time1 - time2) / time1) * 100
    print(f"    Improvement : {improvement:.1f}% faster")
    tests.append({
        'test': 'top_investigated_phenomena',
        'miss': time1,
        'hit': time2,
        'improvement': improvement
    })
    
    print("\n5. Test of research gaps...")
    print("-" * 80)
    
    cache.clear_pattern('neo4j:research_gaps*')
    
    _, time1 = measure_time(analytics.research_gaps_by_system)
    print(f"   First call (MISS) : {time1:.2f} ms")
    
    _, time2 = measure_time(analytics.research_gaps_by_system)
    print(f"   Second call (HIT)  : {time2:.2f} ms")
    
    improvement = ((time1 - time2) / time1) * 100
    print(f"    Improvement : {improvement:.1f}% faster")
    tests.append({
        'test': 'research_gaps_by_system',
        'miss': time1,
        'hit': time2,
        'improvement': improvement
    })
    
    # Redis cache statistics
    print("\n6. Redis cache statistics...")
    print("-" * 80)
    
    stats = cache.get_stats()
    if stats.get('connected'):
        print(f"   Total commands : {stats.get('total_commands', 0)}")
        print(f"   Cache hits         : {stats.get('keyspace_hits', 0)}")
        print(f"   Cache misses       : {stats.get('keyspace_misses', 0)}")
        print(f"   Hit rate       : {stats.get('hit_rate', 0):.2f}%")
    
    # Global summary
    print("\n" + "=" * 80)
    print(" PERFORMANCE SUMMARY")
    print("=" * 80)
    
    total_miss_time = sum(t['miss'] for t in tests)
    total_hit_time = sum(t['hit'] for t in tests)
    avg_improvement = sum(t['improvement'] for t in tests) / len(tests)
    
    print(f"\n   Total time without cache : {total_miss_time:.2f} ms")
    print(f"   Total time with cache: {total_hit_time:.2f} ms")
    print(f"   Average improvement   : {avg_improvement:.1f}%")
    print(f"   Time saved          : {total_miss_time - total_hit_time:.2f} ms")
    
    print("\n   Details by test :")
    print("   " + "-" * 76)
    for test in tests:
        print(f"   {test['test']:<30} | Gain: {test['improvement']:>6.1f}%")
    
    print("\n" + "=" * 80)
    print("  Test completed successfully!")
    print("=" * 80)
    
    # Cleanup
    client.close()


def test_cache_invalidation():
    """Test cache invalidation"""
    
    print("\n\n" + "=" * 80)
    print(" CACHE INVALIDATION TEST")
    print("=" * 80)
    
    cache = get_cache()
    
    if not cache.enabled:
        print("     Redis disabled - Test skipped")
        return
    
    print("\n1. Cleaning Neo4j keys...")
    deleted = cache.clear_pattern('neo4j:*')
    print(f"     {deleted} keys deleted")
    
    print("\n2. Cleaning API keys...")
    deleted = cache.clear_pattern('api:graph:*')
    print(f"     {deleted} keys deleted")
    
    print("\n3. Cleaning RAG keys...")
    deleted = cache.clear_pattern('rag:*')
    print(f"     {deleted} keys deleted")
    
    print("\n Cache cleared successfully!")


def main():
    """Main function"""
    print("\n")
    print("" + "=" * 78 + "")
    print("" + " " * 20 + "REDIS CACHE TEST - NASA KNOWLEDGE GRAPH" + " " * 19 + "")
    print("" + "=" * 78 + "")
    
    try:
        # Performance test
        test_cache_performance()
        
        # Invalidation test
        test_cache_invalidation()
        
    except KeyboardInterrupt:
        print("\n\n  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n Error during test : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
