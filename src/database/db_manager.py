import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import DATABASE_PATH

class DatabaseManager:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Parleys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parleys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parley_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                total_odds REAL NOT NULL,
                bet_amount REAL NOT NULL,
                potential_return REAL NOT NULL,
                actual_return REAL,
                win_count INTEGER,
                loss_count INTEGER,
                data JSON NOT NULL,
                created_at_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Individual bets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parley_id INTEGER NOT NULL,
                bet_type TEXT NOT NULL,
                match_id TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                prediction TEXT NOT NULL,
                odds REAL NOT NULL,
                status TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL,
                result TEXT,
                FOREIGN KEY (parley_id) REFERENCES parleys(id)
            )
        ''')

        # Training data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT NOT NULL,
                league TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_goals INTEGER,
                away_goals INTEGER,
                bet_type TEXT NOT NULL,
                prediction TEXT NOT NULL,
                odds REAL NOT NULL,
                result INTEGER NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL,
                match_date TEXT NOT NULL
            )
        ''')

        # Model performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_version INTEGER NOT NULL,
                accuracy REAL NOT NULL,
                precision REAL NOT NULL,
                recall REAL NOT NULL,
                f1_score REAL NOT NULL,
                training_data_size INTEGER NOT NULL,
                trained_at TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()

    def insert_parley(self, parley_data):
        """Insert a new parley"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO parleys 
            (parley_date, created_at, status, total_odds, bet_amount, potential_return, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            parley_data['parley_date'],
            parley_data['created_at'],
            'pending',
            parley_data['total_odds'],
            parley_data['bet_amount'],
            parley_data['potential_return'],
            json.dumps(parley_data)
        ))
        
        parley_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return parley_id

    def insert_bet(self, bet_data):
        """Insert a bet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bets 
            (parley_id, bet_type, match_id, home_team, away_team, prediction, odds, status, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bet_data['parley_id'],
            bet_data['bet_type'],
            bet_data['match_id'],
            bet_data['home_team'],
            bet_data['away_team'],
            bet_data['prediction'],
            bet_data['odds'],
            'pending',
            bet_data['confidence'],
            bet_data['created_at']
        ))
        
        conn.commit()
        conn.close()

    def get_all_parleys(self):
        """Retrieve all parleys"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM parleys ORDER BY created_at_timestamp DESC')
        parleys = cursor.fetchall()
        conn.close()
        return parleys

    def get_parley_by_id(self, parley_id):
        """Get parley by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM parleys WHERE id = ?', (parley_id,))
        parley = cursor.fetchone()
        conn.close()
        return parley

    def update_parley_status(self, parley_id, status, actual_return=None):
        """Update parley status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if actual_return is not None:
            cursor.execute('''
                UPDATE parleys 
                SET status = ?, actual_return = ?
                WHERE id = ?
            ''', (status, actual_return, parley_id))
        else:
            cursor.execute('''
                UPDATE parleys 
                SET status = ?
                WHERE id = ?
            ''', (status, parley_id))
        
        conn.commit()
        conn.close()

    def insert_training_data(self, training_data):
        """Insert training data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO training_data 
            (match_id, league, home_team, away_team, home_goals, away_goals, 
             bet_type, prediction, odds, result, confidence, created_at, match_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', training_data)
        
        conn.commit()
        conn.close()

    def get_training_data(self, limit=None):
        """Get training data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if limit:
            cursor.execute('SELECT * FROM training_data ORDER BY match_date DESC LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM training_data ORDER BY match_date DESC')
        
        data = cursor.fetchall()
        conn.close()
        return data

    def insert_model_performance(self, performance_data):
        """Insert model performance metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO model_performance 
            (model_version, accuracy, precision, recall, f1_score, training_data_size, trained_at, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', performance_data)
        
        conn.commit()
        conn.close()

    def get_latest_model_performance(self):
        """Get latest model performance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM model_performance ORDER BY trained_at DESC LIMIT 1')
        data = cursor.fetchone()
        conn.close()
        return data
