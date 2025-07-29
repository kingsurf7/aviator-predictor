from flask import Flask, render_template, jsonify
from predictor import AviatorPredictor
import threading
import time

app = Flask(__name__)
predictor = AviatorPredictor()

# Démarrer le thread de mise à jour en arrière-plan
update_thread = threading.Thread(target=predictor.start_realtime_updates)
update_thread.daemon = True
update_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/prediction')
def get_prediction():
    current, prediction, confidence = predictor.get_current_prediction()
    return jsonify({
        'current': current,
        'prediction': prediction,
        'confidence': confidence,
        'timestamp': time.time()
    })

@app.route('/api/history')
def get_history():
    return jsonify(predictor.get_history())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
