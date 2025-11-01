"""
Data Pipeline Main Module
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_pipeline():
    """Run the data extraction and enrichment pipeline"""
    print(" Starting Data Pipeline...")
    
    choice = input("""
Choose pipeline operation:
1. Extract publications from NCBI
2. Enrich with entity extraction
3. Create annotation dataset
4. Run full pipeline
Enter choice (1-4): """)
    
    if choice == "1":
        run_extraction()
    elif choice == "2":
        run_enrichment()
    elif choice == "3":
        run_annotation_creation()
    elif choice == "4":
        run_full_pipeline()
    else:
        print("Invalid choice")

def run_extraction():
    """Run publication extraction"""
    try:
        from .extractors.ncbi_extractor import main as extract_main
        asyncio.run(extract_main())
    except ImportError as e:
        print(f" Could not import extraction module: {e}")

def run_enrichment():
    """Run entity enrichment"""
    try:
        from .enrichment.batch_extract_optimized import main as enrich_main
        asyncio.run(enrich_main())
    except ImportError as e:
        print(f" Could not import enrichment module: {e}")

def run_annotation_creation():
    """Run annotation dataset creation"""
    try:
        from .enrichment.create_annotation_dataset import main as annotation_main
        asyncio.run(annotation_main())
    except ImportError as e:
        print(f" Could not import annotation module: {e}")

def run_full_pipeline():
    """Run complete pipeline"""
    print(" Running full pipeline...")
    run_extraction()
    run_enrichment()
    run_annotation_creation()
    print(" Pipeline complete!")

if __name__ == "__main__":
    run_pipeline()