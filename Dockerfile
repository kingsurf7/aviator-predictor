# Utiliser une image Python officielle
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
COPY app.py .
COPY predictor.py .
COPY models/ ./models/
COPY static/ ./static/
COPY templates/ ./templates/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port 8080
EXPOSE 8080

# Commande pour lancer l'application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]
