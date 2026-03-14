from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from .bet import Bet

@dataclass
class Parley:
    parley_id: int
    bets: List[Bet]
    bet_amount: float
    created_at: str = None
    status: str = 'pending'
    actual_return: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    @property
    def total_odds(self):
        """Calculate combined odds"""
        total = 1.0
        for bet in self.bets:
            total *= bet.odds
        return total
    
    @property
    def potential_return(self):
        """Calculate potential return"""
        return self.bet_amount * self.total_odds
    
    @property
    def profit(self):
        """Calculate profit"""
        if self.actual_return:
            return self.actual_return - self.bet_amount
        return None
    
    def to_dict(self):
        return {
            'parley_id': self.parley_id,
            'bets': [bet.to_dict() for bet in self.bets],
            'bet_amount': self.bet_amount,
            'total_odds': self.total_odds,
            'potential_return': self.potential_return,
            'created_at': self.created_at,
            'status': self.status,
            'actual_return': self.actual_return,
            'profit': self.profit
        }
