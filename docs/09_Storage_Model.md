# Storage Model v1.0

## 1. Purpose

The Storage Engine is responsible for managing the physical location of all biological samples stored in the laboratory.

This includes:

- DNA samples
- Protein expression pellets (Falcons)
- Purified protein aliquots (Eppendorf tubes)

The objective is to know at any time:

- Where a sample is stored.
- Which positions are free.
- Which positions are occupied.
- How many aliquots or Falcons remain.
- The complete movement history of every stored sample.

The Storage Engine is independent from the scientific information associated with each sample.

---

# 2. Design Principles

The storage model has been designed according to the following principles:

## 2.1 The software adapts to the laboratory

Existing laboratory labels, box names and workflows will be preserved whenever possible.

The implementation must not require relabelling existing boxes.

---

## 2.2 Physical objects have identity

A physical box is an object.

Its location may change.

Its identity does not.

---

## 2.3 Every sample occupies one physical position

A DNA tube

A Falcon

An aliquot

occupies exactly one storage position.

---

## 2.4 Empty boxes also exist

A box exists even if it contains no samples.

The system manages all physical boxes present in the laboratory.

---

## 2.5 One source of truth

Every storage location must exist only once inside the database.

No duplicated locations are allowed.

---

# 3. Storage hierarchy

The storage hierarchy is:

```
Freezer
    ↓
Rack
    ↓
Shelf (Falcon racks only)
    ↓
Box
    ↓
Position
    ↓
Stored Sample
```

---

# 4. Storage types

## 4.1 Freezers

Current version:

-80°C Freezer

Future versions may support multiple freezers.

---

## 4.2 Rack types

Two different rack systems exist.

### Protein storage racks

Used for Eppendorf boxes.

Numbered:

1–40

Each rack contains:

- five boxes

Each box contains:

- 8 × 8 positions

---

### Falcon storage racks

Named:

A
B
C
D

Each rack contains:

- two shelves

Each shelf contains:

- three Falcon boxes

Each Falcon box contains:

- 4 × 4 positions

---

# 5. Box types

Two box formats exist.

---

## Eppendorf Box

Capacity:

64 positions

Coordinates:

A1

A2

...

H8

---

## Falcon Box

Capacity:

16 positions

Coordinates:

A1

...

D4

---

# 6. Physical boxes

Every physical box has its own identity.

Properties:

- Internal ID
- Display name
- Box type
- Current rack
- Current shelf (if applicable)
- Notes
- Active

The display name corresponds to the label physically written on the box.

Examples:

BOX1

BOX2

JV1

DNA_SHARED

PROT_A

The display name may be modified without affecting the internal identity.

---

# 7. Storage positions

Every position inside a box is unique.

Examples:

A1

B4

H7

Each position can contain at most one sample.

---

# 8. Position status

A position may be:

EMPTY

Available for use.

---

OCCUPIED

Contains one sample.

---

RESERVED

Reserved for future use.

(Currently not used but supported.)

---

# 9. Stored samples

The Storage Engine stores:

DNA

Protein pellets

Protein aliquots

The Storage Engine does not store reagents.

---

# 10. Box movements

Boxes may be moved between racks.

Moving a box does not modify the samples stored inside it.

Only the box location changes.

---

# 11. Sample movements

Samples may be moved between positions.

Every movement is recorded.

Information recorded:

- Date
- User
- Origin
- Destination
- Reason

---

# 12. Occupancy rules

A position cannot contain more than one sample.

A sample cannot occupy multiple positions.

Moving a sample automatically frees its previous position.

Deleting a sample automatically frees its position.

---

# 13. Existing laboratory migration

The laboratory already contains:

- partially filled boxes
- completely full boxes
- empty boxes

The migration process must support all three situations.

No box names will be modified.

Existing labels will be preserved.

---

# 14. Future compatibility

The model has been designed to support future features including:

- QR codes
- Barcode labels
- Multiple freezers
- Additional rack types
- Automated storage statistics
- Mobile application
- Position reservation
- Batch movements

No database redesign should be required.

---

# 15. Design decisions

The following architectural decisions have been adopted.

✓ Boxes are independent physical objects.

✓ Box names are preserved.

✓ Locations are independent from scientific data.

✓ Storage is shared by DNA and proteins.

✓ Reagents are managed outside the Storage Engine.

✓ Every movement is traceable.

✓ The model prioritizes compatibility with the current laboratory workflow.