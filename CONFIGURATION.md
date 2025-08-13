# Konfiguration - Mistral OCR Test Suite

## 🔧 **Konfiguration der Provider**

Die Anwendung speichert die Konfiguration automatisch in der Datei `config.json`. Diese wird beim ersten Speichern erstellt und bei jedem Neustart der Anwendung geladen.

## 📋 **Azure OpenAI Konfiguration**

### Benötigte Informationen:
- **API Key**: Ihr Azure OpenAI API-Schlüssel
- **Endpoint**: Die URL Ihres Azure OpenAI Ressource (z.B. `https://your-resource.openai.azure.com/`)
- **Deployment Name**: Name Ihres GPT-4 Vision Deployments
- **API Version**: API-Version (Standard: `2024-02-15-preview`)

### Schritte zur Einrichtung:
1. Gehen Sie zu [Azure Portal](https://portal.azure.com)
2. Erstellen Sie eine Azure OpenAI Ressource
3. Erstellen Sie ein GPT-4 Vision Deployment
4. Kopieren Sie den API Key und Endpoint
5. Tragen Sie die Daten in der Anwendung ein

### Beispiel-Konfiguration:
```json
{
  "azure": {
    "enabled": true,
    "api_key": "sk-1234567890abcdef...",
    "endpoint": "https://your-resource.openai.azure.com/",
    "deployment_name": "gpt-4-vision",
    "api_version": "2024-02-15-preview"
  }
}
```

## ☁️ **Google Cloud Platform Konfiguration**

### Benötigte Informationen:
- **Service Account JSON**: Vollständige Service Account JSON-Datei
- **Project ID**: Ihre GCP Projekt-ID
- **Location**: Region Ihres Endpoints (Standard: `us-central1`)
- **Endpoint ID**: ID Ihres Vertex AI Endpoints

### Schritte zur Einrichtung:
1. Gehen Sie zu [Google Cloud Console](https://console.cloud.google.com)
2. Erstellen Sie ein Service Account
3. Laden Sie die JSON-Schlüsseldatei herunter
4. Erstellen Sie einen Vertex AI Endpoint
5. Tragen Sie die Daten in der Anwendung ein

### Service Account erstellen:
1. **IAM & Admin** → **Service Accounts**
2. **Create Service Account**
3. **Keys** → **Add Key** → **Create new key** → **JSON**
4. JSON-Datei herunterladen und Inhalt kopieren

### Beispiel-Konfiguration:
```json
{
  "gcp": {
    "enabled": true,
    "service_account_json": "{\"type\":\"service_account\",\"project_id\":\"your-project\",...}",
    "project_id": "your-project-id",
    "location": "us-central1",
    "endpoint_id": "1234567890123456789"
  }
}
```

## 🚀 **Verwendung der Konfiguration**

### 1. Konfiguration speichern:
- Tragen Sie die Daten in der Web-Oberfläche ein
- Klicken Sie auf "Konfiguration speichern"
- Die Daten werden automatisch in `config.json` gespeichert

### 2. Konfiguration laden:
- Die Anwendung lädt die Konfiguration automatisch beim Start
- Bei jedem Neustart werden die gespeicherten Einstellungen verwendet

### 3. Konfiguration bearbeiten:
- Ändern Sie die Einstellungen in der Web-Oberfläche
- Klicken Sie erneut auf "Konfiguration speichern"
- Die Änderungen werden sofort übernommen

## 🔒 **Sicherheitshinweise**

### Wichtige Sicherheitsaspekte:
- **API Keys niemals teilen**: Teilen Sie Ihre API-Schlüssel nicht mit anderen
- **Service Account schützen**: Bewahren Sie die Service Account JSON sicher auf
- **Gitignore**: Die `config.json` ist bereits in `.gitignore` aufgeführt
- **Produktionsumgebung**: Verwenden Sie Umgebungsvariablen in der Produktion

### Empfohlene Sicherheitsmaßnahmen:
1. **Regelmäßige Rotation**: Rotieren Sie API-Schlüssel regelmäßig
2. **Minimale Berechtigungen**: Geben Sie Service Accounts nur notwendige Berechtigungen
3. **Monitoring**: Überwachen Sie API-Nutzung und Kosten
4. **Backup**: Sichern Sie die Konfiguration regelmäßig

## 🧪 **Testen der Konfiguration**

### Konfiguration testen:
1. **Provider aktivieren**: Aktivieren Sie mindestens einen Provider
2. **Test-Datei hochladen**: Laden Sie eine PDF-Datei hoch
3. **OCR-Ergebnisse prüfen**: Überprüfen Sie die extrahierten Texte
4. **Token-Verbrauch analysieren**: Studieren Sie die Token-Metriken

### Fehlerbehebung:
- **Azure-Fehler**: Prüfen Sie API Key, Endpoint und Deployment Name
- **GCP-Fehler**: Prüfen Sie Service Account JSON und Endpoint ID
- **Netzwerk-Fehler**: Prüfen Sie Internetverbindung und Firewall-Einstellungen

## 📊 **Monitoring und Kosten**

### Azure OpenAI Kosten:
- **Input Tokens**: Kosten für Bildverarbeitung
- **Output Tokens**: Kosten für generierten Text
- **Rate Limits**: Beachten Sie die API-Limits

### GCP Vertex AI Kosten:
- **Prediction Requests**: Kosten pro API-Aufruf
- **Model Serving**: Kosten für Endpoint-Betrieb
- **Quotas**: Beachten Sie die GCP-Quotas

## 🔄 **Konfiguration zurücksetzen**

### Konfiguration löschen:
1. Löschen Sie die Datei `config.json`
2. Starten Sie die Anwendung neu
3. Tragen Sie die Konfiguration erneut ein

### Backup erstellen:
```bash
# Konfiguration sichern
cp config.json config_backup.json

# Konfiguration wiederherstellen
cp config_backup.json config.json
```

---

**Hinweis**: Die Konfiguration wird automatisch gespeichert und bei jedem Neustart geladen. Sie müssen die Daten nur einmal eingeben! 🎯
