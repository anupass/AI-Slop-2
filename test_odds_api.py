import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.api_handlers import OddsAPIHandler
from config import SUPPORTED_SPORTS
import json

odds_handler = OddsAPIHandler()

print("Testing Odds API Handler...")
print(f"API Key: {odds_handler.api_key}")
print(f"Base URL: {odds_handler.base_url}")
print(f"Supported Sports: {SUPPORTED_SPORTS}\n")

# Test getting sports
print("=" * 60)
print("GETTING AVAILABLE SPORTS:")
print("=" * 60)
sports = odds_handler.get_sports()
print(json.dumps(sports[:3], indent=2))

# Test getting odds
print("\n" + "=" * 60)
print("GETTING ODDS FOR FIRST SPORT:")
print("=" * 60)
for sport in SUPPORTED_SPORTS[:1]:
    print(f"\nFetching odds for: {sport}")
    odds = odds_handler.get_odds(sport)
    print(f"Number of matches: {len(odds)}")
    if odds:
        print("\nFirst match:")
        print(json.dumps(odds[0], indent=2)[:500])
    else:
        print("No odds returned!")

# Test get all odds
print("\n" + "=" * 60)
print("GETTING ALL ODDS:")
print("=" * 60)
all_odds = odds_handler.get_all_upcoming_odds()
for sport, odds_list in all_odds.items():
    print(f"{sport}: {len(odds_list) if isinstance(odds_list, list) else 0} matches")