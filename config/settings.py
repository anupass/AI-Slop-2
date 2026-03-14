import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# API Keys
ODDS_API_KEY = os.getenv('ODDS_API_KEY', 'your_odds_api_key_here')
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY', 'your_football_api_key_here')

# API Endpoints
ODDS_API_BASE = 'https://api.the-odds-api.com/v4'
FOOTBALL_API_BASE = 'https://v3.football.api-sports.io'

# Betting Configuration
DAILY_PARLEYS = 5
MIN_CONFIDENCE_THRESHOLD = 0.45  # Lowered from 0.55 to get initial bets
MAX_BET_AMOUNT = 100  # USD
PARLEY_SIZE = 3  # Number of bets per parley

# Supported Bet Types
BET_TYPES = {
    'h2h': 'Head to Head (Win)',
    'spreads': 'Spread/Handicap',
    'totals': 'Over/Under Total',
    'double_chance': 'Double Chance',
    'btts': 'Both Teams to Score',
    'corners': 'Corners',
}

# Supported Sports
SUPPORTED_SPORTS = [
    'soccer_epl',        # English Premier League
    'americanfootball_nfl',  # NFL
]

# Database
DATABASE_PATH = 'data/parleys.db'
HISTORICAL_DATA_PATH = 'data/historical_data.json'
MODEL_PATH = 'data/model/betting_model.pkl'

# Training Configuration
TRAINING_PERIOD_DAYS = 90
HISTORICAL_DATA_YEARS = 2
MODEL_UPDATE_FREQUENCY = 'daily'  # daily, weekly, monthly

# Web Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/betting_bot.log'