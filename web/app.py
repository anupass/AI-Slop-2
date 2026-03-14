from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from src.api_handlers import OddsAPIHandler, FootballAPIHandler
from src.ml import BettingPredictor
from src.betting_engine import ParleyBuilder
from src.utils import setup_logger
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG

# Setup logger
logger = setup_logger(__name__)

# Create Flask app with explicit paths
template_path = Path(__file__).parent / 'templates'
static_path = Path(__file__).parent / 'static'

app = Flask(__name__, 
            template_folder=str(template_path),
            static_folder=str(static_path))

CORS(app)

logger.info(f"Flask app initialized")
logger.info(f"  Template folder: {app.template_folder}")
logger.info(f"  Static folder: {app.static_folder}")

# Initialize components
try:
    db = DatabaseManager()
    odds_handler = OddsAPIHandler()
    football_handler = FootballAPIHandler()
    predictor = BettingPredictor()
    parley_builder = ParleyBuilder()
    logger.info("All components initialized successfully")
except Exception as e:
    logger.error(f"Error initializing components: {e}")
    raise

# ==================== HTML ROUTES ====================

@app.route('/')
def index():
    """Serve main dashboard page"""
    logger.info("Loading index page")
    return render_template('index.html')

@app.route('/parley-detail')
def parley_detail_page():
    """Serve parley detail page"""
    logger.info("Loading parley detail page")
    return render_template('parley_detail.html')

# ==================== TEST ROUTES ====================

@app.route('/test-route')
def test_route():
    """Test if routing works"""
    return "✓ Routing works! Template folder: " + str(app.template_folder)

@app.route('/test-api')
def test_api():
    """Test API"""
    return jsonify({'status': 'API works!', 'message': 'Flask routing is functioning correctly'})

# ==================== API ROUTES ====================

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """Get dashboard statistics"""
    try:
        all_parleys = db.get_all_parleys()
        
        total_parleys = len(all_parleys)
        won_parleys = len([p for p in all_parleys if p[3] == 'won'])
        pending_parleys = len([p for p in all_parleys if p[3] == 'pending'])
        lost_parleys = len([p for p in all_parleys if p[3] == 'lost'])
        
        total_wagered = sum([p[5] for p in all_parleys]) if all_parleys else 0
        total_returned = sum([p[7] if p[7] else 0 for p in all_parleys]) if all_parleys else 0
        
        roi = ((total_returned - total_wagered) / total_wagered * 100) if total_wagered > 0 else 0
        
        model_perf = db.get_latest_model_performance()
        
        return jsonify({
            'total_parleys': total_parleys,
            'won_parleys': won_parleys,
            'pending_parleys': pending_parleys,
            'lost_parleys': lost_parleys,
            'total_wagered': total_wagered,
            'total_returned': total_returned,
            'roi': roi,
            'win_rate': (won_parleys / total_parleys * 100) if total_parleys > 0 else 0,
            'model_accuracy': model_perf[2] if model_perf else 0,
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/parleys', methods=['GET'])
def get_parleys():
    """Get all parleys"""
    try:
        parleys = db.get_all_parleys()
        parley_list = []
        
        for p in parleys:
            parley_list.append({
                'id': p[0],
                'date': p[1],
                'created_at': p[2],
                'status': p[3],
                'total_odds': p[4],
                'bet_amount': p[5],
                'potential_return': p[6],
                'actual_return': p[7],
                'win_count': p[8] if len(p) > 8 else 0,
                'loss_count': p[9] if len(p) > 9 else 0
            })
        
        return jsonify(parley_list)
    except Exception as e:
        logger.error(f"Error fetching parleys: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/parley/<int:parley_id>', methods=['GET'])
def get_parley_detail(parley_id):
    """Get parley details with all legs"""
    try:
        logger.info(f"Fetching parley {parley_id}")
        parley = db.get_parley_by_id(parley_id)
        if not parley:
            logger.warning(f"Parley {parley_id} not found")
            return jsonify({'error': 'Parley not found'}), 404
        
        # Get parley data
        parley_data = {
            'id': parley[0],
            'date': parley[1],
            'created_at': parley[2],
            'status': parley[3],
            'total_odds': parley[4],
            'bet_amount': parley[5],
            'potential_return': parley[6],
            'actual_return': parley[7],
            'win_count': parley[8] if len(parley) > 8 else 0,
            'loss_count': parley[9] if len(parley) > 9 else 0
        }
        
        # Get all bets (legs) for this parley
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bets WHERE parley_id = ? ORDER BY id', (parley_id,))
        bets = cursor.fetchall()
        conn.close()
        
        legs = []
        for bet in bets:
            leg = {
                'id': bet[0],
                'bet_type': bet[2] if len(bet) > 2 else '',
                'match_id': bet[3] if len(bet) > 3 else '',
                'home_team': bet[4] if len(bet) > 4 else '',
                'away_team': bet[5] if len(bet) > 5 else '',
                'prediction': bet[6] if len(bet) > 6 else '',
                'odds': bet[7] if len(bet) > 7 else 0,
                'status': bet[8] if len(bet) > 8 else 'pending',
                'confidence': bet[9] if len(bet) > 9 else 0,
                'created_at': bet[10] if len(bet) > 10 else '',
                'result': bet[11] if len(bet) > 11 else None
            }
            legs.append(leg)
        
        parley_data['legs'] = legs
        parley_data['num_legs'] = len(legs)
        
        logger.info(f"Returning parley {parley_id} with {len(legs)} legs")
        return jsonify(parley_data)
    except Exception as e:
        logger.error(f"Error fetching parley details: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/today-parleys', methods=['GET'])
def get_today_parleys():
    """Get today's parleys"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        parleys = db.get_all_parleys()
        
        today_parleys = [p for p in parleys if p[1] == today]
        
        return jsonify({
            'count': len(today_parleys),
            'parleys': [
                {
                    'id': p[0],
                    'status': p[3],
                    'bet_amount': p[5],
                    'potential_return': p[6],
                    'actual_return': p[7]
                }
                for p in today_parleys
            ]
        })
    except Exception as e:
        logger.error(f"Error fetching today's parleys: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get betting history"""
    try:
        parleys = db.get_all_parleys()
        
        history = []
        for p in parleys:
            history.append({
                'date': p[1],
                'status': p[3],
                'bet_amount': p[5],
                'potential_return': p[6],
                'actual_return': p[7],
                'profit': (p[7] - p[5]) if p[7] else None
            })
        
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model-performance', methods=['GET'])
def get_model_performance():
    """Get model performance metrics"""
    try:
        perf = db.get_latest_model_performance()
        
        if not perf:
            return jsonify({
                'accuracy': 0,
                'precision': 0,
                'recall': 0,
                'f1_score': 0,
                'training_data_size': 0,
                'trained_at': None
            })
        
        return jsonify({
            'accuracy': perf[2],
            'precision': perf[3],
            'recall': perf[4],
            'f1_score': perf[5],
            'training_data_size': perf[6],
            'trained_at': perf[7]
        })
    except Exception as e:
        logger.error(f"Error fetching model performance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/odds', methods=['GET'])
def get_current_odds():
    """Get current odds for all sports"""
    try:
        odds_data = odds_handler.get_all_upcoming_odds()
        return jsonify(odds_data)
    except Exception as e:
        logger.error(f"Error fetching odds: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """Get predictions for upcoming matches"""
    try:
        data = request.json
        matches = data.get('matches', [])
        
        predictions = []
        for match in matches:
            pred = predictor.predict_match(match)
            predictions.append({
                'match_id': match.get('match_id'),
                'predictions': pred
            })
        
        return jsonify(predictions)
    except Exception as e:
        logger.error(f"Error making predictions: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {error}")
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    return jsonify({'error': 'Internal server error'}), 500