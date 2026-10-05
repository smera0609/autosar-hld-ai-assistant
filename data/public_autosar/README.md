# Public AUTOSAR External Validation Data

This directory is used for external validation of the AUTOSAR HLD Document Analysis Assistant.

## Dataset

The external validation uses the **AUTOSAR Classic Platform Workflow Example** published by AUTOSAR.

The downloaded AUTOSAR artifacts are not included in this repository. They must be obtained separately from the official AUTOSAR source and placed locally under:

`data/public_autosar/AUTOSAR_WorkflowExample/`

## Purpose

The project's primary evaluation corpus consists of controlled synthetic AUTOSAR-style HLD documents with known ground truth.

The public AUTOSAR Workflow Example is used separately to evaluate whether the architecture-analysis pipeline can generalize to official AUTOSAR artifacts.

The ARXML validation pipeline performs:

1. ARXML parsing
2. Software-component extraction
3. Port and interface extraction
4. SW-COMPONENT-PROTOTYPE to component-type resolution
5. Assembly connector extraction
6. Conversion to the project's common ArchitectureModel
7. Dependency construction
8. Architecture graph generation

## Current External Validation Result

The tested AUTOSAR Workflow Example produced:

- 21 ARXML files processed
- 0 XML parse errors
- 8 component definitions
- 14 port definitions
- 773 interface catalogue definitions
- 7 component prototype mappings
- 5 assembly connectors
- 3 active interfaces in the common architecture model
- 4 unique component-level dependencies
- 13 graph nodes
- 10 graph edges

The validation completed without unresolved component-instance dependencies or dangling dependency endpoints.

## Important Interpretation

These results demonstrate compatibility with the tested public AUTOSAR artifacts and provide external generalization evidence.

They do **not** represent precision or recall against a production OEM HLD ground-truth dataset.

The 773 interface definitions belong to the interface catalogue contained in the example package; they should not be interpreted as 773 active interfaces in the extracted architecture.

## Repository Policy

Official AUTOSAR downloaded artifacts are intentionally excluded from version control. This repository contains the parser, adapter, tests, and validation methodology needed to reproduce the external validation after obtaining the source artifacts separately.