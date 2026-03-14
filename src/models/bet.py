from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Bet:
    match_id: str
    bet_type: str
    home_team: str
    away_team: str
    prediction: str
    odds: float
    confidence: float
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return asdict(self)
