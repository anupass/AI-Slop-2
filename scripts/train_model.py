import logging
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml import BettingModelTrainer, DataProcessor
from src.database import DatabaseManager
from src.utils import setup_logger
from config import HISTORICAL_DATA_PATH, MODEL_PATH

logger = setup_logger(__name__)

def train_model():
    """Train betting prediction model"""
    
    logger.info("=" * 60)
    logger.info("Starting model training...")
    logger.info("=" * 60)
    
    try:
        db = DatabaseManager()
        data_processor = DataProcessor()
        trainer = BettingModelTrainer()
        
        # Load historical data
        logger.info(f"Loading historical data from {HISTORICAL_DATA_PATH}")
        
        if not Path(HISTORICAL_DATA_PATH).exists():
            logger.error(f"Historical data file not found: {HISTORICAL_DATA_PATH}")
            return {
                'status': 'error',
                'error': 'Historical data file not found',
                'timestamp': datetime.now().isoformat()
            }
        
        with open(HISTORICAL_DATA_PATH, 'r') as f:
            historical_data = json.load(f)
        
        logger.info(f"[OK] Loaded {len(historical_data)} historical fixtures")
        
        # Prepare training data
        logger.info("Preparing training data...")
        training_df = data_processor.create_features_from_fixtures(historical_data)
        logger.info(f"[OK] Prepared {len(training_df)} fixtures with features")
        
        # Log sample data
        logger.info(f"Sample training data:")
        logger.info(f"  Columns: {training_df.columns.tolist()}")
        logger.info(f"  Shape: {training_df.shape}")
        logger.info(f"  Goals range: {training_df['home_goals'].min()}-{training_df['home_goals'].max()}")
        
        # Train models
        logger.info("Training models...")
        performance_metrics = trainer.train_models(training_df.to_dict('records'))
        
        # Log performance
        logger.info("\nModel Performance Summary:")
        logger.info("-" * 60)
        
        total_accuracy = 0
        total_precision = 0
        total_recall = 0
        total_f1 = 0
        
        for bet_type, metrics in performance_metrics.items():
            logger.info(f"\n{bet_type}:")
            logger.info(f"  Accuracy:  {metrics['accuracy']:.4f}")
            logger.info(f"  Precision: {metrics['precision']:.4f}")
            logger.info(f"  Recall:    {metrics['recall']:.4f}")
            logger.info(f"  F1 Score:  {metrics['f1_score']:.4f}")
            logger.info(f"  Samples:   {metrics['train_size']} train / {metrics['test_size']} test")
            
            total_accuracy += metrics['accuracy']
            total_precision += metrics['precision']
            total_recall += metrics['recall']
            total_f1 += metrics['f1_score']
        
        # Calculate averages
        num_models = len(performance_metrics)
        avg_accuracy = total_accuracy / num_models
        avg_precision = total_precision / num_models
        avg_recall = total_recall / num_models
        avg_f1 = total_f1 / num_models
        
        logger.info("\n" + "=" * 60)
        logger.info("Average Performance:")
        logger.info(f"  Accuracy:  {avg_accuracy:.4f}")
        logger.info(f"  Precision: {avg_precision:.4f}")
        logger.info(f"  Recall:    {avg_recall:.4f}")
        logger.info(f"  F1 Score:  {avg_f1:.4f}")
        logger.info("=" * 60)
        
        # Store in database
        db.insert_model_performance((
            1,  # model_version
            avg_accuracy,
            avg_precision,
            avg_recall,
            avg_f1,
            len(training_df),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        logger.info("[OK] Model training completed successfully!")
        logger.info(f"[OK] Models saved to {MODEL_PATH}")
        logger.info(f"[OK] Performance metrics stored in database")
        
        return {
            'status': 'success',
            'model_path': MODEL_PATH,
            'performance': {
                'accuracy': float(avg_accuracy),
                'precision': float(avg_precision),
                'recall': float(avg_recall),
                'f1_score': float(avg_f1)
            },
            'training_samples': len(training_df),
            'models_trained': num_models,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Error training model: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == '__main__':
    result = train_model()
    print("\n" + "=" * 60)
    print(json.dumps(result, indent=2))
    print("=" * 60)