import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.ml import BettingPredictor

predictor = BettingPredictor()

test_match = {
    'id': 'match_1',
    'home_team': 'Arsenal',
    'away_team': 'Everton',
    'sport_key': 'soccer_epl',
    'commence_time': '2026-03-15T15:00:00Z'
}

print("Testing predictor...")
predictions = predictor.predict_match(test_match)

print("\nPredictions:")
import json
print(json.dumps(predictions, indent=2, default=str))