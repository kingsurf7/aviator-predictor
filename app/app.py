from flask import Flask, render_template, jsonify, request
from predictor import AviatorPredictor
import threading
import time
from datetime import datetime
import json

app = Flask(__name__)
predictor = AviatorPredictor()

# Démarrer le thread de mise à jour
update_thread = threading.Thread(target=predictor.start_realtime_updates)
update_thread.daemon = True
update_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/prediction')
def get_prediction():
    prediction_data = predictor.get_current_prediction()
    if prediction_data:
        current, prediction, confidence, trend, volatility = prediction_data
        return jsonify({
            'current': current,
            'prediction': prediction,
            'confidence': confidence,
            'trend': trend,
            'volatility': volatility,
            'timestamp': datetime.now().timestamp()
        })
    return jsonify({'error': 'Initializing...'}), 503

@app.route('/api/history')
def get_history():
    return jsonify(predictor.get_history())

@app.route('/api/analytics')
def get_analytics():
    return jsonify(predictor.get_performance_metrics())

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.json
    success = predictor.update_settings(
        alert_threshold=data.get('alert_threshold'),
        confidence_threshold=data.get('confidence_threshold')
    )
    return jsonify({'success': success})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
