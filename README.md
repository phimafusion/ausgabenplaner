# Ausgabenplaner 📊💰

Ein moderner, transparenter und modularer Ausgaben- und Wirtschaftsplaner zur Verwaltung von Hausgeldern, Liegenschaftskosten, Haushaltsbudgets und Beitragszahlungen mit integrierter **Versionshistorie (Stände-Management)**, **Excel-Export**, **Live-Matrix-Vergleich** und **Echtzeit-Testsuite**.

---

## 🚀 Kernfunktionen

- **📊 Modernes Glassmorphism Dashboard**:
  - Echtzeit-KPI-Karten für Gesamtausgaben, Beitragszahlungen und Rest-Saldo.
  - Dynamische Farbkodierung (positiver/negativer Saldo).
  - Touch-freundliches, voll responsives Layout für Desktop, Tablet und Smartphone.
- **📜 Versionshistorie & Stände-Management**:
  - Git-ähnliches Arbeiten mit versionierten Ständen (z. B. *„Stand ab 01.09.2026“*).
  - **In-Memory-Entwurfsmodus**: Sicheres Experimentieren mit Dirty-Tracking und Warnungen bei ungespeicherten Änderungen.
  - **Schreibschutz & Entsperren**: Gezieltes Freischalten von Tabellenzeilen für Bearbeitung oder Löschung.
  - **Audit-Metadaten**: Lückenlose Nachvollziehbarkeit, wer welchen Stand wann erstellt oder geändert hat.
- **🔍 Historische Matrix-Vergleichsansicht**:
  - Side-by-Side Pivot-Vergleich aller historischen Stände nebeneinander mit dynamischer Kosten- und Beitragsentwicklung.
- **⏱️ Live-Intervall-Berechnungsengine**:
  - Automatische Monatskosten-Umrechnung für quartalsweise und jährliche Zahlungen.
- **👥 Benutzer- & Rechteverwaltung (RBAC)**:
  - Rollenbasiertes Rechtesystem (Administrator vs. Benutzer).
  - Granulare Rechtevergabe (z. B. Export-Rechte für Benutzer).
  - Sichere Passwort-Verwaltung mit Hash-Verfahren.
- **💾 Datensicherung & Export**:
  - **JSON-Export & Import**: Vollständige Sicherung und 1-Klick-Wiederherstellung aller Pläne, Stände und Positionen.
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
│ Backend:                     │ Frontend (Modular ES6):      │
│ • Python 3.12+ / FastAPI     │ • state.js (Reactive Store)  │
│ • SQLite3 (lokal & atomar)   │ • api.js (Auth & Endpoints)  │
│ • openpyxl (Excel-Engine)    │ • formatters.js (DE Formats) │
│ • SSE Subprocess Test Runner │ • 6 UI-Komponenten-Module    │
└──────────────────────────────┴──────────────────────────────┘
```

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+), SQLite3
- **Frontend**: Vanilla ES6-Module (`<script type="module">`), CSS3 (Glassmorphism), HTML5
- **Datenexport**: `openpyxl` (Excel), JSON-Engine
- **Testing**: `pytest`, `pytest-cov`, `httpx` (53 automatisierte Tests)
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

Das Projekt verfügt über eine vollständige Testabdeckung mit 49 automatisierten Tests:

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
│   ├── auth.py                  # JWT-Token & Passwort-Hashing
│   ├── crud.py                  # SQLite CRUD & Snapshot-Operationen
│   ├── database.py              # DB-Initialisierung & Seed-Daten
│   ├── domain.py                # Business-Logik & Intervall-Berechnungen
│   ├── main.py                  # FastAPI Endpunkte & SSE Test Runner
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
│   │       ├── history.js       # Timeline & Matrix-Vergleich
│   │       ├── users.js         # Benutzerverwaltung & Rechte
│   │       └── testsuite.js     # SSE Testsuite-Runner
│   ├── app.js                   # Haupt-Einstiegspunkt & Bootstrapping
│   ├── index.html               # Responsive Single-Page UI
│   └── styles.css               # Modernes Glassmorphism-Design
├── tests/                       # 39 Pytest-Tests (Domain, Auth, UI, History)
├── data/                        # Lokales SQLite-Datenbankverzeichnis
├── docker-compose.yml           # Docker Compose Konfiguration
├── Dockerfile                   # Multi-Stage Dockerfile
├── requirements.txt             # Python Dependencies
├── TODO.md                      # Roadmap & Feature Backlog
└── README.md                    # Dokumentation
```

---

## 📌 Roadmap & Geplante Features

Zukünftige Erweiterungen und Vorschläge sind im [TODO.md](TODO.md) dokumentiert:
- 📊 Interaktive Diagramme (Kostenverteilung nach Kategorien & Trendverlauf)
- 🏢 Multi-Plan-Verwaltung (Mehrere Liegenschaften/Objekte parallel)
- 📑 Druckfertiger PDF-Bericht für Versammlungen
- 🏷️ Eigenes Kategorien-Management mit Farb-Tags
- ⚡ Drag-and-Drop Sortierung & Inline-Editing

---

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz.