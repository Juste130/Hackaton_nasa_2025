#!/usr/bin/env python3
"""
Utilitaire de gestion du cache Redis
Permet de contrôler et monitorer le cache facilement
"""
import argparse
import sys
from redis_cache import get_cache


def show_stats(cache):
    """Afficher les statistiques du cache"""
    print("\n Statistiques du cache Redis")
    print("=" * 60)
    
    stats = cache.get_stats()
    
    if not stats.get('connected'):
        print(" Redis n'est pas connecté")
        if 'error' in stats:
            print(f"   Erreur : {stats['error']}")
        return
    
    print(f" Statut        : Connecté")
    print(f" Commandes     : {stats.get('total_commands', 0):,}")
    print(f"  Cache hits    : {stats.get('keyspace_hits', 0):,}")
    print(f"  Cache misses  : {stats.get('keyspace_misses', 0):,}")
    print(f" Taux de hits  : {stats.get('hit_rate', 0):.2f}%")
    print("=" * 60)


def list_keys(cache, pattern='*'):
    """Lister les clés du cache"""
    print(f"\n Clés correspondant à '{pattern}'")
    print("=" * 60)
    
    if not cache.enabled or not cache.client:
        print(" Redis n'est pas disponible")
        return
    
    try:
        keys = list(cache.client.scan_iter(match=pattern))
        if not keys:
            print("   Aucune clé trouvée")
            return
        
        print(f"   Total : {len(keys)} clés\n")
        
        # Grouper par préfixe
        prefixes = {}
        for key in keys:
            prefix = key.split(':')[0] if ':' in key else 'other'
            if prefix not in prefixes:
                prefixes[prefix] = []
            prefixes[prefix].append(key)
        
        for prefix, prefix_keys in sorted(prefixes.items()):
            print(f"\n   {prefix}:* ({len(prefix_keys)} clés)")
            for key in sorted(prefix_keys)[:10]:
                print(f"      - {key}")
            if len(prefix_keys) > 10:
                print(f"      ... et {len(prefix_keys) - 10} autres")
    
    except Exception as e:
        print(f" Erreur : {e}")
    
    print("=" * 60)


def clear_cache(cache, pattern='*', force=False):
    """Vider le cache"""
    print(f"\n  Nettoyage du cache : {pattern}")
    print("=" * 60)
    
    if not cache.enabled or not cache.client:
        print(" Redis n'est pas disponible")
        return
    
    # Compter les clés d'abord
    try:
        keys = list(cache.client.scan_iter(match=pattern))
        count = len(keys)
        
        if count == 0:
            print("   Aucune clé à supprimer")
            return
        
        print(f"   {count} clé(s) trouvée(s)")
        
        if not force:
            response = input(f"\n  Confirmer la suppression de {count} clé(s) ? (oui/non): ")
            if response.lower() not in ['oui', 'yes', 'y', 'o']:
                print("    Annulé")
                return
        
        deleted = cache.clear_pattern(pattern)
        print(f"    {deleted} clé(s) supprimée(s)")
    
    except Exception as e:
        print(f" Erreur : {e}")
    
    print("=" * 60)


def get_value(cache, key):
    """Récupérer une valeur du cache"""
    print(f"\n Valeur de la clé : {key}")
    print("=" * 60)
    
    if not cache.enabled or not cache.client:
        print(" Redis n'est pas disponible")
        return
    
    try:
        value = cache.get(key)
        if value is None:
            print("    Clé non trouvée ou expirée")
        else:
            print(f"   Type : {type(value).__name__}")
            
            # Afficher la valeur de manière appropriée
            if isinstance(value, (dict, list)):
                import json
                print(f"\n{json.dumps(value, indent=2, ensure_ascii=False)[:500]}")
                if len(str(value)) > 500:
                    print("   ... (tronqué)")
            else:
                print(f"\n   {value}")
    
    except Exception as e:
        print(f" Erreur : {e}")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Utilitaire de gestion du cache Redis pour NASA Knowledge Graph',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
%(prog)s stats                        # Afficher les statistiques
%(prog)s list                         # Lister toutes les clés
%(prog)s list neo4j:*                 # Lister les clés Neo4j
%(prog)s clear neo4j:*                # Vider le cache Neo4j
%(prog)s clear api:* --force          # Vider le cache API sans confirmation
%(prog)s get neo4j:stats              # Voir une valeur spécifique
%(prog)s flush                        # Vider tout le cache
        """
    )
    
    parser.add_argument(
        'command',
        choices=['stats', 'list', 'clear', 'get', 'flush'],
        help='Commande à exécuter'
    )
    
    parser.add_argument(
        'pattern',
        nargs='?',
        default='*',
        help='Pattern de clé (ex: neo4j:*, api:graph:*)'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Forcer l\'action sans confirmation'
    )
    
    args = parser.parse_args()
    
    # Initialiser le cache
    cache = get_cache()
    
    # Vérifier la connexion
    if not cache.enabled:
        print("  Redis est désactivé (REDIS_ENABLED=false)")
        print("   Pour activer : définir REDIS_ENABLED=true dans .env")
        sys.exit(1)
    
    if not cache.client:
        print(" Impossible de se connecter à Redis")
        print("   Vérifiez que Redis est démarré : redis-cli ping")
        sys.exit(1)
    
    # Exécuter la commande
    try:
        if args.command == 'stats':
            show_stats(cache)
        
        elif args.command == 'list':
            list_keys(cache, args.pattern)
        
        elif args.command == 'clear':
            clear_cache(cache, args.pattern, args.force)
        
        elif args.command == 'get':
            if args.pattern == '*':
                print(" Spécifiez une clé exacte avec la commande 'get'")
                sys.exit(1)
            get_value(cache, args.pattern)
        
        elif args.command == 'flush':
            clear_cache(cache, '*', args.force)
    
    except KeyboardInterrupt:
        print("\n\n  Interruption par l'utilisateur")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
