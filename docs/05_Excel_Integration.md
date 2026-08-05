# Excel Integration

## Purpose

This document defines how the LIMS synchronizes with the laboratory's
existing Excel files.

## Principles

-   Existing Excel files remain unchanged.
-   The internal domain model is independent of the Excel structure.
-   Excel files are an integration layer, not the application's data
    model.
-   Administrators control write operations and conflict resolution.

## Integration Strategy

For each Excel workbook:

1.  Read data into the application.
2.  Map Excel columns to the internal domain model.
3.  Apply business rules.
4.  Persist changes.
5.  Write approved updates back to Excel.

## Synchronization Rules

-   Reads may be performed by the application.
-   Writes require administrator authorization.
-   Conflicts are presented to an administrator before applying changes.
-   Data not represented in Excel remains stored only in the
    application.

## Initial Excel Sources

-   Reagents
-   Purchase Orders
-   DNA Inventory
-   Protein Expressions
-   Purified Proteins
-   Rack Map
-   Box Details

## Future Work

Each workbook will receive a detailed field mapping to the internal
model in a later version of this document.
