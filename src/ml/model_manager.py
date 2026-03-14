import os
import pickle
from datetime import datetime

class ModelManager:
    def __init__(self, model_name):
        self.model_name = model_name
        self.model_dir = f'./models/{model_name}'
        os.makedirs(self.model_dir, exist_ok=True)

    def save_model(self, model, version):
        versioned_model_path = os.path.join(self.model_dir, f'model_v{version}.pkl')
        metadata_path = os.path.join(self.model_dir, f'metadata.json')

        # Save the model
        with open(versioned_model_path, 'wb') as model_file:
            pickle.dump(model, model_file)

        # Save metadata
        metadata = {
            'version': version,
            'saved_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'model_name': self.model_name
        }
        with open(metadata_path, 'w') as meta_file:
            json.dump(metadata, meta_file)

    def load_model(self, version):
        model_path = os.path.join(self.model_dir, f'model_v{version}.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as model_file:
                return pickle.load(model_file)
        else:
            raise FileNotFoundError(f'Model version {version} not found.')

    def get_metadata(self):
        metadata_path = os.path.join(self.model_dir, 'metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as meta_file:
                return json.load(meta_file)
        else:
            raise FileNotFoundError('Metadata file not found.')
