# Mistral OCR Test Suite

Eine umfassende Web-Anwendung zum Testen von Mistral-OCR Modellen über verschiedene Cloud-Provider (Azure OpenAI und Google Cloud Platform) mit detaillierter Token-Analyse und Performance-Monitoring.

## 🎯 Features

### 🔧 Konfiguration
- **Multi-Provider Support**: Azure OpenAI Mistral und GCP Mistral-OCR
- **GUI-Konfiguration**: Einfache Konfiguration über Web-Interface
- **Session-Management**: Sichere Speicherung der Konfiguration

### 📊 Test-Szenarien
- **Kleine Dateien**: 1-3 Seiten, gemischter Inhalt
- **Mittlere Dateien**: 5-10 Seiten, textlastig
- **Große Dateien**: 20+ Seiten, bildlastig
- **Stress-Tests**: Parallele Verarbeitung mehrerer Dateien
- **Automatische Test-Datei-Generierung**: PDF-Dateien mit verschiedenen Inhaltstypen

### 📈 Umfassende Metriken
- **Token-Verbrauch**: Input/Output/Total Tokens
- **Performance-Metriken**: Response-Zeiten, Durchsatz
- **Fehleranalyse**: Detaillierte Fehlerberichte pro Seite
- **Live-Monitoring**: Echtzeit-Updates über WebSocket
- **Statistische Auswertungen**: Grafische Darstellung der Ergebnisse

### 🔄 Asynchrone Verarbeitung
- **Background-Jobs**: Celery für asynchrone OCR-Verarbeitung
- **Fortschritts-Tracking**: Live-Updates über WebSocket
- **Fehlerbehandlung**: Robuste Fehlerbehandlung mit Retry-Mechanismen

## 🏗️ Architektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask App     │    │   Celery        │
│   (Bootstrap)   │◄──►│   (WebSocket)   │◄──►│   (Worker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │   OCR Provider  │
                       │   (Session/     │    │   (Azure/GCP)   │
                       │    Cache)       │    └─────────────────┘
                       └─────────────────┘
```

## 🚀 Installation

### Voraussetzungen
- Python 3.8+
- Redis Server
- Azure OpenAI Account oder GCP Account

### 1. Repository klonen
```bash
git clone <repository-url>
cd mistral-ocr-test
```

### 2. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 3. Redis installieren und starten

**Windows:**
```bash
# Redis für Windows herunterladen und installieren
# Oder Docker verwenden:
docker run -d -p 6379:6379 redis:alpine
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### 4. Umgebung konfigurieren
```bash
cp env_example.txt .env
# .env Datei mit Ihren Credentials bearbeiten
```

### 5. Anwendung starten
```bash
python start.py
```

Die Anwendung ist dann unter `http://localhost:5000` erreichbar.

## ⚙️ Konfiguration

### Azure OpenAI Mistral
1. Azure OpenAI Resource erstellen
2. Mistral-Modell deployen
3. API Key und Endpoint in der GUI konfigurieren

### Google Cloud Platform
1. GCP Project erstellen
2. Vertex AI API aktivieren
3. Service Account erstellen und JSON-Datei herunterladen
4. Mistral-OCR Endpoint erstellen
5. Credentials in der GUI konfigurieren

## 📖 Verwendung

### 1. Konfiguration
1. Öffnen Sie die Web-Anwendung
2. Konfigurieren Sie Azure und/oder GCP Provider
3. Speichern Sie die Konfiguration

### 2. Test-Dateien generieren
1. Wählen Sie gewünschte Test-Szenarien aus
2. Klicken Sie auf "Test-Dateien generieren"
3. Warten Sie auf die Generierung

### 3. OCR-Tests durchführen
1. **Einzelne Datei**: Datei per Drag & Drop oder Upload hochladen
2. **Batch-Test**: Mehrere Dateien parallel verarbeiten
3. **Live-Monitoring**: Verfolgen Sie den Fortschritt in Echtzeit

### 4. Ergebnisse analysieren
- **Live-Metriken**: Token-Verbrauch, Response-Zeiten, Erfolgsrate
- **Detaillierte Statistiken**: Umfassende Auswertung nach Test-Abschluss
- **Fehleranalyse**: Detaillierte Fehlerberichte für fehlgeschlagene Seiten

## 🔍 Token-Limit-Analyse

Die Anwendung ist speziell darauf ausgelegt, Token-Limits und deren Auswirkungen zu analysieren:

### Test-Strategien
- **Progressive Tests**: Von kleinen zu großen Dateien
- **Parallele Verarbeitung**: Mehrere Dateien gleichzeitig
- **Rate-Limit-Tests**: Schnelle aufeinanderfolgende Requests
- **Memory-Pressure-Tests**: Sehr große Dateien

### Metriken
- **Token-Verbrauch pro Seite**: Identifikation von Token-Spikes
- **Response-Zeit-Korrelation**: Zusammenhang zwischen Token-Verbrauch und Performance
- **Fehler-Patterns**: Analyse von Token-Limit-Fehlern
- **Memory-Usage**: Überwachung des Speicherverbrauchs

## 📊 Beispiel-Test-Szenarien

### Szenario 1: Token-Limit-Test
```json
{
  "name": "Token Limit Test",
  "files": [
    {"pages": 1, "content_type": "text_heavy"},
    {"pages": 5, "content_type": "text_heavy"},
    {"pages": 10, "content_type": "text_heavy"},
    {"pages": 20, "content_type": "text_heavy"}
  ],
  "parallel_processing": true
}
```

### Szenario 2: Rate-Limit-Test
```json
{
  "name": "Rate Limit Test",
  "files": [
    {"pages": 3, "content_type": "mixed"}
  ],
  "parallel_processing": true,
  "concurrent_requests": 5
}
```

## 🐛 Fehlerbehandlung

### Häufige Fehler
1. **Token-Limit-Fehler**: Automatische Erkennung und Reporting
2. **Rate-Limit-Fehler**: Retry-Mechanismus mit exponentieller Backoff
3. **Netzwerk-Fehler**: Automatische Wiederholung
4. **Provider-spezifische Fehler**: Detaillierte Fehleranalyse

### Debugging
- **Live-Logs**: Echtzeit-Logging über WebSocket
- **Fehler-Modal**: Detaillierte Fehleranzeige in der GUI
- **Task-Status**: Verfolgung des Task-Status und Fortschritts

## 🔧 Entwicklung

### Projektstruktur
```
mistral-ocr-test/
├── app.py                 # Flask-Hauptanwendung
├── tasks.py              # Celery-Tasks und OCR-Provider
├── templates/
│   └── index.html        # Frontend-Template
├── static/               # Statische Dateien
├── uploads/              # Hochgeladene Dateien
├── test_files/           # Generierte Test-Dateien
├── results/              # Verarbeitungsergebnisse
├── requirements.txt      # Python-Dependencies
├── start.py             # Startup-Script
└── README.md            # Diese Datei
```

### Erweiterte Features
- **Custom Test-Szenarien**: Eigene Test-Konfigurationen
- **Export-Funktionen**: Export von Statistiken als CSV/JSON
- **API-Endpoints**: REST-API für externe Integration
- **Docker-Support**: Containerisierung der Anwendung

## 🤝 Beitragen

1. Fork des Repositories
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

## 🆘 Support

Bei Fragen oder Problemen:
1. Issues im GitHub Repository erstellen
2. Dokumentation durchsuchen
3. Debug-Logs analysieren

## 🔮 Roadmap

- [ ] Docker-Containerisierung
- [ ] Erweiterte Metriken (Memory, CPU)
- [ ] Export-Funktionen
- [ ] API-Dokumentation
- [ ] Unit-Tests
- [ ] CI/CD-Pipeline
- [ ] Multi-Language Support
- [ ] Advanced Analytics Dashboard
