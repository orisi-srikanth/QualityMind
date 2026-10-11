"""
Compatibility shim forwarding to backend.app.database.seed.
"""
from backend.app.database.seed import seed_database

if __name__ == "__main__":
    seed_database()
