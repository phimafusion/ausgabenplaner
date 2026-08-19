# Ausgabenplaner – Roadmap & Feature Backlog (TODO) 📋🚀

Dieses Dokument fasst geplante Erweiterungen, architektonische Verbesserungen und Ideen für zukünftige Releases zusammen.

---

## 🚀 0. DevOps, CI/CD & Synology Deployment (🔥 Höchste Priorität)
- [x] **GitHub Actions Container Build & GitHub Container Registry (GHCR)**:
  - Automatischer Build des Multi-Arch Docker-Images (`linux/amd64`, `linux/arm64`) bei Push auf `main` oder neuem Release.
  - Veröffentlichung des fertigen Images unter `ghcr.io/phimafusion/ausgabenplaner:latest`.
  - Anpassung der `docker-compose.yml` auf `image: ghcr.io/phimafusion/ausgabenplaner:latest` für 1-Klick-Updates im Synology Container Manager ohne lokalen Build-Aufwand auf dem NAS.

---

## 📊 1. Visualisierung & Analytics (Charts & Trends)
- [ ] **Kategorien-Aufteilung (Donut / Pie Chart)**:
  - Visuelle Kostenverteilung (z. B. Wohnen, Energie, Versicherung, Instandhaltung, Rücklagen).
- [ ] **Historische Trendanalyse (Line Chart)**:
  - Verlaufskurve für Gesamtausgaben, Beiträge und Rest-Saldo über alle gespeicherten Stände hinweg.
- [ ] **Dashboard KPI-Badges**:
  - Durchschnittliche monatliche Kosten pro Kopf / Partei.

---

## 🏢 2. Multi-Plan-Verwaltung (Liegenschaften / Mandanten)
- [ ] **Plan-Auswahl in der Top-Navigation**:
  - Dropdown zur Auswahl und zum schnellen Wechsel zwischen verschiedenen Liegenschaften/Plänen (z. B. „Tütingstraße 22“, „Musterweg 5“, „Projekt B“).
- [ ] **Plan-CRUD für Administratoren**:
  - Neuen Plan anlegen, archivieren, umbenennen oder duplizieren.
- [ ] **Plan-spezifische Benutzerzuordnungen**:
  - Berechtigungen pro Plan/Liegenschaft vergeben.

---

## 📑 3. PDF-Export & Druckoptimierung
- [ ] **Druckfertiger PDF-Bericht**:
  - 1-Klick-Download eines ansprechend formatierten PDF-Monatsberichts für Eigentümerversammlungen oder Mieterabrechnungen.
- [ ] **CSS Print-Stylesheet (`@media print`)**:
  - Sauberes, tintensparendes Drucklayout ohne Navbar, Footer und Modals.

---

## 🏷️ 4. Kategorien-Management & Tabellen-Filter
- [ ] **Kategorien-Editor**:
  - Eigene Kategorien mit individuellen Farb-Tags anlegen und verwalten.
- [ ] **Live-Suche & Tabellen-Filter**:
  - Sofortsuche über Positionen und Bemerkungen in der Hauptmaske.
  - Filtern nach Kategorie, Betrag oder Beitragszahler.

---

## ⚡ 5. Bedienkomfort & Workflow-Optimierung
- [ ] **Drag-and-Drop Sortierung**:
  - Positionen und Beiträge per Drag-and-Drop in der Tabelle umsortieren (`sort_order`).
- [ ] **Inline-Editing**:
  - Schnellbearbeitung von Beträgen und Texten direkt in der Tabellenzelle (mit `Enter` bestätigen / `Esc` abbrechen).
- [ ] **Tastaturkürzel**:
  - `Strg + S` zum schnellen Speichern des aktuellen Stands.
  - `Strg + N` zum Hinzufügen einer neuen Position.

---

## 🌓 6. Theming (Dark / Light Mode)
- [ ] **Theme-Toggle**:
  - Umschalter zwischen dem aktuellen Dark Glassmorphism Design und einem modernen, kontrastreichen Light Mode.
- [ ] **Persistierung des Themes**:
  - Speichern der Benutzereinstellung im `localStorage`.
