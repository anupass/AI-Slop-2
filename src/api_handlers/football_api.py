import requests
from datetime import datetime, timedelta
from config import FOOTBALL_API_BASE, FOOTBALL_API_KEY
import logging

logger = logging.getLogger(__name__)

class FootballAPIHandler:
    def __init__(self, api_key=FOOTBALL_API_KEY):
        self.api_key = api_key
        self.base_url = FOOTBALL_API_BASE
        self.headers = {'x-apisports-key': api_key}

    def get_fixtures_by_date(self, date_str):
        """Get fixtures for a specific date"""
        try:
            params = {'date': date_str}
            response = requests.get(
                f'{self.base_url}/fixtures',
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching fixtures for {date_str}: {e}")
            return None

    def get_fixtures_by_league_season(self, league_id, season):
        """Get all fixtures for a league in a season"""
        try:
            params = {'league': league_id, 'season': season}
            response = requests.get(
                f'{self.base_url}/fixtures',
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching fixtures for league {league_id}, season {season}: {e}")
            return None

    def get_historical_data(self, league_id, seasons):
        """Download historical data for training"""
        all_fixtures = []
        
        for season in seasons:
            logger.info(f"Downloading fixtures for league {league_id}, season {season}")
            data = self.get_fixtures_by_league_season(league_id, season)
            
            if data and 'response' in data:
                all_fixtures.extend(data['response'])
        
        return all_fixtures

    def parse_fixture(self, fixture):
        """Parse fixture data"""
        return {
            'fixture_id': fixture['fixture']['id'],
            'date': fixture['fixture']['date'],
            'league_id': fixture['league']['id'],
            'league_name': fixture['league']['name'],
            'home_team': fixture['teams']['home']['name'],
            'away_team': fixture['teams']['away']['name'],
            'home_goals': fixture['goals']['home'],
            'away_goals': fixture['goals']['away'],
            'status': fixture['fixture']['status']['short'],
            'goals': {
                'home': fixture['goals']['home'],
                'away': fixture['goals']['away']
            },
            'shots': fixture['statistics'][0]['shots'] if fixture['statistics'] else {},
            'possession': fixture['statistics'][0]['possession'] if fixture['statistics'] else {},
        }

    def get_team_statistics(self, team_id, season):
        """Get team statistics"""
        try:
            params = {'team': team_id, 'season': season}
            response = requests.get(
                f'{self.base_url}/teams/statistics',
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching team stats for team {team_id}: {e}")
            return None

    def get_head_to_head(self, team1_id, team2_id, last=5):
        """Get head-to-head history"""
        try:
            params = {'h2h': f'{team1_id}-{team2_id}', 'last': last}
            response = requests.get(
                f'{self.base_url}/fixtures',
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching h2h for teams {team1_id} vs {team2_id}: {e}")
            return None
