# Ausgabenplaner 📊💰

Ein moderner, transparenter Budget- und Ausgabenplaner zur Verwaltung von monatlichen Einnahmen, Fixkosten, Abonnements, Sparzielen und variablen Ausgaben – ideal für Haushalte, Paare und Einzelpersonen.

---

## 🚀 Features

- **Übersichtliches Dashboard**: Gesamteinnahmen, Fixkosten, Sparrate und verfügbares Budget auf einen Blick.
- **Kategoriensystem**:
  - 🏠 **Fixkosten** (Miete, Strom, Internet etc.)
  - 📱 **Abos & Verträge** (Streaming, Mitgliedschaften etc.)
  - 🐖 **Sparen & Rücklagen** (Notgroschen, Urlaub, Notfallfond etc.)
  - 📈 **Investitionen & ETF-Sparpläne** (Altersvorsorge, Wertpapiere etc.)
- **Dynamische Aufteilung**: Automatische Berechnung von Kostenanteilen (z. B. nach prozentualem Gehaltsverhältnis bei Paaren/WGs).
- **Sicherheit & Authentifizierung**:
  - JWT-basierte Authentifizierung mit sicherem Session-Handling.
  - Rollen- und Benutzerverwaltung via SQLite.
- **Backup & Datensicherung**:
  - Vollständiger **JSON-Export** aller Daten (Kategorien, Einträge, Einstellungen).
  - Zuverlässiger **JSON-Import** mit Validierung zur Wiederherstellung von Snapshots.
- **Leichtgewichtig & Schnell**: FastAPI-Backend mit nativer SQLite-Datenbank und responsivem Vanilla-CSS/JS-Frontend ohne schwerfällige Frameworks.

---

## 🛠 Tech-Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Datenbank**: SQLite (lokal gespeichert, wartungsarm)
- **Frontend**: Modernes Vanilla HTML5, CSS3 (Modernes Glassmorphism-UI / Dark Accent Theme) & JavaScript
- **Containerisierung**: Docker & Docker Compose
- **Testing**: `pytest`, `pytest-cov`, `httpx`

---

## 📦 Installation & Start

### Option 1: Lokale Python-Umgebung

1. **Repository klonen**:
   ```bash
   git clone https://github.com/phimafusion/ausgabenplaner.git
   cd ausgabenplaner
   ```

2. **Virtuelle Umgebung erstellen und aktivieren**:
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

---

### Option 2: Mit Docker & Docker Compose

```bash
docker-compose up -d --build
```

Die Anwendung ist anschließend unter `http://localhost:3000` erreichbar. Die Datenbankdaten werden persistent im Verzeichnis `./data` gesichert.

---

## 🧪 Tests ausführen

Das Projekt verfügt über umfassende automatisierte Tests für Domainlogik, CRUD-Endpunkte, Authentifizierung, Edge Cases und den JSON-Export/Import.

```bash
# Tests ausführen
pytest

# Tests mit Coverage-Report
pytest --cov=app --cov-report=term-missing
```

---

## 📁 Projektstruktur

```text
ausgabenplaner/
├── app/
│   ├── auth.py          # Authentifizierung & Token-Handling (JWT / Passwords)
│   ├── crud.py          # Datenbankoperationen & Import/Export
│   ├── database.py      # SQLite-Verbindung & Schema-Initialisierung
│   ├── domain.py        # Business-Logik & Berechnungen
│   ├── main.py          # FastAPI App & Endpunkte
│   └── schemas.py       # Pydantic Modelle & Datenvalidierung
├── static/
│   ├── app.js           # Frontend App Logik & API-Interaktionen
│   ├── index.html       # Hauptseite
│   └── styles.css       # Design & Styling
├── tests/               # Pytest Testsuite
├── data/                # Lokales SQLite-Datenbankverzeichnis (persistent)
├── docker-compose.yml   # Docker Compose Konfiguration
├── Dockerfile           # Multi-Stage Dockerfile
├── requirements.txt     # Python Dependencies
└── README.md            # Dokumentation
```

---

## 📌 Roadmap / To-Do

- [ ] **1. Historienmodul integrieren**:
  - Archivierung und Auswertung historischer Monatsabschlüsse.
  - Langzeitvergleich von Einnahmen, Ausgaben und Sparquoten über Monate und Jahre hinweg (Diagramme & Trends).
- [x] **2. Mobile Ansicht (Responsive Design)**:
  - Optimierung der Benutzeroberfläche für Smartphones und Tablets.
  - Touch-freundliche Navigation (Hamburger-Menü & Touch-Targets), responsive Tabellenkarten und mobile Dialoge für kompakte Displays.

---

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz.