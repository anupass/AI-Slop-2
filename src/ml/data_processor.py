import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.feature_columns = [
            'home_goals', 'away_goals', 'home_shots', 'away_shots',
            'home_possession', 'away_possession', 'home_form', 'away_form',
            'home_goal_diff', 'away_goal_diff', 'home_win_rate', 'away_win_rate'
        ]

    def prepare_training_data(self, raw_data):
        """Convert raw fixture data to training features"""
        df = pd.DataFrame(raw_data)
        
        # Calculate features
        df['home_goals'] = pd.to_numeric(df['home_goals'], errors='coerce').fillna(0)
        df['away_goals'] = pd.to_numeric(df['away_goals'], errors='coerce').fillna(0)
        df['total_goals'] = df['home_goals'] + df['away_goals']
        df['goal_diff'] = df['home_goals'] - df['away_goals']
        
        # Create outcome labels - MUST be 0 or 1, not -2 or -1
        df['home_win'] = (df['home_goals'] > df['away_goals']).astype(int)
        df['away_win'] = (df['away_goals'] > df['home_goals']).astype(int)
        df['draw'] = (df['home_goals'] == df['away_goals']).astype(int)
        df['over_2_5'] = (df['total_goals'] > 2.5).astype(int)
        df['under_2_5'] = (df['total_goals'] <= 2.5).astype(int)
        
        # Verify all targets are 0 or 1
        for col in ['home_win', 'away_win', 'draw', 'over_2_5', 'under_2_5']:
            assert df[col].isin([0, 1]).all(), f"Invalid values in {col}: {df[col].unique()}"
        
        return df

    def create_features_from_fixtures(self, fixtures):
        """Create feature matrix from fixture history"""
        features = []
        
        for fixture in fixtures:
            try:
                home_possession = fixture.get('possession', {})
                away_possession = fixture.get('possession', {})
                
                # Handle possession as dict or string
                if isinstance(home_possession, dict):
                    home_poss_val = float(home_possession.get('home', 50) or 50)
                else:
                    home_poss_val = float(str(home_possession).rstrip('%') or 50)
                
                if isinstance(away_possession, dict):
                    away_poss_val = float(away_possession.get('away', 50) or 50)
                else:
                    away_poss_val = float(str(away_possession).rstrip('%') or 50)
                
                home_shots = fixture.get('shots', {})
                away_shots = fixture.get('shots', {})
                
                if isinstance(home_shots, dict):
                    home_shots_val = float(home_shots.get('on', 0) or 0)
                else:
                    home_shots_val = 0
                
                if isinstance(away_shots, dict):
                    away_shots_val = float(away_shots.get('on', 0) or 0)
                else:
                    away_shots_val = 0
                
                feature_dict = {
                    'match_id': fixture.get('fixture_id', ''),
                    'league': fixture.get('league_name', ''),
                    'home_team': fixture.get('home_team', ''),
                    'away_team': fixture.get('away_team', ''),
                    'home_goals': float(fixture.get('home_goals') or 0),
                    'away_goals': float(fixture.get('away_goals') or 0),
                    'home_shots': home_shots_val,
                    'away_shots': away_shots_val,
                    'home_possession': home_poss_val,
                    'away_possession': away_poss_val,
                    'date': fixture.get('date', ''),
                    'status': fixture.get('status', '')
                }
                features.append(feature_dict)
            except Exception as e:
                logger.warning(f"Error processing fixture: {e}")
                continue
        
        return pd.DataFrame(features)

    def calculate_team_form(self, matches, team_name, last_n=5):
        """Calculate team form (last 5 matches)"""
        team_matches = [
            m for m in matches 
            if m['home_team'] == team_name or m['away_team'] == team_name
        ][-last_n:]
        
        wins = 0
        draws = 0
        goals_for = 0
        goals_against = 0
        
        for match in team_matches:
            if match['home_team'] == team_name:
                if match['home_goals'] > match['away_goals']:
                    wins += 1
                elif match['home_goals'] == match['away_goals']:
                    draws += 1
                goals_for += match['home_goals']
                goals_against += match['away_goals']
            else:
                if match['away_goals'] > match['home_goals']:
                    wins += 1
                elif match['away_goals'] == match['home_goals']:
                    draws += 1
                goals_for += match['away_goals']
                goals_against += match['home_goals']
        
        return {
            'wins': wins,
            'draws': draws,
            'losses': len(team_matches) - wins - draws,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'goal_diff': goals_for - goals_against,
            'avg_goals': goals_for / len(team_matches) if team_matches else 0
        }

    def normalize_features(self, X):
        """Normalize features to 0-1 range"""
        X_min = X.min()
        X_max = X.max()
        X_range = X_max - X_min
        
        # Avoid division by zero
        X_range = X_range.replace(0, 1)
        
        return (X - X_min) / X_range

    def create_training_targets(self, df):
        """Create target variables for different bet types - MUST return 0/1 values"""
        # CRITICAL FIX: Do NOT use bitwise NOT (~) on boolean series in pandas
        # Use .astype(int) to convert boolean to integer (True->1, False->0)
        
        btts_yes_cond = (df['home_goals'] > 0) & (df['away_goals'] > 0)
        btts_no_cond = (df['home_goals'] == 0) | (df['away_goals'] == 0)
        
        targets = {
            'h2h_home': (df['home_goals'] > df['away_goals']).astype(int),
            'h2h_away': (df['away_goals'] > df['home_goals']).astype(int),
            'h2h_draw': (df['home_goals'] == df['away_goals']).astype(int),
            'over_2_5': (df['home_goals'] + df['away_goals'] > 2.5).astype(int),
            'under_2_5': (df['home_goals'] + df['away_goals'] <= 2.5).astype(int),
            'btts_yes': btts_yes_cond.astype(int),
            'btts_no': btts_no_cond.astype(int),
        }
        
        # Verify all targets are valid
        for target_name, target_values in targets.items():
            unique_vals = target_values.unique()
            if not all(v in [0, 1] for v in unique_vals):
                logger.error(f"Invalid target values in {target_name}: {unique_vals}")
                raise ValueError(f"Target {target_name} contains invalid values: {unique_vals}")
        
        return targets