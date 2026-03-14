from datetime import datetime, timedelta
import json

def get_date_range(days=7):
    """Get date range for last N days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:.2f}"

def calculate_roi(initial, final):
    """Calculate ROI"""
    if initial == 0:
        return 0
    return ((final - initial) / initial) * 100

def save_json(data, file_path):
    """Save data as JSON"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(file_path):
    """Load data from JSON"""
    with open(file_path, 'r') as f:
        return json.load(f)

def convert_odds_format(odds, from_format, to_format):
    """Convert odds between formats"""
    # Convert to decimal first
    if from_format == 'american':
        if odds > 0:
            decimal = 1 + (odds / 100)
        else:
            decimal = 1 + (100 / abs(odds))
    elif from_format == 'fractional':
        parts = odds.split('/')
        decimal = 1 + (float(parts[0]) / float(parts[1]))
    else:  # already decimal
        decimal = odds
    
    # Convert from decimal to target
    if to_format == 'american':
        if decimal >= 2:
            return (decimal - 1) * 100
        else:
            return -100 / (decimal - 1)
    elif to_format == 'fractional':
        frac = decimal - 1
        return f"{frac}:1"
    else:  # decimal
        return decimal
