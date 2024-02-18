# Verwenden Sie ein offizielles Python-Runtime-Image als Basis
FROM python:3-slim

# Setzen Sie das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopieren Sie die Abhängigkeiten und installieren Sie diese
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kopieren Sie den Rest des Anwendungs-Codes
COPY main.py .

# Starten Sie die Anwendung
CMD ["python", "./main.py"]
