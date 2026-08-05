# Business Rules

## Purpose

This document defines the business rules governing the Laboratory
Inventory Management System (LIMS). These rules describe laboratory
operations independently of implementation details.

------------------------------------------------------------------------

# Inventory

1.  Every physical item has one current location.
2.  A storage position can contain at most one physical item.
3.  Every inventory change must be traceable.
4.  Stock values must never become negative.

# Reagents

1.  Every reagent has a unique inventory number.
2.  Reagents can be consumed but remain in the catalog unless deleted by
    an administrator.
3.  Low stock alerts are generated when current stock reaches the
    minimum threshold.

# Protein Expression

1.  One Protein Expression produces one or more Pellets.
2.  Every Pellet belongs to exactly one Protein Expression.
3.  Pellets may be consumed independently.

# Purification

1.  One Purification produces one or more Aliquots.
2.  Every Aliquot belongs to exactly one Purification.
3.  Aliquots may be consumed independently.

# DNA

1.  Every DNA sample has one storage location.
2.  DNA records remain in the catalog even if stock is exhausted.

# Storage

1.  Every Box belongs to one Rack.
2.  Every Rack belongs to one Freezer.
3.  Falcon boxes and Eppendorf boxes use different layouts.
4.  A Position cannot be assigned to multiple items simultaneously.

# Purchase Orders

1.  Purchase Orders can be Requested, Received or Cancelled.
2.  Receiving an order may create a new Reagent if it does not already
    exist.

# Users

1.  Administrators have full access.
2.  Researchers may register production and consumption.
3.  Guests have read-only access except for purchase requests.

# Excel Synchronization

1.  Excel files remain supported.
2.  The internal domain model is the source of truth.
3.  Synchronization conflicts require administrator approval.

# Future Rules

Additional rules will be added as new modules are introduced.
