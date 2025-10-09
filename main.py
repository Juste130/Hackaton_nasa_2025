"""Run the FastAPI app defined in `api_ai.py`.

This `main.py` provides a simple entrypoint so you can start the API with:

    python3 main.py

Environment variables (optional):
- HOST (default: 0.0.0.0)
- PORT (default: 8000)
"""
import os
import uvicorn

try:
    # Import the FastAPI app from the api_ai module
    from api_ai import app  # type: ignore
except Exception as e:
    # If import fails, show a helpful message and re-raise
    print(f"Failed to import FastAPI app from api_ai.py: {e}")
    raise


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    print(f"Starting FastAPI app from api_ai.py on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
