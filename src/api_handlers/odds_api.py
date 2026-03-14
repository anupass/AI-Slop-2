import requests
from datetime import datetime, timedelta
from config import ODDS_API_BASE, ODDS_API_KEY, SUPPORTED_SPORTS
import logging

logger = logging.getLogger(__name__)

class OddsAPIHandler:
    def __init__(self, api_key=ODDS_API_KEY):
        self.api_key = api_key
        self.base_url = ODDS_API_BASE

    def get_sports(self):
        """Get available sports"""
        try:
            response = requests.get(
                f'{self.base_url}/sports',
                params={'apiKey': self.api_key}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sports: {e}")
            return []

    def get_odds(self, sport_key, regions='us', odds_format='decimal'):
        """Get current odds for a sport"""
        try:
            params = {
                'apiKey': self.api_key,
                'regions': regions,
                'oddsFormat': odds_format,
                'markets': 'h2h,spreads,totals'
            }
            
            response = requests.get(
                f'{self.base_url}/sports/{sport_key}/odds',
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching odds for {sport_key}: {e}")
            return []

    def get_all_upcoming_odds(self):
        """Get odds for all supported sports"""
        all_odds = {}
        
        for sport in SUPPORTED_SPORTS:
            logger.info(f"Fetching odds for {sport}")
            odds = self.get_odds(sport)
            if odds:
                all_odds[sport] = odds
        
        return all_odds

    def parse_odds_response(self, odds_data):
        """Parse odds API response into structured format"""
        parsed_matches = []
        
        for match in odds_data:
            match_info = {
                'match_id': match['id'],
                'home_team': match['home_team'],
                'away_team': match['away_team'],
                'commence_time': match['commence_time'],
                'sport_key': match['sport_key'],
                'odds_by_bookmaker': {}
            }
            
            for bookmaker in match.get('bookmakers', []):
                bookmaker_odds = {
                    'bookmaker': bookmaker['key'],
                    'markets': {}
                }
                
                for market in bookmaker.get('markets', []):
                    market_key = market['key']
                    outcomes = {}
                    
                    for outcome in market.get('outcomes', []):
                        outcomes[outcome['name']] = outcome['price']
                    
                    bookmaker_odds['markets'][market_key] = outcomes
                
                match_info['odds_by_bookmaker'][bookmaker['key']] = bookmaker_odds
            
            parsed_matches.append(match_info)
        
        return parsed_matches
