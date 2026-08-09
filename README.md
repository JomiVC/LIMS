# LIMS – Laboratory Information Management System

## Overview

LIMS is a Laboratory Information Management System developed for a
molecular biology research laboratory.

The application manages laboratory inventory, protein production,
DNA stock, storage locations, E.Coli strains, cell culture, and
purchase orders, while maintaining compatibility with the
laboratory's existing Excel workflow.

The project is designed to evolve incrementally from an initial
prototype into a scalable and maintainable application. Modules are
built one at a time: each module's requirements are specified in
detail before implementation begins.

## Modules

- **Reagents** — Search, Orders, Register/delete items
- **DNA** — Search, Register
- **Proteins** — Search, Register, Expressed proteins, Purified
  proteins, Proteases
- **Storage** — Samples, Boxes, New equipment (create box / rack /
  freezer)
- **E.Coli strains** — Search, Register
- **Cell culture** — Search, Register
- **Research Assistant** — Plan an experiment (the only module
  without a search)

Every module has its own search, except Research Assistant.
Protein, protease, DNA, and E.Coli strain registrations support
file attachments (PDFs, chromatograms, scanned gels, etc.).

Planned for later: Excel synchronization, QR code support,
statistics and dashboards.

## Technology Stack

- Python
- Streamlit
- SQLite (WAL mode, for concurrent multi-user access)
- Pandas
- Google Drive API
- Git & GitHub

## Project Structure

```
LIMS/

docs/
database/
models/
repositories/
services/
pages/
ui/
storage/
tests/

app.py
config.py
requirements.txt
README.md
```

## Documentation

Project documentation is located in the `docs` folder. The main
documents are:

- Architecture
- Domain Model
- Business Rules
- Data Model
- Excel Integration
- Software Architecture
- Decision Log
- Roadmap

## Development Principles

- Incremental development — one module, one visible feature at a
  time
- Clean architecture with clear layer separation (models →
  repositories → services → pages)
- Reuse existing code whenever possible
- Avoid unnecessary refactoring
- Excel compatibility
- Long-term maintainability
- All UI text in English

## Current Status

**Storage module in progress.** Freezers, racks, and boxes can be
registered and browsed. Items (DNA / protein aliquots / reagent
lots) can be assigned to free positions, though those item types
are still minimal stub tables pending their own dedicated modules.

## Author

Developed by Jomi for the Laboratory of Molecular Biology.

---

## Development Principles

The project follows these principles:

- Incremental development
- Clean architecture
- Separation of responsibilities
- Reuse existing code whenever possible
- Avoid unnecessary refactoring
- Excel compatibility
- Long-term maintainability

---

## Current Status

Current development stage:

**Version 0.1 – Project Foundation**

The project is currently focused on building the software architecture before implementing laboratory modules.

---

## Author

Developed for the Molecular Biology Laboratory.

Architecture and implementation developed collaboratively using ChatGPT as software architect and development assistant.