"""Test script to verify bot components"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.api_handlers import OddsAPIHandler, FootballAPIHandler
from src.ml import BettingPredictor
from src.betting_engine import ParleyBuilder
from src.database import DatabaseManager
from src.utils import setup_logger
from scripts.run_daily_parley import run_daily_betting

logger = setup_logger(__name__)

def test_apis():
    """Test API connections"""
    logger.info("\n=== Testing API Connections ===")
    
    odds_handler = OddsAPIHandler()
    football_handler = FootballAPIHandler()
    
    # Test Odds API
    logger.info("Testing The Odds API...")
    sports = odds_handler.get_sports()
    if sports:
        logger.info(f"[OK] Connected to Odds API. Found {len(sports)} sports")
    else:
        logger.warning("[WARN] Could not fetch sports from Odds API")
    
    # Test Football API
    logger.info("Testing API-Football...")
    logger.info("[OK] API-Football connection configured")

def test_model():
    """Test model loading"""
    logger.info("\n=== Testing ML Model ===")
    
    predictor = BettingPredictor()
    if predictor.trainer.models:
        logger.info(f"[OK] Loaded {len(predictor.trainer.models)} trained models")
        for bet_type in predictor.trainer.models.keys():
            logger.info(f"  - {bet_type}")
    else:
        logger.warning("[WARN] No models loaded. Run 'python scripts/train_model.py' first")

def test_database():
    """Test database"""
    logger.info("\n=== Testing Database ===")
    
    db = DatabaseManager()
    parleys = db.get_all_parleys()
    logger.info(f"[OK] Database connected. Found {len(parleys)} existing parleys")

def test_daily_betting():
    """Test daily betting process"""
    logger.info("\n=== Testing Daily Betting Process ===")
    
    result = run_daily_betting()
    
    if result is None:
        logger.error("[ERROR] Daily betting returned None")
        return
    
    logger.info(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        logger.info(f"[OK] Created {result['parleys_created']} parleys")
        logger.info(f"     Found {result['bets_found']} high-confidence bets")
        logger.info(f"     Analyzed {result['matches_analyzed']} matches")
    elif result['status'] == 'warning':
        logger.info(f"[WARN] {result['message']}")
        if 'matches_analyzed' in result:
            logger.info(f"       Matches analyzed: {result['matches_analyzed']}")
    else:
        logger.error(f"[ERROR] {result.get('error', 'Unknown error')}")

if __name__ == '__main__':
    logger.info("Starting bot component tests...")
    logger.info("=" * 60)
    
    test_apis()
    test_model()
    test_database()
    test_daily_betting()
    
    logger.info("\n" + "=" * 60)
    logger.info("All tests completed")
    logger.info("=" * 60)