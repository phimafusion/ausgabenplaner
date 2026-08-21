# Ausgabenplaner – Roadmap & Feature Backlog (TODO) 📋🚀

Dieses Dokument fasst geplante Erweiterungen, architektonische Verbesserungen und Ideen für zukünftige Releases zusammen.

---

## 🚀 0. DevOps, CI/CD & Synology Deployment (🔥 Höchste Priorität)
- [x] **GitHub Actions Container Build & GitHub Container Registry (GHCR)**:
  - Automatischer Build des Multi-Arch Docker-Images (`linux/amd64`, `linux/arm64`) bei Push auf `main` oder neuem Release.
  - Veröffentlichung des fertigen Images unter `ghcr.io/phimafusion/ausgabenplaner:latest`.
  - Anpassung der `docker-compose.yml` auf `image: ghcr.io/phimafusion/ausgabenplaner:latest` für 1-Klick-Updates im Synology Container Manager ohne lokalen Build-Aufwand auf dem NAS.
- [x] **Versionsanzeige im Header & Changelog-Reiter**:
  - Permanente Anzeige der Versionsnummer (`v1.3.0`) im Navbar-Header und Login.
  - Eigener Reiter in den Einstellungen für die Versionshistorie und Release Notes (Changelog).
- [x] **Plan-Löschung**:
  - Administratoren können Pläne sicher löschen (inkl. Bestätigungsdialog, Kaskadierung und Schutz des letzten Plans).

---

## 📊 1. Visualisierung & Analytics (Charts & Trends)
- [ ] **Kategorien-Aufteilung (Donut / Pie Chart)**:
  - Visuelle Kostenverteilung (z. B. Wohnen, Energie, Versicherung, Instandhaltung, Rücklagen).
- [ ] **Historische Trendanalyse (Line Chart)**:
  - Verlaufskurve für Gesamtausgaben, Beiträge und Rest-Saldo über alle gespeicherten Stände hinweg.
- [ ] **Dashboard KPI-Badges**:
  - Durchschnittliche monatliche Kosten pro Kopf / Partei.

---

## 📋 2. Plan-Verwaltung & Optionen
- [x] **Zentrale Plan-Verwaltung im Optionsmenü**:
  - Verwaltung, Umbenennung und Wechsel von Plänen im Einstellungsmenü bei aufgeräumtem Dashboard.
- [x] **Plan-CRUD für Administratoren**:
  - Neuen Plan anlegen, archivieren/reaktivieren, umbenennen oder duplizieren (vollständige Deep-Copy als Vorlage).
- [x] **Plan-spezifische Benutzerzuordnungen**:
  - Granulare Berechtigungen pro Plan vergeben (RBAC via `user_plans`).

---

## 📑 3. PDF-Export & Druckoptimierung
- [ ] **Druckfertiger PDF-Bericht**:
  - 1-Klick-Download eines ansprechend formatierten PDF-Monatsberichts für Eigentümerversammlungen oder Mieterabrechnungen.
- [ ] **CSS Print-Stylesheet (`@media print`)**:
  - Sauberes, tintensparendes Drucklayout ohne Navbar, Footer und Modals.

---

## 🏷️ 4. Kategorien-Management & Tabellen-Filter
- [x] **Kategorien-Editor**:
  - Eigene Kategorien mit individuellen Farb-Tags und Icons anlegen und verwalten.
- [x] **Granulare Benutzerberechtigung**:
  - Recht `can_manage_categories` per Checkbox im Benutzerformular vergeben.
- [x] **Live-Suche & Tabellen-Filter**:
  - Sofortsuche über Positionen und Bemerkungen in der Hauptmaske.
  - Filtern nach Kategorie und Betragstyp (Ausgaben/Einnahmen) mit Live-Trefferzähler.

---

## ⚡ 5. Bedienkomfort & Workflow-Optimierung
- [x] **Stand direkt aktualisieren (In-Place Update)**:
  - Bestehende Versionen direkt ohne Erstellung eines neuen Verlaufs-Eintrags überschreiben.
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
