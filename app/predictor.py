import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import RobustScaler
import requests
import time
import json
from threading import Lock

class AviatorPredictor:
    def __init__(self):
        self.model = load_model('models/aviator_model.h5')
        self.scaler = RobustScaler()
        self.history = []
        self.current_prediction = None
        self.lock = Lock()
        self.load_initial_data()

    def load_initial_data(self):
        # Charger les données initiales depuis l'API
        try:
            response = requests.get('https://aviatorengine.1win.com/api/history', timeout=10)
            data = response.json()
            self.history = [x['multiplier'] for x in data]
            self.scaler.fit(np.array(self.history).reshape(-1, 1))
        except Exception as e:
            print(f"Error loading initial data: {e}")
            self.history = [1.0] * 30  # Valeurs par défaut

    def start_realtime_updates(self):
        while True:
            try:
                self.update_prediction()
                time.sleep(5)  # Mettre à jour toutes les 5 secondes
            except Exception as e:
                print(f"Update error: {e}")
                time.sleep(10)

    def update_prediction(self):
        # Récupérer la dernière valeur
        try:
            response = requests.get('https://aviatorengine.1win.com/api/current', timeout=5)
            current = response.json()['multiplier']
            
            with self.lock:
                self.history.append(current)
                if len(self.history) > 500:
                    self.history = self.history[-500:]
                
                # Faire la prédiction
                if len(self.history) >= 30:
                    sequence = np.array(self.history[-30:]).reshape(1, 30, 1)
                    normalized = self.scaler.transform(sequence.reshape(-1, 1))
                    prediction_norm = self.model.predict(normalized.reshape(1, 30, 1))
                    prediction = self.scaler.inverse_transform(prediction_norm)[0][0]
                    confidence = self.calculate_confidence()
                    
                    self.current_prediction = {
                        'current': current,
                        'prediction': prediction,
                        'confidence': confidence
                    }
        except Exception as e:
            print(f"Prediction update failed: {e}")

    def calculate_confidence(self):
        # Implémentez votre logique de confiance ici
        return 0.8  # Exemple

    def get_current_prediction(self):
        with self.lock:
            if self.current_prediction:
                return (
                    self.current_prediction['current'],
                    self.current_prediction['prediction'],
                    self.current_prediction['confidence']
                )
            return None, None, None

    def get_history(self):
        with self.lock:
            return self.history[-50:]  # Retourne les 50 dernières valeurs
