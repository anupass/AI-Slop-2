import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from config import MODEL_PATH
from .data_processor import DataProcessor

logger = logging.getLogger(__name__)

class BettingModelTrainer:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.models = {}
        self.scalers = {}
        self.performance_metrics = {}
        self.feature_columns = ['home_goals', 'away_goals', 'home_shots', 'away_shots',
                               'home_possession', 'away_possession']

    def train_models(self, training_data):
        """Train multiple models for different bet types"""
        
        logger.info("Starting model training...")
        
        try:
            df = self.data_processor.prepare_training_data(training_data)
            
            # Remove rows with NaN values
            df = df.dropna(subset=['home_goals', 'away_goals', 'home_shots', 'away_shots', 'home_possession', 'away_possession'])
            
            # Remove outliers (matches with extremely high/low values)
            df = df[df['home_goals'] <= 10]
            df = df[df['away_goals'] <= 10]
            df = df[df['home_possession'] >= 0]
            df = df[df['away_possession'] >= 0]
            
            if len(df) < 100:
                logger.error(f"Not enough training data: {len(df)} samples (need at least 100)")
                raise ValueError(f"Insufficient training data: {len(df)} samples")
            
            logger.info(f"Using {len(df)} training samples (after cleanup)")
            
            # Create targets
            targets = self.data_processor.create_training_targets(df)
            
            # Prepare features
            X = df[self.feature_columns].fillna(0).astype(float)
            
            # Check for any NaN values after fillna
            if X.isnull().any().any():
                logger.warning("NaN values found in features, replacing with 0")
                X = X.fillna(0)
            
            # Normalize features
            X_normalized = self.data_processor.normalize_features(X)
            
            logger.info(f"Feature matrix shape: {X_normalized.shape}")
            
            # Train model for each bet type
            for bet_type, y in targets.items():
                logger.info(f"Training model for {bet_type}...")
                
                # Verify target values
                unique_labels = y.unique()
                logger.info(f"  Target distribution: {dict(y.value_counts())}")
                
                if len(unique_labels) < 2:
                    logger.warning(f"  Skipping {bet_type}: only one class present")
                    continue
                
                # Verify labels are 0 and 1
                if not all(label in [0, 1] for label in unique_labels):
                    logger.error(f"  Invalid labels in {bet_type}: {unique_labels}")
                    raise ValueError(f"Invalid labels in {bet_type}: {unique_labels}")
                
                # Split data with stratification
                X_train, X_test, y_train, y_test = train_test_split(
                    X_normalized, y, test_size=0.2, random_state=42, stratify=y
                )
                
                # Convert to DataFrame with feature names
                X_train_df = pd.DataFrame(X_train, columns=self.feature_columns)
                X_test_df = pd.DataFrame(X_test, columns=self.feature_columns)
                
                # Use RandomForestClassifier with better hyperparameters for calibration
                model = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                    class_weight='balanced'  # Handle class imbalance
                )
                model.fit(X_train_df, y_train)
                
                # Make predictions
                y_pred = model.predict(X_test_df)
                y_pred_proba = model.predict_proba(X_test_df)
                
                # Verify predictions are 0 or 1
                if not all(p in [0, 1] for p in y_pred):
                    logger.error(f"  Invalid predictions in {bet_type}: {np.unique(y_pred)}")
                    raise ValueError(f"Model produced invalid predictions: {np.unique(y_pred)}")
                
                # Evaluate with safe metrics
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, zero_division=0, labels=[0, 1], average='weighted')
                recall = recall_score(y_test, y_pred, zero_division=0, labels=[0, 1], average='weighted')
                f1 = f1_score(y_test, y_pred, zero_division=0, labels=[0, 1], average='weighted')
                
                self.models[bet_type] = model
                self.performance_metrics[bet_type] = {
                    'accuracy': float(accuracy),
                    'precision': float(precision),
                    'recall': float(recall),
                    'f1_score': float(f1),
                    'test_size': len(y_test),
                    'train_size': len(y_train),
                    'model_type': 'RandomForest'
                }
                
                logger.info(f"  [OK] Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
            
            if not self.models:
                logger.error("No models were trained successfully")
                raise ValueError("Model training failed: no valid models trained")
            
            # Save models
            self.save_models()
            logger.info(f"[OK] Model training completed! Trained {len(self.models)} models")
            
            return self.performance_metrics
            
        except Exception as e:
            logger.error(f"Error during model training: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def save_models(self):
        """Save trained models"""
        try:
            model_dir = Path(MODEL_PATH).parent
            model_dir.mkdir(parents=True, exist_ok=True)
            
            joblib.dump({
                'models': self.models,
                'performance': self.performance_metrics,
                'feature_columns': self.feature_columns,
                'timestamp': datetime.now().isoformat()
            }, str(MODEL_PATH))
            logger.info(f"[OK] Models saved to {MODEL_PATH}")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            raise

    def load_models(self):
        """Load trained models"""
        try:
            model_path = Path(MODEL_PATH)
            
            if not model_path.exists():
                logger.warning(f"Model file not found: {MODEL_PATH}")
                return False
            
            data = joblib.load(str(model_path))
            self.models = data['models']
            self.performance_metrics = data['performance']
            self.feature_columns = data.get('feature_columns', self.feature_columns)
            logger.info(f"[OK] Models loaded successfully ({len(self.models)} models)")
            return True
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def predict(self, features, bet_type):
        """Make prediction for a specific bet type"""
        if bet_type not in self.models:
            logger.warning(f"No model found for {bet_type}")
            return None
        
        try:
            model = self.models[bet_type]
            
            # Ensure features is a DataFrame with proper column names
            if not isinstance(features, pd.DataFrame):
                features = pd.DataFrame(features, columns=self.feature_columns)
            
            prediction_proba = model.predict_proba(features)
            
            # Ensure we have probabilities for both classes
            if prediction_proba.shape[1] == 2:
                return {
                    'confidence_class_0': float(prediction_proba[0][0]),
                    'confidence_class_1': float(prediction_proba[0][1])
                }
            else:
                logger.warning(f"Unexpected prediction shape for {bet_type}")
                return None
        except Exception as e:
            logger.error(f"Error making prediction for {bet_type}: {e}")
            return None