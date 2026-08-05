# Architecture Decision Log (ADR)

## Purpose

This document records the most important architectural decisions made
during the development of the Laboratory Information Management System
(LIMS).

Its purpose is to explain why decisions were made, making future
maintenance and evolution easier.

------------------------------------------------------------------------

# ADR-001

## Title

Application language is English.

### Status

Accepted

### Reason

The laboratory works in English.

------------------------------------------------------------------------

# ADR-002

## Title

Existing laboratory identifiers remain unchanged.

### Status

Accepted

### Reason

Inventory Numbers, DNA Numbers and other laboratory identifiers already
exist on physical labels and must be preserved.

------------------------------------------------------------------------

# ADR-003

## Title

SQLite as the initial database.

### Status

Accepted

### Reason

SQLite is simple to deploy and adequate for the laboratory size. Future
migration to PostgreSQL should remain possible.

------------------------------------------------------------------------

# ADR-004

## Title

Excel files remain supported.

### Status

Accepted

### Reason

Existing Excel files remain part of the laboratory workflow and must
stay synchronized.

------------------------------------------------------------------------

# ADR-005

## Title

Internal model independent from Excel.

### Status

Accepted

### Reason

Excel is an integration layer, not the application's internal data
model.

------------------------------------------------------------------------

# ADR-006

## Title

Layered software architecture.

### Status

Accepted

### Reason

Separate UI, business logic, repositories and data sources to improve
maintainability.

------------------------------------------------------------------------

# ADR-007

## Title

Incremental development.

### Status

Accepted

### Reason

The project evolves through small, testable iterations instead of large
rewrites.

------------------------------------------------------------------------

# ADR-008

## Title

Single logical database.

### Status

Accepted

### Reason

The application uses one logical data model even if multiple external
sources exist.

------------------------------------------------------------------------

# ADR-009

## Title

Physical storage hierarchy.

### Status

Accepted

### Reason

Storage follows:

Freezer → Rack → Level (optional) → Box → Position

------------------------------------------------------------------------

# ADR-010

## Title

Architecture before implementation.

### Status

Accepted

### Reason

Architectural decisions are documented before coding to reduce technical
debt.
