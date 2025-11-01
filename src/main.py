"""
NASA Bioscience Publications - Main Application Entry Point
"""
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

def main():
    """Main application entry point"""
    print(" NASA Bioscience Publications System")
    print("Choose an option:")
    print("1. Start API Server")
    print("2. Run Data Pipeline")
    print("3. Test AI Agents")
    print("4. Exit")
    
    choice = input("Enter your choice (1-4): ")
    
    if choice == "1":
        print("Starting API Server...")
        # Import and start API
        from api.main import start_api_server
        start_api_server()
    elif choice == "2":
        print("Running Data Pipeline...")
        # Import and run data pipeline
        from data_pipeline.main import run_pipeline
        run_pipeline()
    elif choice == "3":
        print("Testing AI Agents...")
        # Import and test AI agents
        from ai.main import test_agents
        test_agents()
    elif choice == "4":
        print("Goodbye! ")
        sys.exit(0)
    else:
        print("Invalid choice. Please try again.")
        main()

if __name__ == "__main__":
    main()