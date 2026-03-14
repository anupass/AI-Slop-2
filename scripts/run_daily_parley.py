#!/usr/bin/env python3
"""
Run daily parley generation with real API odds
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.api_handlers import OddsAPIHandler
from src.ml import BettingPredictor
from src.utils import setup_logger
from config import SUPPORTED_SPORTS
from datetime import datetime
import random

logger = setup_logger(__name__)

def main():
    """Main function to generate daily parleys"""
    print("Starting daily parley generation...")
    logger.info("Starting daily parley generation...")
    
    try:
        print("Initializing components...")
        db = DatabaseManager()
        odds_handler = OddsAPIHandler()
        predictor = BettingPredictor()
        print("Components initialized")
        
        # Get real matches and odds from API
        print("Fetching upcoming matches from API...")
        logger.info("Fetching upcoming matches from API...")
        all_matches = []
        
        for sport_key in SUPPORTED_SPORTS:
            try:
                print(f"Fetching {sport_key}...")
                odds_data = odds_handler.get_odds(sport_key)
                if odds_data:
                    print(f"Found {len(odds_data)} matches for {sport_key}")
                    logger.info(f"Found {len(odds_data)} matches for {sport_key}")
                    all_matches.extend(odds_data)
                else:
                    print(f"No odds data for {sport_key}")
            except Exception as e:
                print(f"Error fetching {sport_key}: {e}")
                logger.error(f"Error fetching odds for {sport_key}: {e}")
                continue
        
        print(f"Total matches: {len(all_matches)}")
        
        if not all_matches:
            print("No matches found from API")
            logger.warning("No matches found from API")
            return
        
        print(f"Processing {len(all_matches)} matches...")
        logger.info(f"Processing {len(all_matches)} matches...")
        
        # Generate predictions and odds for each match
        predictions_list = []
        for i, match in enumerate(all_matches[:15]):  # Limit to 15 matches
            try:
                match_info = {
                    'id': match.get('id'),
                    'home_team': match.get('home_team'),
                    'away_team': match.get('away_team'),
                    'sport_key': match.get('sport_key'),
                    'commence_time': match.get('commence_time')
                }
                
                print(f"[{i+1}/15] Predicting {match_info['home_team']} vs {match_info['away_team']}...")
                
                # Get predictions
                pred_data = predictor.predict_match(match_info)
                
                # Extract odds from bookmakers
                odds_map = extract_bookmaker_odds(match)
                
                # Extract class_1 confidence values
                pred_confidences = {}
                for bet_type, classes in pred_data.items():
                    # Get class_1 confidence (the positive prediction)
                    class_1_conf = classes.get('confidence_class_1', 0)
                    pred_confidences[bet_type] = class_1_conf
                
                pred_with_odds = {
                    'match_id': match_info['id'],
                    'home_team': match_info['home_team'],
                    'away_team': match_info['away_team'],
                    'predictions': pred_confidences,
                    'odds': odds_map
                }
                
                predictions_list.append(pred_with_odds)
                logger.info(f"Prediction: {match_info['home_team']} vs {match_info['away_team']}")
                
            except Exception as e:
                print(f"Error processing match: {e}")
                logger.error(f"Error processing match: {e}")
                import traceback
                print(traceback.format_exc())
                continue
        
        print(f"\nGenerated {len(predictions_list)} predictions")
        
        if not predictions_list:
            print("No predictions generated")
            logger.warning("No predictions generated")
            return
        
        logger.info(f"Generated {len(predictions_list)} predictions")
        
        # Build parleys with target of 3 legs @ 5.0 total odds
        print(f"\nBuilding {5} parleys...")
        build_parleys(db, predictions_list)
        
        print("\nDaily parley generation completed!")
        logger.info("Daily parley generation completed!")
    
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        logger.error(f"Error in daily parley generation: {e}")
        import traceback
        print(traceback.format_exc())
        logger.error(traceback.format_exc())

def extract_bookmaker_odds(match):
    """Extract best odds from bookmakers for each market"""
    odds_map = {}
    
    try:
        bookmakers = match.get('bookmakers', [])
        
        for bookmaker in bookmakers:
            markets = bookmaker.get('markets', [])
            
            for market in markets:
                market_key = market.get('key')
                outcomes = market.get('outcomes', [])
                
                for outcome in outcomes:
                    name = outcome.get('name', '').lower()
                    price = outcome.get('price', 1.5)
                    
                    # Map to bet types
                    if market_key == 'h2h':
                        if 'home' in name or name == match.get('home_team', '').lower():
                            key = 'h2h_home'
                            if key not in odds_map or price > odds_map[key]:
                                odds_map[key] = price
                        elif 'away' in name or name == match.get('away_team', '').lower():
                            key = 'h2h_away'
                            if key not in odds_map or price > odds_map[key]:
                                odds_map[key] = price
                        elif 'draw' in name:
                            key = 'h2h_draw'
                            if key not in odds_map or price > odds_map[key]:
                                odds_map[key] = price
                    
                    elif market_key == 'totals':
                        if 'over' in name:
                            key = 'over_2_5'
                            if key not in odds_map or price > odds_map[key]:
                                odds_map[key] = price
                        elif 'under' in name:
                            key = 'under_2_5'
                            if key not in odds_map or price > odds_map[key]:
                                odds_map[key] = price
    
    except Exception as e:
        logger.error(f"Error extracting odds: {e}")
    
    # Set defaults if no odds found (lower defaults for safer bets)
    defaults = {
        'h2h_home': 1.6,
        'h2h_away': 1.9,
        'h2h_draw': 3.2,
        'over_2_5': 1.8,
        'under_2_5': 1.8,
        'btts_yes': 1.9,
        'btts_no': 1.8
    }
    
    for key, value in defaults.items():
        if key not in odds_map:
            odds_map[key] = value
    
    return odds_map

def build_parleys(db, predictions_list):
    """Build 5 parleys with 3 legs each targeting ~5.0 total odds"""
    try:
        num_parleys = 5
        created_count = 0
        target_total_odds = 5.0
        
        print(f"Starting to build {num_parleys} parleys from {len(predictions_list)} predictions...")
        
        for parley_num in range(num_parleys):
            if len(predictions_list) < 3:
                print(f"Not enough predictions for parley {parley_num + 1}")
                logger.warning(f"Not enough predictions for parley {parley_num + 1}")
                break
            
            # Select 3 random predictions
            selected = random.sample(predictions_list, 3)
            
            legs = []
            total_odds = 1.0
            min_confidence = 0.01
            
            print(f"\nBuilding Parley #{parley_num + 1}:")
            logger.info(f"\nBuilding Parley #{parley_num + 1}:")
            
            for pred in selected:
                pred_confidences = pred.get('predictions', {})
                odds_map = pred.get('odds', {})
                
                # Find bet type with highest confidence AND reasonable odds
                candidates = []
                
                for bet_type, confidence in pred_confidences.items():
                    if confidence >= min_confidence:
                        odds = odds_map.get(bet_type, 1.5)
                        # Prefer odds between 1.5-2.0 for safer bets
                        if 1.5 <= odds <= 2.0:
                            candidates.append({
                                'bet_type': bet_type,
                                'confidence': confidence,
                                'odds': odds,
                                'score': confidence * odds  # Higher score = better bet
                            })
                
                if not candidates:
                    # Fallback: use highest confidence regardless of odds
                    best_bet = None
                    best_confidence = 0
                    best_odds = 1.5
                    
                    for bet_type, confidence in pred_confidences.items():
                        if confidence > best_confidence:
                            odds = odds_map.get(bet_type, 1.5)
                            best_bet = bet_type
                            best_confidence = confidence
                            best_odds = float(odds)
                else:
                    # Pick best candidate (highest score)
                    best_candidate = max(candidates, key=lambda x: x['score'])
                    best_bet = best_candidate['bet_type']
                    best_confidence = best_candidate['confidence']
                    best_odds = best_candidate['odds']
                
                if best_bet:
                    leg = {
                        'match_id': pred['match_id'],
                        'home_team': pred['home_team'],
                        'away_team': pred['away_team'],
                        'bet_type': best_bet,
                        'prediction': best_bet,
                        'odds': round(best_odds, 2),
                        'confidence': round(best_confidence, 4),
                        'status': 'pending'
                    }
                    legs.append(leg)
                    total_odds *= best_odds
                    msg = f"  {pred['home_team']} vs {pred['away_team']}: {best_bet} @ {best_odds:.2f}"
                    print(msg)
                    logger.info(msg)
            
            # Create parley with exactly 3 legs
            if len(legs) == 3:
                # Cap total odds at reasonable level if too high
                if total_odds > 10.0:
                    print(f"Total odds {total_odds:.2f} too high, skipping parley")
                    logger.warning(f"Total odds {total_odds:.2f} too high, skipping parley")
                    continue
                
                bet_amount = 50  # $50 per parley
                potential_return = bet_amount * total_odds
                
                print(f"Creating parley... total_odds={total_odds:.2f}")
                parley_id = db.create_parley(
                    date=datetime.now().strftime('%Y-%m-%d'),
                    status='pending',
                    total_odds=round(total_odds, 2),
                    bet_amount=round(bet_amount, 2),
                    potential_return=round(potential_return, 2)
                )
                print(f"Parley created with ID: {parley_id}")
                
                for leg in legs:
                    db.create_bet(
                        parley_id=parley_id,
                        match_id=leg['match_id'],
                        bet_type=leg['bet_type'],
                        home_team=leg['home_team'],
                        away_team=leg['away_team'],
                        prediction=leg['prediction'],
                        odds=leg['odds'],
                        confidence=leg['confidence'],
                        status=leg['status']
                    )
                
                msg = f"[OK] Created parley #{parley_id}: {total_odds:.2f} odds, ${potential_return:.2f} potential"
                print(msg)
                logger.info(msg)
                created_count += 1
            else:
                print(f"Skipping parley: only {len(legs)} legs (need 3)")
        
        print(f"\nSuccessfully created {created_count} parleys")
        logger.info(f"Successfully created {created_count} parleys")
    
    except Exception as e:
        print(f"ERROR in build_parleys: {e}")
        logger.error(f"Error building parleys: {e}")
        import traceback
        print(traceback.format_exc())
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()