import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import RobustScaler
import requests
import time
from threading import Lock
from collections import deque
import talib
from scipy import stats
import json
import os

class AviatorPredictor:
    def __init__(self):
        self.model = load_model('app/models/aviator_model.h5')
        self.scaler = RobustScaler()
        self.history = []
        self.prediction_history = deque(maxlen=20)
        self.error_history = deque(maxlen=20)
        self.volatility_history = deque(maxlen=50)
        self.current_prediction = None
        self.lock = Lock()
        self.trend = "neutral"
        self.settings = {
            'alert_threshold': 2.0,
            'confidence_threshold': 0.7
        }
        self.load_initial_data()
        self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    self.settings = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_settings(self, alert_threshold=None, confidence_threshold=None):
        try:
            if alert_threshold is not None:
                self.settings['alert_threshold'] = float(alert_threshold)
            if confidence_threshold is not None:
                self.settings['confidence_threshold'] = float(confidence_threshold)
            self.save_settings()
            return True
        except:
            return False

    def load_initial_data(self):
        try:
            response = requests.get('https://aviatorengine.1win.com/api/history', timeout=10)
            data = response.json()
            self.history = [x['multiplier'] for x in data]
            if len(self.history) > 30:
                self.scaler.fit(np.array(self.history).reshape(-1, 1))
        except Exception as e:
            print(f"Error loading initial data: {e}")
            self.history = [1.0] * 30

    def start_realtime_updates(self):
        while True:
            try:
                self.update_prediction()
                time.sleep(5)
            except Exception as e:
                print(f"Update error: {e}")
                time.sleep(10)

    def calculate_confidence(self):
        if len(self.error_history) < 3 or len(self.prediction_history) < 3:
            return 0.5
            
        recent_errors = list(self.error_history)[-3:]
        accuracy = 1 - np.mean(recent_errors)
        
        consistency = 1 / (1 + np.std(list(self.prediction_history)[-5:]))
        volatility = 1 / (1 + (np.mean(list(self.volatility_history)[-5:]) if self.volatility_history else 1))
        trend_strength = 0.8 if self.trend != "neutral" else 0.5
        
        confidence = 0.5*accuracy + 0.3*consistency + 0.1*volatility + 0.1*trend_strength
        return np.clip(confidence, 0.1, 0.95)

    def detect_trend(self, data):
        if len(data) < 10:
            return "neutral"
            
        prices = np.array(data)
        x = np.arange(len(data))
        slope, _, _, _, _ = stats.linregress(x, prices)
        macd = talib.MACD(prices)[2][-1]
        sma = talib.SMA(prices, timeperiod=5)[-1]
        
        if slope > 0.05 and macd > 0 and prices[-1] > sma:
            return "up"
        elif slope < -0.05 and macd < 0 and prices[-1] < sma:
            return "down"
        return "neutral"

    def update_volatility(self):
        if len(self.history) >= 10:
            recent = self.history[-10:]
            returns = np.diff(recent) / recent[:-1]
            self.volatility_history.append(np.std(returns))

    def update_prediction(self):
        try:
            response = requests.get('https://aviatorengine.1win.com/api/current', timeout=5)
            current = response.json()['multiplier']
            
            with self.lock:
                self.history.append(current)
                if len(self.history) > 500:
                    self.history = self.history[-500:]
                
                self.update_volatility()
                self.trend = self.detect_trend(self.history[-30:])
                
                if len(self.history) >= 30:
                    sequence = np.array(self.history[-30:]).reshape(1, 30, 1)
                    normalized = self.scaler.transform(sequence.reshape(-1, 1))
                    prediction_norm = self.model.predict(normalized.reshape(1, 30, 1))
                    prediction = self.scaler.inverse_transform(prediction_norm)[0][0]
                    
                    if self.current_prediction:
                        error = abs(self.current_prediction['prediction'] - current) / current
                        self.error_history.append(error)
                    
                    self.prediction_history.append(prediction)
                    
                    self.current_prediction = {
                        'current': current,
                        'prediction': prediction,
                        'confidence': self.calculate_confidence(),
                        'trend': self.trend,
                        'volatility': np.mean(list(self.volatility_history)[-3:]) if self.volatility_history else 1.0
                    }
        except Exception as e:
            print(f"Prediction update failed: {e}")

    def get_current_prediction(self):
        with self.lock:
            if self.current_prediction:
                return (
                    self.current_prediction['current'],
                    self.current_prediction['prediction'],
                    self.current_prediction['confidence'],
                    self.current_prediction['trend'],
                    self.current_prediction['volatility']
                )
            return None

    def get_history(self):
        with self.lock:
            return self.history[-100:]

    def get_performance_metrics(self):
        with self.lock:
            if not self.error_history:
                return {}
            
            recent_errors = list(self.error_history)[-5:] or [0]
            recent_preds = list(self.prediction_history)[-5:] or [1]
            
            return {
                'avg_error': float(np.mean(recent_errors)),
                'last_error': float(recent_errors[-1]),
                'stability': float(1 - np.std(recent_preds)/np.mean(recent_preds)),
                'success_rate': float(sum(e < 0.1 for e in recent_errors)/len(recent_errors)),
                'settings': self.settings
            }
