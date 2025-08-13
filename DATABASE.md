# Datenbank - Mistral OCR Test Suite

## 🗄️ **SQLite Datenbank-Integration**

Die Anwendung verwendet jetzt eine lokale SQLite-Datenbank (`mistral_ocr_test.db`) für die persistente Speicherung aller Daten. Dies bietet mehrere Vorteile gegenüber der In-Memory-Speicherung.

## 📊 **Datenbank-Struktur**

### **1. Konfigurationen-Tabelle (`configurations`)**
```sql
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,           -- 'azure' oder 'gcp'
    config_data TEXT NOT NULL,        -- JSON-Konfiguration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Zweck**: Speichert die Provider-Konfigurationen (API Keys, Endpoints, etc.)

### **2. Test-Historie-Tabelle (`test_history`)**
```sql
CREATE TABLE test_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,     -- Eindeutige Task-ID
    filename TEXT NOT NULL,           -- Name der verarbeiteten Datei
    providers TEXT NOT NULL,          -- JSON-Array der verwendeten Provider
    results TEXT NOT NULL,            -- JSON-Ergebnisse der OCR-Verarbeitung
    statistics TEXT NOT NULL,         -- JSON-Statistiken pro Provider
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Zweck**: Vollständige Historie aller durchgeführten Tests

### **3. Task-Store-Tabelle (`task_store`)**
```sql
CREATE TABLE task_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,     -- Eindeutige Task-ID
    status TEXT NOT NULL,             -- 'running', 'completed', 'failed'
    progress INTEGER DEFAULT 0,       -- Fortschritt in Prozent
    filename TEXT,                    -- Name der Datei
    test_config TEXT,                 -- JSON-Test-Konfiguration
    providers TEXT,                   -- JSON-Array der Provider
    config_data TEXT,                 -- JSON-Konfiguration zum Zeitpunkt des Tests
    result_data TEXT,                 -- JSON-Ergebnisse
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Zweck**: Verwaltung laufender und abgeschlossener Tasks

### **4. Statistiken-Tabelle (`statistics`)**
```sql
CREATE TABLE statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,           -- 'azure' oder 'gcp'
    total_pages INTEGER DEFAULT 0,    -- Gesamtanzahl verarbeiteter Seiten
    successful_pages INTEGER DEFAULT 0, -- Erfolgreich verarbeitete Seiten
    failed_pages INTEGER DEFAULT 0,   -- Fehlgeschlagene Seiten
    success_rate REAL DEFAULT 0.0,    -- Erfolgsrate in Prozent
    total_response_time REAL DEFAULT 0.0, -- Gesamte Response-Zeit
    average_response_time REAL DEFAULT 0.0, -- Durchschnittliche Response-Zeit
    min_response_time REAL DEFAULT 0.0,     -- Minimale Response-Zeit
    max_response_time REAL DEFAULT 0.0,     -- Maximale Response-Zeit
    total_tokens INTEGER DEFAULT 0,   -- Gesamte Token-Anzahl
    input_tokens INTEGER DEFAULT 0,   -- Input-Token-Anzahl
    output_tokens INTEGER DEFAULT 0,  -- Output-Token-Anzahl
    average_tokens_per_page REAL DEFAULT 0.0, -- Durchschnittliche Token pro Seite
    total_errors INTEGER DEFAULT 0,   -- Gesamtanzahl Fehler
    error_details TEXT,               -- JSON-Details zu Fehlern
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Zweck**: Aggregierte Statistiken pro Provider

## 🔧 **Datenbank-Funktionen**

### **Konfiguration verwalten**
```python
# Konfiguration laden
config = load_config()

# Konfiguration speichern
save_config(config_data)
```

### **Tasks verwalten**
```python
# Task speichern
save_task(task_id, status, progress, filename, config_data)

# Task abrufen
task = get_task(task_id)
```

### **Test-Historie verwalten**
```python
# Test zur Historie hinzufügen
save_test_history(task_id, filename, providers, results, statistics)

# Alle Tests abrufen
tests = get_test_history()

# Spezifischen Test abrufen
test = get_test_by_id(task_id)
```

### **Statistiken verwalten**
```python
# Statistiken aktualisieren
update_statistics(provider, stats)

# Alle Statistiken abrufen
statistics = get_statistics()
```

## 📈 **Vorteile der Datenbank-Integration**

### **1. Persistierung**
- **Konfigurationen**: Bleiben auch nach Neustart erhalten
- **Test-Historie**: Vollständige Übersicht aller Tests
- **Statistiken**: Langzeit-Trends und Vergleiche möglich

### **2. Datenintegrität**
- **ACID-Eigenschaften**: Atomarität, Konsistenz, Isolation, Dauerhaftigkeit
- **Referentielle Integrität**: Zusammenhängende Daten bleiben konsistent
- **Transaktionen**: Sichere Datenbankoperationen

### **3. Performance**
- **Indizierung**: Schnelle Abfragen auch bei vielen Datensätzen
- **Strukturierte Abfragen**: Effiziente Datenbankoperationen
- **Skalierbarkeit**: Gute Performance auch bei wachsenden Datenmengen

### **4. Analyse-Möglichkeiten**
- **Langzeit-Trends**: Entwicklung der Performance über Zeit
- **Provider-Vergleiche**: Detaillierte Vergleiche zwischen Azure und GCP
- **Token-Analyse**: Umfassende Token-Verbrauch-Analysen

## 🛠️ **Datenbank-Verwaltung**

### **Datenbank initialisieren**
```python
# Automatisch beim Start der Anwendung
init_database()
```

### **Datenbank-Verbindung**
```python
# Verbindung herstellen
conn = get_db_connection()

# Nach Verwendung schließen
conn.close()
```

### **Backup erstellen**
```bash
# Datenbank sichern
cp mistral_ocr_test.db mistral_ocr_test_backup.db

# Datenbank wiederherstellen
cp mistral_ocr_test_backup.db mistral_ocr_test.db
```

## 📊 **Datenbank-Abfragen**

### **Alle Tests eines Providers**
```sql
SELECT * FROM test_history 
WHERE providers LIKE '%azure%' 
ORDER BY created_at DESC;
```

### **Statistiken eines Providers**
```sql
SELECT * FROM statistics 
WHERE provider = 'azure';
```

### **Fehler-Analyse**
```sql
SELECT provider, total_errors, error_details 
FROM statistics 
WHERE total_errors > 0;
```

### **Performance-Vergleich**
```sql
SELECT provider, average_response_time, success_rate 
FROM statistics 
ORDER BY average_response_time;
```

## 🔒 **Sicherheit**

### **Datenbank-Schutz**
- **Datei-Berechtigungen**: Nur für autorisierte Benutzer zugänglich
- **Backup-Strategie**: Regelmäßige Sicherungen
- **Verschlüsselung**: Optional SQLite-Verschlüsselung möglich

### **Sensible Daten**
- **API Keys**: Werden in der Datenbank gespeichert
- **Service Accounts**: Vollständige JSON-Daten in der Datenbank
- **Gitignore**: Datenbank-Datei ist von Git ausgeschlossen

## 🚀 **Migration von In-Memory zu Datenbank**

### **Automatische Migration**
- Die Anwendung erstellt die Datenbank automatisch beim ersten Start
- Bestehende Konfigurationen werden in die Datenbank migriert
- Keine manuellen Schritte erforderlich

### **Daten-Konsistenz**
- Alle Daten werden in der Datenbank gespeichert
- In-Memory-Daten werden nicht mehr verwendet
- Vollständige Persistierung aller Informationen

## 📋 **Monitoring und Wartung**

### **Datenbank-Größe**
```bash
# Größe der Datenbank prüfen
ls -lh mistral_ocr_test.db
```

### **Datenbank-Integrität**
```bash
# SQLite-Integritätsprüfung
sqlite3 mistral_ocr_test.db "PRAGMA integrity_check;"
```

### **Tabellen-Übersicht**
```bash
# Alle Tabellen anzeigen
sqlite3 mistral_ocr_test.db ".tables"

# Tabellen-Struktur anzeigen
sqlite3 mistral_ocr_test.db ".schema"
```

---

**Hinweis**: Die SQLite-Datenbank bietet eine robuste, skalierbare Lösung für die Datenpersistierung. Alle Daten bleiben auch nach Neustarts der Anwendung erhalten! 🎯
