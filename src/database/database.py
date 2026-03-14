import sqlite3
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path='data/parleys.db'):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS parleys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            total_odds REAL NOT NULL,
            bet_amount REAL NOT NULL,
            potential_return REAL NOT NULL,
            actual_return REAL,
            win_count INTEGER DEFAULT 0,
            loss_count INTEGER DEFAULT 0
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parley_id INTEGER NOT NULL,
            match_id TEXT NOT NULL,
            bet_type TEXT NOT NULL,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            prediction TEXT NOT NULL,
            odds REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            confidence REAL NOT NULL,
            created_at TEXT NOT NULL,
            result TEXT
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            accuracy REAL NOT NULL,
            precision REAL NOT NULL,
            recall REAL NOT NULL,
            f1_score REAL NOT NULL,
            training_data_size INTEGER NOT NULL,
            trained_at TEXT NOT NULL
        )''')
        
        conn.commit()
        conn.close()
    
    def create_parley(self, date, status, total_odds, bet_amount, potential_return):
        conn = self.get_connection()
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute('''INSERT INTO parleys (date, created_at, status, total_odds, bet_amount, potential_return)
            VALUES (?, ?, ?, ?, ?, ?)''', (date, created_at, status, total_odds, bet_amount, potential_return))
        parley_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return parley_id
    
    def create_bet(self, parley_id, match_id, bet_type, home_team, away_team, prediction, odds, confidence, status='pending'):
        conn = self.get_connection()
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute('''INSERT INTO bets (parley_id, match_id, bet_type, home_team, away_team, prediction, odds, status, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (parley_id, match_id, bet_type, home_team, away_team, prediction, odds, status, confidence, created_at))
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def get_parley_by_id(self, parley_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM parleys WHERE id = ?', (parley_id,))
        parley = cursor.fetchone()
        conn.close()
        return tuple(parley) if parley else None
    
    def get_all_parleys(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM parleys ORDER BY id DESC')
        parleys = cursor.fetchall()
        conn.close()
        return [tuple(p) for p in parleys]
    
    def get_parleys_by_date(self, date):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM parleys WHERE date = ? ORDER BY id DESC', (date,))
        parleys = cursor.fetchall()
        conn.close()
        return [tuple(p) for p in parleys]
    
    def update_parley_status(self, parley_id, status, actual_return=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if actual_return:
            cursor.execute('UPDATE parleys SET status = ?, actual_return = ? WHERE id = ?', (status, actual_return, parley_id))
        else:
            cursor.execute('UPDATE parleys SET status = ? WHERE id = ?', (status, parley_id))
        conn.commit()
        conn.close()
    
    def get_bets_by_parley(self, parley_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bets WHERE parley_id = ? ORDER BY id', (parley_id,))
        bets = cursor.fetchall()
        conn.close()
        return [tuple(b) for b in bets]
    
    def update_bet_result(self, bet_id, status, result):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE bets SET status = ?, result = ? WHERE id = ?', (status, result, bet_id))
        conn.commit()
        conn.close()
    
    def get_latest_model_performance(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM model_performance ORDER BY trained_at DESC LIMIT 1')
        perf = cursor.fetchone()
        conn.close()
        return tuple(perf) if perf else None
    
    def save_model_performance(self, model_name, accuracy, precision, recall, f1_score, training_data_size):
        conn = self.get_connection()
        cursor = conn.cursor()
        trained_at = datetime.now().isoformat()
        cursor.execute('''INSERT INTO model_performance (model_name, accuracy, precision, recall, f1_score, training_data_size, trained_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)''', (model_name, accuracy, precision, recall, f1_score, training_data_size, trained_at))
        conn.commit()
        conn.close()
    
    def get_betting_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        stats = {}
        cursor.execute('SELECT COUNT(*) as count FROM parleys')
        stats['total_parleys'] = cursor.fetchone()[0]
        cursor.execute('SELECT status, COUNT(*) as count FROM parleys GROUP BY status')
        for row in cursor.fetchall():
            stats[f'{row[0]}_parleys'] = row[1]
        cursor.execute('SELECT SUM(bet_amount) FROM parleys')
        stats['total_wagered'] = cursor.fetchone()[0] or 0
        cursor.execute('SELECT SUM(actual_return) FROM parleys WHERE actual_return IS NOT NULL')
        stats['total_returned'] = cursor.fetchone()[0] or 0
        conn.close()
        return stats