import logging

logger = logging.getLogger(__name__)

class OddsAnalyzer:
    """Analyze odds and identify value bets"""
    
    @staticmethod
    def calculate_implied_probability(odds):
        """Calculate implied probability from decimal odds"""
        if odds <= 0:
            return 0
        return 1 / odds

    @staticmethod
    def find_best_bookmaker(bets_info, bet_type):
        """Find bookmaker with best odds for a bet type"""
        best_odds = None
        best_bookmaker = None
        
        for bet in bets_info:
            if bet['bet_type'] == bet_type:
                if best_odds is None or bet['best_odds'] > best_odds:
                    best_odds = bet['best_odds']
                    best_bookmaker = bet['bookmaker']
        
        return best_bookmaker, best_odds

    @staticmethod
    def calculate_kelly_criterion(odds, win_probability):
        """Calculate Kelly Criterion for optimal bet sizing"""
        if odds <= 0 or win_probability <= 0:
            return 0
        
        b = odds - 1
        p = win_probability
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Conservative approach: use half Kelly
        return max(0, kelly * 0.5)

    @staticmethod
    def compare_odds_across_bookmakers(match_id, bet_type, bookmakers_data):
        """Compare odds across different bookmakers"""
        odds_comparison = {}
        
        for bookmaker, data in bookmakers_data.items():
            if 'markets' in data and bet_type in data['markets']:
                odds_comparison[bookmaker] = data['markets'][bet_type]
        
        if not odds_comparison:
            return None
        
        # Find best odds
        best_odds = None
        best_bookmaker = None
        
        for bookmaker, odds in odds_comparison.items():
            for outcome, price in odds.items():
                if price and (best_odds is None or price > best_odds):
                    best_odds = price
                    best_bookmaker = bookmaker
        
        return {
            'best_odds': best_odds,
            'best_bookmaker': best_bookmaker,
            'all_odds': odds_comparison
        }