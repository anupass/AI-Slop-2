"""Diagnose why predictions have low confidence"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api_handlers import OddsAPIHandler
from src.ml import BettingPredictor
from src.utils import setup_logger

logger = setup_logger(__name__)

def diagnose_predictions():
    """Analyze prediction confidence scores"""
    
    logger.info("=== Prediction Diagnostics ===\n")
    
    try:
        odds_handler = OddsAPIHandler()
        predictor = BettingPredictor()
        
        # Get current odds
        logger.info("Fetching current odds...")
        odds_data = odds_handler.get_all_upcoming_odds()
        
        all_matches = []
        for sport_key, matches in odds_data.items():
            parsed_matches = odds_handler.parse_odds_response(matches)
            all_matches.extend(parsed_matches)
        
        logger.info(f"Found {len(all_matches)} matches\n")
        
        # Analyze first 5 matches
        for i, match in enumerate(all_matches[:5]):
            logger.info(f"Match {i+1}: {match['home_team']} vs {match['away_team']}")
            logger.info(f"  ID: {match['match_id']}")
            logger.info(f"  Time: {match['commence_time']}")
            
            # Get predictions
            predictions = predictor.predict_match(match)
            
            if predictions:
                logger.info(f"  Predictions:")
                for bet_type, pred in predictions.items():
                    conf_0 = pred['confidence_class_0']
                    conf_1 = pred['confidence_class_1']
                    max_conf = max(conf_0, conf_1)
                    prediction = 'Class 1' if conf_1 > conf_0 else 'Class 0'
                    logger.info(f"    {bet_type}: {prediction} (confidence: {max_conf:.4f})")
            else:
                logger.warning(f"  No predictions generated")
            
            logger.info("")
        
        # Get best bets with lowered threshold
        logger.info("\n=== Best Bets Analysis ===\n")
        
        for threshold in [0.40, 0.45, 0.50, 0.55]:
            best_bets = predictor.get_best_bets(all_matches, odds_data, threshold)
            logger.info(f"Threshold {threshold}: Found {len(best_bets)} bets")
            
            if best_bets:
                for bet in best_bets[:3]:
                    logger.info(f"  - {bet['home_team']} vs {bet['away_team']}: {bet['bet_type']} "
                              f"(confidence: {bet['confidence']:.4f}, odds: {bet.get('best_odds', 'N/A')})")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    diagnose_predictions()