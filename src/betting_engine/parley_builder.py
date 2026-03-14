import logging
from datetime import datetime
from itertools import combinations
from src.models import Bet, Parley
from src.database import DatabaseManager
from config import DAILY_PARLEYS, PARLEY_SIZE, MAX_BET_AMOUNT

logger = logging.getLogger(__name__)

class ParleyBuilder:
    def __init__(self):
        self.db = DatabaseManager()

    def build_parleys(self, best_bets, num_parleys=DAILY_PARLEYS, parley_size=PARLEY_SIZE):
        """Build optimal parleys from best bets"""
        
        if len(best_bets) < parley_size:
            logger.warning(f"Not enough bets to create parley of size {parley_size}. Have {len(best_bets)}, need {parley_size}")
            return []
        
        # Get top bets
        top_bets = best_bets[:parley_size * num_parleys]
        
        # Generate combinations
        parley_combinations = list(combinations(top_bets, parley_size))
        
        if not parley_combinations:
            logger.warning("Could not generate parley combinations")
            return []
        
        # Select best combinations (maximize confidence)
        best_combinations = sorted(
            parley_combinations,
            key=lambda x: sum(bet['confidence'] for bet in x) / len(x),
            reverse=True
        )[:num_parleys]
        
        parleys = []
        for i, combo in enumerate(best_combinations):
            parley = self._create_parley(combo, i + 1)
            if parley:
                parleys.append(parley)
        
        logger.info(f"Built {len(parleys)} parleys")
        return parleys

    def _create_parley(self, bets_info, parley_number):
        """Create a parley from bet information"""
        
        bets = []
        total_odds = 1.0
        total_confidence = 0
        
        for bet_info in bets_info:
            bet = Bet(
                match_id=bet_info['match_id'],
                bet_type=bet_info['bet_type'],
                home_team=bet_info['home_team'],
                away_team=bet_info['away_team'],
                prediction=bet_info['prediction'],
                odds=bet_info.get('best_odds', 1.5),  # Default to 1.5 if not found
                confidence=bet_info['confidence']
            )
            bets.append(bet)
            total_odds *= bet.odds
            total_confidence += bet.confidence
        
        avg_confidence = total_confidence / len(bets)
        
        # Skip if confidence too low
        if avg_confidence < 0.40:
            return None
        
        parley = Parley(
            parley_id=parley_number,
            bets=bets,
            bet_amount=MAX_BET_AMOUNT / len(bets_info),
            created_at=datetime.now().isoformat()
        )
        
        return parley

    def save_parleys(self, parleys):
        """Save parleys to database"""
        parley_ids = []
        
        for parley in parleys:
            parley_data = {
                'parley_date': datetime.now().strftime('%Y-%m-%d'),
                'created_at': parley.created_at,
                'total_odds': parley.total_odds,
                'bet_amount': parley.bet_amount,
                'potential_return': parley.potential_return
            }
            
            parley_id = self.db.insert_parley(parley_data)
            parley_ids.append(parley_id)
            
            # Save individual bets
            for bet in parley.bets:
                bet_data = {
                    'parley_id': parley_id,
                    'bet_type': bet.bet_type,
                    'match_id': bet.match_id,
                    'home_team': bet.home_team,
                    'away_team': bet.away_team,
                    'prediction': bet.prediction,
                    'odds': bet.odds,
                    'confidence': bet.confidence,
                    'created_at': bet.created_at
                }
                self.db.insert_bet(bet_data)
        
        logger.info(f"Saved {len(parleys)} parleys to database")
        return parley_ids