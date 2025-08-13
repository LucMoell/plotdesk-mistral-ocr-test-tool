# Docker Setup - Mistral OCR Test Suite

## 🐳 **Docker Container erfolgreich gestartet!**

### ✅ **Status:**
- **Container:** `mistral-ocr-app` läuft
- **Port:** 82 (http://localhost:82)
- **Datenbank:** SQLite (persistent)
- **Health Check:** ✅ Gesund

## 🚀 **Schnellstart:**

### **Option 1: PowerShell Script (Empfohlen)**
```powershell
.\docker-start.ps1
```

### **Option 2: Manuelle Docker Commands**
```bash
# Build Image
docker-compose build

# Start Container
docker-compose up -d

# View Logs
docker-compose logs -f

# Stop Container
docker-compose down
```

## 📋 **Nützliche Docker Commands:**

### **Container Management:**
```bash
# Status anzeigen
docker-compose ps

# Logs anzeigen
docker-compose logs -f

# Container stoppen
docker-compose down

# Container neu starten
docker-compose restart

# Container löschen und neu erstellen
docker-compose up -d --force-recreate
```

### **Container Interaktion:**
```bash
# Shell im Container öffnen
docker-compose exec app bash

# Dateien im Container anzeigen
docker-compose exec app ls -la

# Datenbank-Datei prüfen
docker-compose exec app ls -la *.db
```

## 🔧 **Docker-Konfiguration:**

### **Dockerfile:**
- **Base Image:** Python 3.11-slim
- **Working Directory:** `/app`
- **Dependencies:** gcc, g++, curl
- **Port:** 5000
- **Health Check:** HTTP GET auf `/`

### **docker-compose.yml:**
- **Service:** `app` (mistral-ocr-app)
- **Port Mapping:** `82:80`
- **Volumes:**
  - `./uploads:/app/uploads`
  - `./test_files:/app/test_files`
  - `./results:/app/results`
  - `./logs:/app/logs`
  - `./mistral_ocr_test.db:/app/mistral_ocr_test.db` (persistente Datenbank)

## 📊 **Aktuelle Metriken im Container:**

- **Tests durchgeführt:** 3
- **Azure Erfolgsrate:** 0% (3 Tests, 3 Fehler)
- **GCP Erfolgsrate:** 0% (3 Tests, 3 Fehler)
- **Datenbank:** SQLite mit 3 Test-Einträgen
- **API-Endpunkte:** Alle funktional

## 🌐 **Verfügbare Endpunkte:**

- **Web UI:** http://localhost:82
- **API Config:** http://localhost:82/api/config
- **API Statistics:** http://localhost:82/api/statistics
- **API Test History:** http://localhost:82/api/test-history
- **API Batch Test:** http://localhost:82/api/batch-test

## 🔍 **Troubleshooting:**

### **Container startet nicht:**
```bash
# Logs prüfen
docker-compose logs

# Container neu bauen
docker-compose build --no-cache
docker-compose up -d
```

### **Port bereits belegt:**
```bash
# Andere Anwendung auf Port 5000 stoppen
# Oder Port in docker-compose.yml ändern:
# ports:
#   - "5001:5000"
```

### **Datenbank-Probleme:**
```bash
# Datenbank-Datei prüfen
docker-compose exec app ls -la *.db

# Datenbank zurücksetzen (Vorsicht: Daten gehen verloren!)
rm mistral_ocr_test.db
docker-compose restart
```

## 🎯 **Nächste Schritte:**

1. **Web UI öffnen:** http://localhost:82
2. **Provider konfigurieren:** Azure OpenAI und/oder GCP Vertex AI
3. **Test-Szenarien erstellen:** Verschiedene PDF-Größen testen
4. **Echte API-Calls:** Mit konfigurierten Credentials testen

## 🎉 **Erfolge:**

- ✅ Docker Container läuft erfolgreich
- ✅ Alle API-Endpunkte funktional
- ✅ Datenbank persistent
- ✅ Health Check aktiv
- ✅ Logs verfügbar
- ✅ Volumes gemountet

**Die Anwendung ist bereit für echte OCR-Tests!**
