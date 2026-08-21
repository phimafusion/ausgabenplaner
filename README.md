# Ausgabenplaner 📊💰

Ein moderner, transparenter und modularer Ausgaben- und Wirtschaftsplaner zur Verwaltung von Hausgeldern, Kostenpositionen, Haushaltsbudgets und Beitragszahlungen mit integrierter **Plan-Verwaltung**, **Versionshistorie (Stände-Management)**, **Kategorien-Management & Live-Filter**, **Excel- & JSON-Export**, **Live-Matrix-Vergleich** und **Echtzeit-Testsuite**.

---

## 🚀 Kernfunktionen

- **📋 Plan- & Haushaltsverwaltung**:
  - Verwaltung des Wirtschaftsplans mit optionaler Erweiterbarkeit im Einstellungsmenü.
  - Aufgeräumtes Dashboard für den direkten Fokus auf den aktuellen Wirtschaftsplan.
  - **Plan-CRUD & Anpassung**: Pläne im Optionsmenü umbenennen, mit Beschreibungen versehen, archivieren oder reaktivieren.
  - **1:1 Plan-Duplizierung (Deep Copy)**: Duplizieren kompletter Pläne inklusive aller historischen Stände, Positionen und Beiträge als Vorlage.
  - **Sichere Plan-Löschung**: Kaskadierendes Löschen mit Bestätigung und Schutz des letzten verbleibenden Plans.
- **🏷️ Kategorien-Management & Live-Filter**:
  - **Eigene Kategorien definieren**: Individuelle Kategorien mit Farb-Tags und Icons anlegen, bearbeiten und sortieren.
  - **Live-Suche & Tabellen-Filter**: Sofortsuche über Positionen und Bemerkungen mit Live-Trefferzähler.
  - **Filter nach Betragstyp**: Schnelles Umschalten zwischen Ausgaben und Einnahmen.
- **👥 Granulare Benutzer- & Rechteverwaltung (RBAC)**:
  - Rollenbasiertes Rechtesystem (Administrator vs. Benutzer).
  - **Granulare Plan-Zuordnung (`user_plans`)**: Benutzer können gezielt einzelnen Plänen zugewiesen werden; Admins besitzen automatisch Vollzugriff auf alle Pläne.
  - **Funktionsspezifische Berechtigungen**: Checkboxen für Planverwaltung, Kategorien, Datenexport, Datenimport, Backups, Benutzerverwaltung und Testsuite.
  - Sichere Passwort-Verwaltung mit Hash-Verfahren.
- **📊 Modernes Glassmorphism Dashboard**:
  - Echtzeit-KPI-Karten für Gesamtausgaben, Beitragszahlungen und Rest-Saldo.
  - Dynamische Farbkodierung (positiver/negativer Saldo).
  - **Vollflächige vertikale Tabellenanordnung**: Ausgaben und Einnahmen untereinander mit maximaler Breite für lange Bezeichnungen und Bemerkungstexte.
  - **Ultra-kompakte Mobile-Kacheln**: Optimiertes Smartphone-Layout mit Titel & Betrag oben und dezenten Kategorie-Badges darunter.
- **📜 Versionshistorie & Stände-Management**:
  - Git-ähnliches Arbeiten mit versionierten Ständen (z. B. *„Stand ab 01.09.2026“*).
  - **In-Memory-Entwurfsmodus & In-Place Update**: Sicheres Experimentieren mit Dirty-Tracking und Möglichkeit, bestehende Stände direkt ohne Duplikat zu überschreiben.
  - **Schreibschutz & Entsperren**: Gezieltes Freischalten von Tabellenzeilen für Bearbeitung oder Löschung.
  - **Audit-Metadaten**: Lückenlose Nachvollziehbarkeit, wer welchen Stand wann erstellt oder geändert hat.
- **🔍 Historische Matrix-Vergleichsansicht**:
  - Side-by-Side Pivot-Vergleich aller historischen Stände nebeneinander mit dynamischer Kosten- und Beitragsentwicklung.
- **⏱️ Live-Intervall-Berechnungsengine**:
  - Automatische Monatskosten-Umrechnung für quartalsweise und jährliche Zahlungen.
- **💾 Datensicherung, Snapshots & Export**:
  - **Automatisierte Backups & Snapshots**: Konfigurierbare automatische Intervallsicherungen mit Rotation (Retention).
  - **Vollständiger JSON-Export & Import**: Sicherung und 1-Klick-Wiederherstellung aller Pläne, Stände, Kategorien und Archivierungszustände.
  - **Excel-Export (.xlsx)**: Professionell aufbereitete Arbeitsmappe mit formatierter Datums- und Währungsdarstellung.
- **🧪 Integrierte Live-Testsuite (Admin)**:
  - Führt die Pytest-Suite direkt aus der Web-App aus.
  - Live Server-Sent Events (SSE) Streaming mit Fortschrittsanzeige in Echtzeit.

---

## 🛠 Tech-Stack & Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Ausgabenplaner Architektur               │
├──────────────────────────────┬──────────────────────────────┤
│ Backend (Modulare Router):   │ Frontend (Modular ES6):      │
│ • Python 3.12+ / FastAPI     │ • state.js (Reactive Store)  │
│ • SQLite3 (atomar + WAL)     │ • api.js (Auth & Endpoints)  │
│ • openpyxl (Excel-Engine)    │ • formatters.js (DE Formats) │
│ • Multi-Plan & Category CRUD │ • 8 UI-Komponenten-Module    │
│ • Granulare RBAC Permissions │ • categories.js, plans.js    │
│ • SSE Subprocess Test Runner │ • users.js, backups.js etc.  │
└──────────────────────────────┴──────────────────────────────┘
```

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+), SQLite3
- **Frontend**: Vanilla ES6-Module (`<script type="module">`), CSS3 (Glassmorphism), HTML5
- **Datenexport**: `openpyxl` (Excel), JSON-Engine
- **Testing**: `pytest`, `pytest-cov`, `httpx` (75 automatisierte Tests)
- **Container & CI/CD**: Docker (Multi-Arch `linux/amd64` & `linux/arm64`), Docker Compose, GitHub Actions & GitHub Container Registry (GHCR)

---

## 📦 Installation & Start

### Option 1: Schneller Start mit Docker (Empfohlen für Server & Synology NAS)

Das offizielle Multi-Arch Docker-Image wird über GitHub Actions automatisch gebaut und in der GitHub Container Registry bereitgestellt.

```bash
docker-compose up -d
```

Oder direkt als Container starten:
```bash
docker run -d \
  --name ausgabenplaner \
  -p 3000:3000 \
  -v $(pwd)/data:/app/data \
  -e ADMIN_PASSWORD=admin123 \
  ghcr.io/phimafusion/ausgabenplaner:latest
```

Die Anwendung ist anschließend unter `http://localhost:3000` erreichbar. Die Datenbankdaten werden persistent im Verzeichnis `./data` gesichert.

---

### Option 2: Lokale Python-Umgebung (Entwicklung)

1. **Repository klonen**:
   ```bash
   git clone https://github.com/phimafusion/ausgabenplaner.git
   cd ausgabenplaner
   ```

2. **Virtuelle Umgebung erstellen & aktivieren**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Abhängigkeiten installieren**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Anwendung starten**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
   ```

   Öffne danach [http://localhost:3000](http://localhost:3000) im Browser.
   - Standard-Admin: `admin` / `admin123`

---

## 🧪 Tests ausführen

Das Projekt verfügt über eine vollständige Testabdeckung mit 75 automatisierten Tests:

```bash
# Tests ausführen
pytest tests -v

# Tests mit Coverage-Report
pytest --cov=app --cov-report=term-missing
```

---

## 📁 Projektstruktur

```text
ausgabenplaner/
├── app/
│   ├── routers/                 # Modulare FastAPI Router (Auth, Users, Plans, Categories, Data, Backups, Testsuite)
│   ├── auth.py                  # JWT-Token & Passwort-Hashing
│   ├── backups.py               # Backup-Engine & Scheduler
│   ├── crud.py                  # SQLite CRUD, Multi-Plan & Snapshot-Operationen
│   ├── database.py              # DB-Initialisierung, Migrationen & Seed-Daten
│   ├── domain.py                # Business-Logik & Intervall-Berechnungen
│   ├── main.py                  # FastAPI Endpunkte & Lifecycle
│   └── schemas.py               # Pydantic Modelle & Validierung
├── static/
│   ├── js/                      # Modulare Frontend-Architektur (ES6)
│   │   ├── state.js             # Anwendungs-Zustand & Dirty-Tracking
│   │   ├── dom.js               # DOM-Elemente Cache
│   │   ├── formatters.js        # Währungs- & Datumshelfer (DE)
│   │   ├── api.js               # Central API Client
│   │   ├── events.js            # Event-Listener Wiring
│   │   └── components/
│   │       ├── modals.js        # Dialoge & Guards
│   │       ├── kpi.js           # KPI-Rendering & Summenberechnung
│   │       ├── tables.js        # Positions- & Beitrags-Tabellen
│   │       ├── categories.js    # Kategorien-Verwaltung & Farbwahl
│   │       ├── history.js       # Timeline & Matrix-Vergleich
│   │       ├── users.js         # Benutzerverwaltung & Plan-Rechte
│   │       ├── testsuite.js     # SSE Testsuite-Runner
│   │       ├── backups.js       # Backup- & Snapshot-Verwaltung
│   │       └── plans.js         # Multi-Plan-Verwaltung & Switcher
│   ├── app.js                   # Haupt-Einstiegspunkt & Bootstrapping
│   ├── index.html               # Responsive Single-Page UI (v1.3.0)
│   └── styles.css               # Modernes Glassmorphism-Design
├── tests/                       # 75 Pytest-Tests (Domain, Auth, UI, Multi-Plan, Backups, Export)
├── data/                        # Lokales SQLite-Datenbankverzeichnis & Snapshots
├── docker-compose.yml           # Docker Compose Konfiguration (GHCR Image)
├── Dockerfile                   # Multi-Stage Dockerfile
├── requirements.txt             # Python Dependencies
├── TODO.md                      # Roadmap & Feature Backlog
└── README.md                    # Dokumentation
```

---

## 📌 Roadmap & Geplante Features

Zukünftige Erweiterungen und Vorschläge sind im [TODO.md](TODO.md) dokumentiert:
- 📊 Interaktive Diagramme (Kostenverteilung nach Kategorien & Trendverlauf)
- 📑 Druckfertiger PDF-Bericht für Versammlungen
- ⚡ Drag-and-Drop Sortierung & Inline-Editing
- 🌓 Theme-Toggle (Light / Dark Mode)

---

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz.