import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import RobustScaler
import requests
import time
import json
from threading import Lock
from collections import deque
import talib
from scipy import stats

class AviatorPredictor:
    def __init__(self):
        self.model = load_model('models/aviator_model.h5')
        self.scaler = RobustScaler()
        self.history = []
        self.prediction_history = deque(maxlen=20)  # Stocke les dernières prédictions
        self.error_history = deque(maxlen=20)       # Stocke les erreurs récentes
        self.volatility_history = deque(maxlen=50)  # Mesure la volatilité
        self.current_prediction = None
        self.lock = Lock()
        self.trend = "neutral"
        self.load_initial_data()

    def calculate_confidence(self):
        """Calcule un score de confiance composite"""
        if len(self.error_history) < 5 or len(self.prediction_history) < 5:
            return 0.5  # Valeur par défaut si pas assez de données
        
        # 1. Exactitude récente (40% du score)
        recent_errors = list(self.error_history)[-5:]
        accuracy_component = 1 - (np.mean(recent_errors) / 2)  # Normalisé à 0-1
        
        # 2. Cohérence des prédictions (30%)
        prediction_std = np.std(list(self.prediction_history)[-5:])
        consistency_component = 1 / (1 + prediction_std)
        
        # 3. Volatilité du marché (20%)
        volatility = np.mean(list(self.volatility_history)[-10:]) if self.volatility_history else 1.0
        volatility_component = 1 / (1 + volatility)
        
        # 4. Force de la tendance (10%)
        trend_component = 0.8 if self.trend != "neutral" else 0.5
        
        # Combinaison pondérée
        confidence = (
            0.4 * accuracy_component +
            0.3 * consistency_component +
            0.2 * volatility_component +
            0.1 * trend_component
        )
        
        # Ajustement final
        return np.clip(confidence, 0.1, 0.95)

    def detect_trend(self, data):
        """Détecte la tendance avec plusieurs indicateurs"""
        if len(data) < 10:
            return "neutral"
            
        prices = np.array(data)
        
        # 1. Régression linéaire
        x = np.arange(len(data))
        slope, _, _, _, _ = stats.linregress(x, prices)
        
        # 2. MACD
        macd = talib.MACD(prices)[2][-1]  # Histogramme MACD
        
        # 3. Moyenne mobile
        sma = talib.SMA(prices, timeperiod=5)[-1]
        
        # Décision composite
        if slope > 0.05 and macd > 0 and prices[-1] > sma:
            return "up"
        elif slope < -0.05 and macd < 0 and prices[-1] < sma:
            return "down"
        else:
            return "neutral"

    def update_volatility(self):
        """Calcule la volatilité récente"""
        if len(self.history) >= 10:
            recent = self.history[-10:]
            returns = np.diff(recent) / recent[:-1]
            self.volatility_history.append(np.std(returns))

    def update_prediction(self):
        try:
            response = requests.get('https://aviatorengine.1win.com/api/current', timeout=5)
            current = response.json()['multiplier']
            
            with self.lock:
                # Mise à jour de l'historique
                self.history.append(current)
                if len(self.history) > 500:
                    self.history = self.history[-500:]
                
                # Calculs techniques
                self.update_volatility()
                self.trend = self.detect_trend(self.history[-30:])
                
                # Prédiction
                if len(self.history) >= 30:
                    sequence = np.array(self.history[-30:]).reshape(1, 30, 1)
                    normalized = self.scaler.transform(sequence.reshape(-1, 1))
                    prediction_norm = self.model.predict(normalized.reshape(1, 30, 1))
                    prediction = self.scaler.inverse_transform(prediction_norm)[0][0]
                    
                    # Mise à jour des historiques
                    if self.current_prediction:
                        last_pred = self.current_prediction['prediction']
                        error = abs(last_pred - current) / current
                        self.error_history.append(error)
                    
                    self.prediction_history.append(prediction)
                    
                    # Calcul de la confiance
                    confidence = self.calculate_confidence()
                    
                    self.current_prediction = {
                        'current': current,
                        'prediction': prediction,
                        'confidence': confidence,
                        'trend': self.trend,
                        'volatility': np.mean(list(self.volatility_history)[-5:]) if self.volatility_history else 1.0,
                        'timestamp': time.time()
                    }
        except Exception as e:
            print(f"Prediction update failed: {e}")
