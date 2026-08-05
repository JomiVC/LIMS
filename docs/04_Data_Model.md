# Data Model

## Purpose

This document defines the logical data model of the LIMS. It is
independent of the user interface, database engine and Excel
implementation.

------------------------------------------------------------------------

# Reagent

Represents a reagent definition.

## Attributes

-   inventory_number (Primary Key, Integer)
-   name
-   supplier
-   supplier_reference
-   category
-   minimum_stock
-   unit
-   owner
-   observations
-   status

## Relationships

-   One Reagent has many Reagent Stock records.
-   One Reagent has many Inventory Movements.

------------------------------------------------------------------------

# Reagent Stock

Represents a physical stock of a reagent stored in one location.

## Attributes

-   stock_id
-   reagent_inventory_number
-   location
-   quantity
-   batch_number (optional)
-   expiration_date (optional)

------------------------------------------------------------------------

# DNA Sample

Represents one physical DNA tube.

## Attributes

-   dna_number (Primary Key)
-   insert_name
-   uniprot_id
-   residues
-   sequence_description
-   vector
-   antibiotic_resistance
-   vector_design
-   organism_optimized
-   concentration
-   location
-   box
-   position
-   origin
-   provider_order_number
-   purchase_date
-   owner
-   sequencing_file
-   sequencing_folder

------------------------------------------------------------------------

# Design Decisions

-   Existing laboratory identifiers remain the primary keys.
-   Excel files remain unchanged.
-   The internal model may contain richer structures than Excel.
-   Stock is updated automatically from inventory operations but may be
    adjusted manually by authorized users.
-   Manual adjustments are recorded as inventory movements.

------------------------------------------------------------------------

# Future Entities

The following entities will be completed in the next revision:

-   Protein
-   Protein Expression
-   Pellet
-   Purification
-   Aliquot
-   Antibody
-   User
-   Purchase Order
-   Inventory Movement
-   Freezer
-   Rack
-   Box
-   Position
