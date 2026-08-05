# Laboratory Inventory Management System (LIMS)

**Architecture v1.0**

------------------------------------------------------------------------

# 1. Project Vision

## Purpose

The purpose of this project is to develop a robust, scalable and
maintainable Laboratory Inventory Management System (LIMS) for a
molecular biology laboratory.

The application will centralize the management of laboratory inventory,
including reagents, DNA, protein production, purified proteins, storage
locations and purchase requests.

The system is intended to become the primary inventory management tool
of the laboratory while remaining compatible with the current
Excel-based workflow.

## Objectives

The system must:

-   Manage laboratory reagents.
-   Manage protein expression batches.
-   Manage purified protein stocks.
-   Manage DNA inventory.
-   Track the exact physical location of every stored item.
-   Register inventory movements.
-   Control stock levels.
-   Generate stock and expiration alerts.
-   Synchronize information with existing Excel files stored in Google
    Drive.
-   Support future extensions without requiring major architectural
    changes.

## Scope

The application covers:

-   Laboratory inventory
-   Storage management
-   Protein production
-   DNA inventory
-   Purchase requests
-   User management
-   Inventory history
-   Excel synchronization

The application does not replace laboratory notebooks or experimental
records.

------------------------------------------------------------------------

# 2. Design Principles

## 2.1 Domain First

The software models how the laboratory works before modelling databases,
Excel files or the user interface.

## 2.2 Incremental Development

The project evolves through small, controlled improvements. Existing
code should be reused whenever it provides value.

## 2.3 Single Source of Truth

The domain model represents the laboratory. Excel files are treated as
an integration layer, not as the internal data model.

## 2.4 Maintainability

The architecture prioritizes readability, modularity and long-term
maintenance.

## 2.5 Scalability

New modules should be added without redesigning the existing system.

Examples include:

-   QR codes
-   Mobile application
-   Statistics
-   Order management
-   User authentication
-   Notifications

## 2.6 Traceability

Relevant inventory actions should be traceable through inventory
movements and history records.

## 2.7 Documentation First

Architectural decisions should be documented before implementation
whenever possible.

------------------------------------------------------------------------

## Document Status

-   Version: 1.0 (Draft)
-   Status: Under Development
-   Last Updated: August 2026
