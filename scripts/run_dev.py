import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uvicorn
from backend.scripts.seed_data import seed_data

def main():
    print("=" * 60)
    print("Starting Vera Multi-Merchant WhatsApp AI Assistant")
    print("=" * 60)
    
    # 1. Initialize and seed database if not already seeded
    print("Verifying database records...")
    asyncio.run(seed_data())

    # 2. Launch FastAPI with auto-reload
    print("\nLaunching Backend server at http://localhost:8000 ...")
    print("API Documentation available at: http://localhost:8000/docs")
    print("Merchant Dashboard accessible at: http://localhost:8000")
    print("Interactive WhatsApp Simulator: http://localhost:8000/#/simulator\n")

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
