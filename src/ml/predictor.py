import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .trainer import BettingModelTrainer
from .data_processor import DataProcessor
from config import MODEL_PATH

logger = logging.getLogger(__name__)

class BettingPredictor:
    def __init__(self):
        self.trainer = BettingModelTrainer()
        # Try to load models, continue if they don't exist
        if not self.trainer.load_models():
            logger.warning("Models not loaded. Predictions will not work until models are trained.")
        self.data_processor = DataProcessor()

    def predict_match(self, match_data):
        """Predict outcomes for a match"""
        
        if not self.trainer.models:
            logger.error("No models available for prediction")
            return {}
        
        features = self._prepare_features(match_data)
        
        if features is None:
            return {}
        
        predictions = {}
        for bet_type in self.trainer.models.keys():
            pred = self.trainer.predict(features, bet_type)
            if pred:
                predictions[bet_type] = pred
        
        return predictions

    def _prepare_features(self, match_data):
        """Prepare feature vector from match data"""
        try:
            # Ensure match_data is a dict
            if isinstance(match_data, str):
                logger.error(f"Invalid match data type: string. Expected dict")
                return None
            
            # Extract features in the correct order
            feature_values = [
                float(match_data.get('home_goals', 0) or 0),
                float(match_data.get('away_goals', 0) or 0),
                float(match_data.get('home_shots', 0) or 0),
                float(match_data.get('away_shots', 0) or 0),
                float(match_data.get('home_possession', 50) or 50),
                float(match_data.get('away_possession', 50) or 50),
            ]
            
            # Create DataFrame with proper column names
            feature_df = pd.DataFrame(
                [feature_values],
                columns=self.trainer.feature_columns
            )
            
            return feature_df
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return None

    def get_best_bets(self, matches, odds_data, min_confidence=0.55):
        """Get best bets from available matches"""
        best_bets = []
        
        if not self.trainer.models:
            logger.warning("No models available for predictions")
            return best_bets
        
        for match in matches:
            # Ensure match is a dict
            if isinstance(match, str):
                logger.warning(f"Skipping invalid match data: {match}")
                continue
            
            predictions = self.predict_match(match)
            
            if not predictions:
                continue
            
            for bet_type, pred in predictions.items():
                confidence = max(pred['confidence_class_0'], pred['confidence_class_1'])
                predicted_outcome = 'class_1' if pred['confidence_class_1'] > pred['confidence_class_0'] else 'class_0'
                
                if confidence >= min_confidence:
                    # Find best odds for this bet
                    best_odd = self._find_best_odds(match, bet_type, predicted_outcome, odds_data)
                    
                    # Use default odds if not found (will use bookmaker's odds)
                    if best_odd:
                        bet_info = {
                            'match_id': match.get('match_id'),
                            'home_team': match.get('home_team'),
                            'away_team': match.get('away_team'),
                            'bet_type': bet_type,
                            'prediction': predicted_outcome,
                            'confidence': confidence,
                            'commence_time': match.get('commence_time'),
                            'best_odds': best_odd['odds'],
                            'bookmaker': best_odd['bookmaker']
                        }
                        best_bets.append(bet_info)
                    else:
                        # Use default odds (1.5) if not found
                        bet_info = {
                            'match_id': match.get('match_id'),
                            'home_team': match.get('home_team'),
                            'away_team': match.get('away_team'),
                            'bet_type': bet_type,
                            'prediction': predicted_outcome,
                            'confidence': confidence,
                            'commence_time': match.get('commence_time'),
                            'best_odds': 1.5,  # Default odds
                            'bookmaker': 'unknown'
                        }
                        best_bets.append(bet_info)
        
        # Sort by confidence
        best_bets.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"Found {len(best_bets)} bets with confidence >= {min_confidence}")
        
        return best_bets

    def _find_best_odds(self, match, bet_type, prediction, odds_data):
        """Find best odds for a specific prediction"""
        best_odd = None
        best_value = 0
        
        try:
            match_id = match.get('match_id')
            
            # Search through all match odds
            for match_odds in odds_data:
                if isinstance(match_odds, str):
                    continue
                
                # Check if this is the right match
                if match_odds.get('match_id') != match_id:
                    continue
                
                # Look through bookmakers
                for bookmaker, bookmaker_data in match_odds.get('odds_by_bookmaker', {}).items():
                    markets = bookmaker_data.get('markets', {})
                    
                    if bet_type in markets:
                        market_odds = markets[bet_type]
                        
                        # Find best odds for any outcome (we'll use the highest)
                        for outcome, odds_value in market_odds.items():
                            if odds_value and isinstance(odds_value, (int, float)) and odds_value > best_value:
                                best_value = odds_value
                                best_odd = {
                                    'odds': float(odds_value),
                                    'bookmaker': bookmaker,
                                    'outcome': outcome,
                                    'bet_type': bet_type
                                }
        except Exception as e:
            logger.debug(f"Error finding best odds: {e}")
        
        return best_odd