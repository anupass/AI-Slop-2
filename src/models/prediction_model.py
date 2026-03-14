from dataclasses import dataclass

@dataclass
class PredictionResult:
    match_id: str
    home_team: str
    away_team: str
    prediction: str
    confidence: float
    best_odds: float
    bookmaker: str
    bet_type: str
