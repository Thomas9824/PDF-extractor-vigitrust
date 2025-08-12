FROM python:3.11-slim

WORKDIR /app

# Copier les requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY testv5.py .
COPY api/extract.py .

# Exposer le port 8000
EXPOSE 8000

# Commande par défaut
CMD ["python", "extract.py"]