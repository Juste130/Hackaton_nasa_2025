#!/usr/bin/env python3
"""
Redis cache management utility
Allows easy cache control and monitoring
"""
import argparse
import sys
from src.utils.redis_cache import get_cache


def show_stats(cache):
    """Display cache statistics"""
    print("\n Redis Cache Statistics")
    print("=" * 40)
    
    stats = cache.get_stats()
    
    if not stats.get('connected'):
        print(" Redis is not connected")
        if 'error' in stats:
            print(f"   Error: {stats['error']}")
        return
    
    print(f" Status        : Connected")
    print(f" Commands      : {stats.get('total_commands', 0):,}")
    print(f"  Cache hits    : {stats.get('keyspace_hits', 0):,}")
    print(f"  Cache misses  : {stats.get('keyspace_misses', 0):,}")
    print(f" Hit rate: {stats.get('hit_rate', 0):.2f}%")
    print("=" * 60)


def list_keys(cache, pattern='*'):
    """List cache keys"""
    print(f"\n Keys matching '{pattern}'")
    print("=" * 60)
    
    if not cache.enabled or not cache.client:
        print(" Redis is not available")
        return
    
    try:
        keys = list(cache.client.scan_iter(match=pattern))
        if not keys:
            print("   No keys found")
            return
        
        print(f"   Total: {len(keys)} keys\n")
        
        # Group by prefix
        prefixes = {}
        for key in keys:
            prefix = key.split(':')[0] if ':' in key else 'other'
            if prefix not in prefixes:
                prefixes[prefix] = []
            prefixes[prefix].append(key)
        
        for prefix, prefix_keys in sorted(prefixes.items()):
            print(f"\n   {prefix}:* ({len(prefix_keys)} keys)")
            for key in sorted(prefix_keys)[:10]:
                print(f"      - {key}")
            if len(prefix_keys) > 10:
                print(f"      ... and {len(prefix_keys) - 10} others")
    
    except Exception as e:
        print(f" Error: {e}")
    
    print("=" * 60)


def clear_cache(cache, pattern='*', force=False):
    """Clear cache"""
    print(f"\n  Cache cleanup: {pattern}")
    print("=" * 60)
    
    if not cache.enabled or not cache.client:
        print(" Redis is not available")
        return
    
    # Count keys first
    try:
        keys = list(cache.client.scan_iter(match=pattern))
        count = len(keys)
        
        if count == 0:
            print("   No keys to delete")
            return
        
        print(f"   {count} key(s) found")
        
        if not force:
            response = input(f"\n  Confirm deletion of {count} key(s)? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("    Cancelled")
                return
        
        deleted = cache.clear_pattern(pattern)
        print(f"    {deleted} key(s) deleted")
    
    except Exception as e:
        print(f" Error: {e}")
    
    print("=" * 60)


def get_value(cache, key):
    """Get a value from cache"""
    print(f"\n Cache key value: {key}")
    print("=" * 60)
    
    if not cache.enabled or not cache.client:
        print(" Redis is not available")
        return
    
    try:
        value = cache.get(key)
        if value is None:
            print("    Key not found or expired")
        else:
            print(f"   Type: {type(value).__name__}")
            
            # Display value appropriately
            if isinstance(value, (dict, list)):
                import json
                print(f"\n{json.dumps(value, indent=2, ensure_ascii=False)[:500]}")
                if len(str(value)) > 500:
                    print("   ... (truncated)")
            else:
                print(f"\n   {value}")
    
    except Exception as e:
        print(f" Error: {e}")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Redis cache management utility for NASA Knowledge Graph',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
%(prog)s stats                        # Display statistics
%(prog)s list                         # List all keys  
%(prog)s list neo4j:*                 # List Neo4j keys
%(prog)s clear neo4j:*                # Clear Neo4j cache
%(prog)s clear api:* --force          # Clear API cache without confirmation
%(prog)s get cache_key                # Get specific value
%(prog)s flush                        # Clear entire cache
        """
    )
    
    parser.add_argument(
        'command',
        choices=['stats', 'list', 'clear', 'get', 'flush'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'pattern',
        nargs='?',
        default='*',
        help='Key pattern (ex: neo4j:*, api:graph:*)'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force action without confirmation'
    )
    
    args = parser.parse_args()
    
    # Initialize cache
    cache = get_cache()
    
    # Check connection
    if not cache.enabled:
        print("  Redis is disabled (REDIS_ENABLED=false)")
        print("   To enable: set REDIS_ENABLED=true in .env")
        sys.exit(1)
    
    if not cache.client:
        print(" Unable to connect to Redis")
        print("   Check that Redis is running: redis-cli ping")
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == 'stats':
            show_stats(cache)
        
        elif args.command == 'list':
            list_keys(cache, args.pattern)
        
        elif args.command == 'clear':
            clear_cache(cache, args.pattern, args.force)
        
        elif args.command == 'get':
            if args.pattern == '*':
                print(" Specify an exact key with the 'get' command")
                sys.exit(1)
            get_value(cache, args.pattern)
        
        elif args.command == 'flush':
            clear_cache(cache, '*', args.force)
    
    except KeyboardInterrupt:
        print("\n\n  User interruption")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
