# Software Architecture

## Purpose

This document defines the software architecture of the Laboratory
Information Management System (LIMS).

Its purpose is to ensure that the application remains maintainable,
scalable, modular, and easy to evolve over time.

------------------------------------------------------------------------

# Architectural Principles

-   Separation of responsibilities.
-   Incremental development.
-   Reuse existing code whenever possible.
-   Avoid unnecessary refactoring.
-   One responsibility per module.
-   Business logic independent from the user interface.
-   Internal data model independent from Excel files.
-   Low coupling and high cohesion.

------------------------------------------------------------------------

# Layered Architecture

Streamlit UI

↓

Application Services

↓

Repositories

↓

SQLite / Excel Adapter

↓

Google Drive

------------------------------------------------------------------------

# UI Layer

Responsible for user interaction only.

# Service Layer

Contains business rules, validation and workflows.

# Repository Layer

Responsible for SQLite access and Excel/Google Drive integration.

Repositories never contain business rules.

# Database Layer

SQLite stores the official internal model.

# Target Project Structure

LIMS/

app.py

config.py

requirements.txt

database/

models/

repositories/

services/

pages/

ui/

storage/

tests/

docs/

------------------------------------------------------------------------

# Evolution Strategy

The architecture evolves through small, reversible changes.
