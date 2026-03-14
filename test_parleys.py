import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import DatabaseManager

db = DatabaseManager()
parleys = db.get_all_parleys()

print(f"\nTotal parleys in database: {len(parleys)}")
for p in parleys:
    print(f"  Parley #{p[0]}: {p[1]} - Status: {p[3]} - Bet: ${p[5]:.2f}")

print("\n")