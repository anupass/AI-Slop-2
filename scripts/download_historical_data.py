import logging
import sys
from pathlib import Path
from datetime import datetime
import json

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api_handlers.football_api import FootballAPIHandler
from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger
from config.settings import HISTORICAL_DATA_PATH, HISTORICAL_DATA_YEARS

logger = setup_logger(__name__)

# Major football league IDs (API-Football)
LEAGUE_IDS = {
    39: 'English Premier League',
    140: 'La Liga',
    135: 'Serie A',
    78: 'Bundesliga',
    61: 'Ligue 1'
}

def download_historical_data():
    """Download historical fixture data for training."""

    logger.info("Starting historical data download...")

    try:
        football_handler = FootballAPIHandler()
        db = DatabaseManager()

        # Only download past completed seasons
        current_year = datetime.now().year
        seasons = [year for year in range(current_year - HISTORICAL_DATA_YEARS, current_year)]
        logger.info(f"Downloading data for seasons: {seasons}")

        all_fixtures = []

        for league_id, league_name in LEAGUE_IDS.items():
            logger.info(f"Downloading {league_name} ({league_id})...")
            
            fixtures = football_handler.get_historical_data(league_id, seasons)
            logger.info(f"API returned {len(fixtures)} fixtures for {league_name}")

            for fixture_data in fixtures:
                try:
                    fixture = parse_fixture(fixture_data)

                    # Only include completed matches
                    if fixture.get('status') in ['FT', 'AET']:
                        all_fixtures.append(fixture)

                        # Prepare training data safely
                        home_goals = fixture.get('home_goals', 0)
                        away_goals = fixture.get('away_goals', 0)
                        fixture_id = fixture.get('fixture_id')
                        home_team = fixture.get('home_team', 'Unknown')
                        away_team = fixture.get('away_team', 'Unknown')
                        fixture_date = fixture.get('date', datetime.now().isoformat())

                        # Determine result
                        if home_goals > away_goals:
                            result = 'home'
                            outcome_flag = 1
                        elif home_goals == away_goals:
                            result = 'draw'
                            outcome_flag = 0
                        else:
                            result = 'away'
                            outcome_flag = -1

                        # Placeholder odds and confidence
                        training_data = (
                            fixture_id,
                            league_name,
                            home_team,
                            away_team,
                            home_goals,
                            away_goals,
                            'h2h',          # placeholder strategy
                            result,
                            1.0,             # placeholder odds
                            outcome_flag,
                            0.5,             # placeholder confidence
                            datetime.now().isoformat(),
                            fixture_date
                        )

                        db.insert_training_data(training_data)

                except Exception as e:
                    logger.warning(f"Skipping fixture due to error: {e}")
                    continue

        # Save all fixtures to JSON
        Path(HISTORICAL_DATA_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORICAL_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_fixtures, f, indent=2, ensure_ascii=False)

        logger.info(f"Downloaded {len(all_fixtures)} historical fixtures")
        logger.info(f"Data saved to {HISTORICAL_DATA_PATH}")

        return {
            'status': 'success',
            'fixtures_downloaded': len(all_fixtures),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error downloading historical data: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def parse_fixture(fixture_data):
    """
    Parse fixture data safely.
    Handles missing statistics and optional fields.
    """
    try:
        fixture = {
            'fixture_id': fixture_data.get('fixture', {}).get('id'),
            'date': fixture_data.get('fixture', {}).get('date'),
            'home_team': fixture_data.get('teams', {}).get('home', {}).get('name', 'Unknown'),
            'away_team': fixture_data.get('teams', {}).get('away', {}).get('name', 'Unknown'),
            'home_goals': fixture_data.get('goals', {}).get('home', 0),
            'away_goals': fixture_data.get('goals', {}).get('away', 0),
            'status': fixture_data.get('fixture', {}).get('status', {}).get('short', 'NS'),
            'statistics': fixture_data.get('statistics', {})  # optional
        }
        return fixture
    except Exception as e:
        logger.warning(f"Failed to parse fixture {fixture_data.get('fixture', {}).get('id')}: {e}")
        return {}

if __name__ == '__main__':
    result = download_historical_data()
    print(result)