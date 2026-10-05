# AUTOSAR HLD Intelligence & Validation Assistant

An AI-assisted engineering tool for analyzing AUTOSAR-style High-Level Design (HLD) documents and validating architecture information from AUTOSAR artifacts.

The system converts automotive architecture documents into searchable and structured engineering knowledge by combining document processing, architecture extraction, consistency validation, Retrieval-Augmented Generation (RAG), knowledge graphs, revision comparison, OCR, human review, and external AUTOSAR ARXML validation.

> This repository is an engineering prototype. Controlled evaluation is performed using synthetic AUTOSAR-style HLD documents with known ground truth. A separate external-validation pipeline uses publicly available official AUTOSAR workflow artifacts. The system is intended to assist engineers, not replace engineering review or formal architecture governance.

---

## Problem Statement

Automotive High-Level Design documents can contain large amounts of architecture information, including:

- Software components
- Interfaces
- P-Ports and R-Ports
- Signals
- Dependencies
- Functional flows
- Integration relationships

Manually locating, validating, comparing, and tracing this information across large HLD documents can require significant engineering effort.

This project develops an AI-assisted AUTOSAR HLD analysis system that combines deterministic architecture analysis with evidence-grounded AI search.

The goal is not to automatically approve architecture decisions, but to help engineers extract, inspect, search, validate, compare, and review architecture information more efficiently.

---

# Key Features

## HLD Document Ingestion

The application supports automotive HLD PDF documents and provides:

- Page-aware text extraction
- Section-aware document chunking
- Metadata preservation
- Native PDF support
- Scanned PDF support
- Automatic OCR fallback

---

## OCR Support

Scanned documents are processed using Tesseract OCR when native text extraction is insufficient.

This enables the same downstream architecture extraction pipeline to operate on both native and scanned HLD documents.

---

## Architecture Extraction

The system extracts structured architecture entities including:

- Software Components
- Interfaces
- P-Ports and R-Ports
- Signals
- Component Dependencies
- Functional Flows

These entities are represented using a common structured architecture model.

---

## Architecture Consistency Validation

A deterministic validation layer checks architecture information for structural inconsistencies such as:

- Missing provider ports
- Missing consumer ports
- Undefined interfaces
- Unknown components
- Invalid dependencies
- Signal/interface inconsistencies

Using explicit rules for structural validation reduces dependence on LLM reasoning for checks that can be performed deterministically.

---

## Evidence-Grounded RAG

The question-answering pipeline uses:

- Sentence Transformer embeddings
- ChromaDB vector storage
- Semantic retrieval
- Local Qwen LLM through Ollama
- Evidence-grounded prompting
- Page/source citation metadata

Pipeline:

```text
HLD
 ↓
Chunking
 ↓
Sentence Transformer Embeddings
 ↓
ChromaDB
 ↓
Semantic Retrieval
 ↓
Retrieved HLD Evidence
 ↓
Local Qwen LLM
 ↓
Grounded Answer + Source Metadata
```

When sufficient evidence cannot be found in the HLD, the system is designed to respond:

> Insufficient evidence in the provided HLD.

This reduces unsupported answers instead of encouraging the model to guess.

---

## Architecture Knowledge Graph

Architecture relationships are reconstructed as a graph.

Example:

```text
Component
    |
    | PROVIDES
    v
Interface
    |
    | CARRIES
    v
Signal
```

Additional relationships include:

```text
CONSUMED_BY
DEPENDS_ON
FLOWS_TO
```

The graph enables architecture traceability, dependency exploration, and structural inspection.

---

## Functional Flow Extraction

Functional flows between components can be reconstructed from architecture information.

Example:

```text
WheelSpeedSensor
        ↓
VehicleSpeedController
        ↓
InstrumentCluster
```

Functional flows can also be incorporated into the architecture graph.

---

## Revision Comparison

The system compares HLD revisions and identifies architecture changes such as:

- Added or removed components
- Added or removed interfaces
- Port changes
- Signal changes
- Dependency changes
- Signal renaming

This provides structured change visibility between architecture document versions.

---

## Engineer Review Workflow

Automated validation findings remain under human control.

Findings can be marked as:

- Pending
- Accepted
- Rejected

Engineer decisions and comments are persisted using SQLite.

This implements a human-in-the-loop review process instead of automatically accepting AI-generated findings.

---

# Official AUTOSAR External Validation

In addition to the controlled synthetic HLD benchmark, the project includes a separate external-validation pipeline using publicly available official AUTOSAR Workflow Example artifacts.

The purpose of this pipeline is to test whether the architecture model and graph-building approach can process AUTOSAR ARXML structures outside the synthetic HLD corpus.

This is a separate validation activity and is not included in the synthetic HLD precision/recall measurements.

## External Validation Pipeline

```text
Official AUTOSAR Workflow Example ZIP
                |
                v
          ARXML Discovery
                |
                v
            ARXML Parser
                |
                v
    Components / Ports / Interfaces
     Instances / Assembly Connectors
                |
                v
      Common Architecture Model
                |
                v
       Dependency Resolution
                |
                v
        Architecture Graph
                |
                v
      External Validation Report
```

The ARXML parser extracts and resolves:

- Software component types
- Component instances
- Ports
- Interface definitions
- Assembly connectors
- Component dependencies

The extracted information is converted into the same common architecture representation used by downstream analysis components where applicable.

---

## Official AUTOSAR External Validation Results

The public AUTOSAR Workflow Example used for external validation produced:

```text
ARXML files processed       21
Parse errors                 0

Components                   8
Ports                       14
Active interfaces            3
Component instances          7
Assembly connectors          5

Resolved dependencies        4

Architecture graph nodes    13
Architecture graph edges    10

Overall validation        PASSED
```

Five assembly connectors map to four unique component-level dependencies because multiple connectors may resolve to the same component pair.

The resolved dependencies include:

```text
WhlSpdSnsr -> WhlSpdVirt

VehSpdVirt -> VehSpdActr

VehicleSpeedComposition -> WheelSpeedComposition

VehSpdActr -> VehSpdCalc
```

### Important Interpretation

The official AUTOSAR Workflow Example is used as public external AUTOSAR validation data.

It is **not** treated as:

- A production OEM HLD dataset
- A substitute for confidential automotive architecture documents
- Ground truth for the synthetic precision/recall benchmark

The external test demonstrates that the project can parse and map relevant structures from a public AUTOSAR artifact into the project's architecture representation.

Generalization to arbitrary OEM HLD layouts and ARXML configurations still depends on parser and document-layout coverage.

---

# Two Analysis Modes

The Streamlit interface provides two primary workflows.

## 1. HLD Document Analysis

```text
PDF
 ↓
Extraction / OCR
 ↓
Architecture Model
 ↓
Validation
 ↓
RAG
 ↓
Architecture Graph
 ↓
Engineer Review
```

This mode supports the main HLD document analysis workflow.

## 2. Official AUTOSAR External Validation

```text
ARXML ZIP
 ↓
Parsing
 ↓
Architecture Model
 ↓
Dependency Resolution
 ↓
Architecture Graph
 ↓
External Validation
```

This mode allows an official AUTOSAR Workflow Example ZIP to be uploaded and analyzed independently from the synthetic HLD benchmark.

---

# System Architecture

```text
                    AUTOSAR-Style HLD PDF
                             |
                             v
                     Document Ingestion
                   PyMuPDF / PDFPlumber
                             |
                    +--------+--------+
                    |                 |
                    v                 v
               Native Text        Scanned PDF
                                      |
                                 Tesseract OCR
                    |                 |
                    +--------+--------+
                             |
                             v
                    Structured Extraction
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
     Components          Interfaces           Ports
          |                  |                  |
          +------------------+------------------+
                             |
                      Signals / Dependencies
                             |
                +------------+------------+
                |                         |
                v                         v
       Consistency Checker          Functional Flow
                |                         |
                +------------+------------+
                             |
                             v
                    Architecture Graph
                             |
               +-------------+-------------+
               |                           |
               v                           v
       Revision Comparison             RAG Pipeline
                                           |
                                   Sentence Transformers
                                           |
                                       ChromaDB
                                           |
                                  Evidence Retrieval
                                           |
                                    Local Qwen LLM
                                           |
                              Grounded Answer + Source
                                           |
                                           v
                                    Engineer Review
                                           |
                                         SQLite
```

The project additionally supports an external AUTOSAR path:

```text
Official AUTOSAR ARXML ZIP
          |
          v
      ARXML Parser
          |
          v
Component / Interface / Port /
Instance / Connector Extraction
          |
          v
 Common Architecture Model
          |
          v
 Dependency Resolution
          |
          v
 Architecture Graph
          |
          v
 External Validation
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| UI | Streamlit |
| API | FastAPI |
| Local LLM | Qwen via Ollama |
| Embeddings | Sentence Transformers |
| Vector Database | ChromaDB |
| PDF Processing | PyMuPDF, PDFPlumber |
| OCR | Tesseract |
| AUTOSAR External Parsing | Python XML / ARXML processing |
| Graph Processing | NetworkX |
| Persistent Review Store | SQLite |
| Containerization | Docker / Docker Compose |
| Validation | Custom deterministic rules |

---

# Controlled Evaluation Results

The main architecture extraction benchmark uses a controlled synthetic AUTOSAR-style HLD corpus with known ground truth.

The controlled benchmark is kept separate from the official AUTOSAR external-validation experiment.

---

## Native PDF Architecture Extraction

Across five controlled synthetic native-PDF HLD documents:

```text
Components      Precision 1.000 | Recall 1.000 | F1 1.000
Interfaces      Precision 1.000 | Recall 1.000 | F1 1.000
Ports           Precision 1.000 | Recall 1.000 | F1 1.000
Signals         Precision 1.000 | Recall 1.000 | F1 1.000
Dependencies    Precision 1.000 | Recall 1.000 | F1 1.000
```

Overall:

```text
TP = 69
FP = 0
FN = 0

Micro-F1 = 1.000
```

These results apply only to the controlled synthetic native-PDF evaluation corpus.

They should **not** be interpreted as 100% accuracy on arbitrary automotive documents or production OEM HLDs.

---

## OCR Architecture Extraction

Across five controlled synthetic scanned HLDs:

```text
Precision = 0.985
Recall    = 0.928
Micro-F1  = 0.955

TP = 64
FP = 1
FN = 5
```

The OCR experiment demonstrates the effect of character-level OCR errors on downstream architecture extraction.

---

## Structural Validation

Two known structural defects were deliberately introduced into the controlled evaluation corpus.

Results:

```text
Injected defects detected: 2 / 2
False positives:            0
False negatives:            0
```

Examples include missing provider ports for defined interfaces.

---

## Revision Comparison

For the controlled Vehicle Control HLD V1 → V2 pair, the comparator identified all six known architecture changes:

```text
1. DiagnosticsManager component added

2. DiagnosticStatusInterface added

3. DiagnosticStatusIn R-Port added

4. WheelSpeed renamed to Wheel_Speed

5. DiagnosticStatus signal added

6. DiagnosticsManager dependency added
```

---

## Controlled RAG Benchmark

A ten-question benchmark was used to evaluate supported and unsupported questions.

```text
Evidence-supported questions: 6
Correct supported answers:     6 / 6

Unsupported questions:         4
Correct refusals:              4 / 4

Supported citation coverage:   6 / 6
Citation metadata validity:    6 / 6
```

Citation metadata validity verifies that retrieved source metadata/evidence is available.

It should not be interpreted as an independent semantic-entailment metric.

---

# Dataset Strategy

Production automotive HLDs are often proprietary and may contain confidential OEM architecture information.

For this reason, the primary controlled evaluation corpus consists of synthetic AUTOSAR-style HLD documents with known ground truth.

This allows deterministic measurement without relying on unauthorized confidential documents.

The repository includes controlled documents such as:

```text
Vehicle_Control_HLD_v1.pdf
Vehicle_Control_HLD_v2.pdf
Braking_System_HLD.pdf
Door_Control_HLD.pdf
Body_Control_HLD.pdf
```

Scanned versions are included for OCR evaluation.

Ground truth is stored in:

```text
data/ground_truth/architecture_ground_truth.json
```

The synthetic corpus enables controlled testing of:

- Entity extraction
- OCR robustness
- Structural validation
- Revision comparison
- RAG question answering

---

# Public AUTOSAR Data Strategy

Public AUTOSAR artifacts are used separately to provide external validation beyond the controlled synthetic corpus.

The project uses the official AUTOSAR Classic Platform Workflow Example as an external AUTOSAR reference artifact.

The official files themselves are intentionally not committed to this repository.

Instead, the repository provides instructions for obtaining the public artifact separately and the Streamlit application supports uploading the Workflow Example ZIP for validation.

This avoids presenting public AUTOSAR reference material as project-owned data and keeps the controlled synthetic benchmark clearly separated from external validation.

---

# Project Structure

```text
autosar-hld-ai-assistant/
│
├── app/
│   ├── api/
│   ├── comparison/
│   ├── database/
│   ├── evaluation/
│   ├── external_validation/
│   ├── extraction/
│   ├── graph/
│   ├── ingestion/
│   ├── models/
│   ├── rag/
│   ├── utils/
│   └── validation/
│
├── data/
│   ├── ground_truth/
│   ├── public_autosar/
│   └── sample_hlds/
│
├── scripts/
├── tests/
│
├── streamlit_app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
└── README.md
```

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/smera0609/autosar-hld-ai-assistant.git
cd autosar-hld-ai-assistant
```

---

## 2. Create a Python Environment

Windows:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

---

## 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

---

## 4. Install Tesseract OCR

Tesseract must be available on the system when scanned-document OCR is required.

---

## 5. Install Ollama

Install Ollama and make the required local Qwen model available before using LLM-based HLD question answering.

The prototype uses:

```text
qwen3:4b-instruct
```

---

# Running the Streamlit Application

Activate the virtual environment and run:

```powershell
streamlit run streamlit_app.py
```

The application provides both:

```text
HLD Document Analysis
```

and:

```text
Official AUTOSAR External Validation
```

modes.

---

# Running the FastAPI Backend

Run:

```powershell
python -m uvicorn app.api.main:app --reload
```

Swagger API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The backend exposes endpoints including:

```text
GET  /health

POST /extract

POST /validate

POST /functional-flow

POST /analyze
```

---

# Docker Compose Deployment

The project includes Docker Compose support for running the Streamlit UI and FastAPI backend as separate services.

Build and start the application:

```powershell
docker compose up --build
```

After startup:

```text
Streamlit UI
http://localhost:8501

FastAPI Swagger Documentation
http://localhost:8000/docs

FastAPI Health Endpoint
http://localhost:8000/health
```

The Docker environment includes the dependencies required by the application, including OCR support.

To stop the services:

```powershell
docker compose down
```

A full no-cache rebuild is normally unnecessary unless dependency-layer rebuilding is specifically required.

---

# API Layer

FastAPI provides programmatic access to the document-analysis functionality.

Available endpoints include:

```text
GET  /health
POST /extract
POST /validate
POST /functional-flow
POST /analyze
```

Swagger UI provides interactive endpoint documentation and testing.

---

# Streamlit Interface

The HLD analysis interface provides views for:

- Architecture overview
- Components
- Interfaces and signals
- Validation findings
- HLD question answering
- Architecture graph
- Revision comparison
- Engineer review

The external AUTOSAR validation interface provides views for:

- Components and ports
- Interfaces
- Connectors and dependencies
- Architecture graph
- Validation export

---

# Design Principles

## Evidence Grounding

LLM responses are generated from retrieved HLD evidence rather than unrestricted generation.

---

## Human-in-the-Loop Review

Automated findings remain subject to engineer acceptance or rejection.

The system assists engineering decisions rather than automatically approving them.

---

## Traceability

Architecture entities, dependencies, functional flows, retrieved evidence, validation findings, and engineer decisions remain available for inspection.

---

## Deterministic Validation Where Appropriate

Structural consistency checks use explicit engineering rules instead of relying entirely on an LLM.

This provides predictable behavior for checks that can be expressed deterministically.

---

## Local-First AI Architecture

The prototype uses:

- Local embeddings
- Local vector storage
- Locally hosted LLM inference

This architecture is suitable for environments where engineering documents should remain within controlled infrastructure.

---

## Separation of Controlled and External Evaluation

Synthetic HLD documents provide controlled ground truth.

Official public AUTOSAR artifacts provide separate external compatibility validation.

Results from these two evaluation settings are reported independently to avoid overstating generalization.

---

# Current Limitations

This project is a prototype rather than a production AUTOSAR engineering platform.

Current limitations include:

- The controlled HLD evaluation corpus is synthetic and relatively small.
- Controlled HLD layouts do not represent every production OEM document format.
- OCR errors can propagate into architecture extraction.
- Complex architecture diagrams are not yet interpreted using dedicated computer-vision models.
- RAG citation metadata validation is not equivalent to independent semantic-entailment verification.
- Official AUTOSAR external validation currently focuses on relevant ARXML structures such as components, ports, interfaces, instances, and assembly connectors.
- ARXML data-element/signal extraction is not yet included in the external-validation adapter.
- External validation uses a public AUTOSAR Workflow Example, not a production OEM HLD.
- Enterprise RBAC and project isolation are future deployment enhancements.
- Engineer validation remains necessary before findings are used for engineering decisions.

---

# Future Enhancements

Potential extensions include:

- Larger and more diverse HLD evaluation corpus
- Evaluation using authorized real-world automotive HLDs
- Additional ARXML structure coverage
- Data-element and signal extraction from ARXML
- Diagram-aware architecture extraction
- Extraction provenance at entity level
- Interactive impact analysis
- Graph-based architecture queries
- Cross-document architecture consistency checking
- Role-based access control
- Project/workspace isolation
- Container orchestration for enterprise deployment
- Integration with approved engineering repositories
- Expanded benchmark suite for grounded-answer evaluation

---

# Why This Is More Than a PDF Chatbot

The system does not simply send PDF text to an LLM.

It combines multiple engineering analysis mechanisms:

```text
Document Processing
        +
Structured Architecture Extraction
        +
Deterministic Consistency Validation
        +
Functional Flow Analysis
        +
Architecture Knowledge Graph
        +
Revision Comparison
        +
Evidence-Grounded RAG
        +
Human Engineer Review
        +
Official AUTOSAR ARXML External Validation
```

This hybrid architecture uses AI where semantic reasoning is useful while retaining deterministic processing for structural engineering checks.

---

# Evaluation Summary

```text
CONTROLLED SYNTHETIC HLD BENCHMARK

Native PDF entities evaluated        69
Native extraction Micro-F1        1.000

OCR extraction Precision          0.985
OCR extraction Recall             0.928
OCR extraction Micro-F1           0.955

Injected structural defects         2
Detected                            2
False positives                     0
False negatives                     0

Known revision changes              6
Detected                            6

Supported RAG questions             6
Correct                             6

Unsupported RAG questions           4
Correct refusals                    4

Citation coverage                 6/6
Citation metadata validity        6/6
```

Separate external validation:

```text
OFFICIAL AUTOSAR WORKFLOW EXAMPLE

ARXML files                         21
Parse errors                        0
Components                          8
Ports                              14
Active interfaces                   3
Component instances                 7
Assembly connectors                 5
Resolved dependencies               4
Graph nodes                        13
Graph edges                        10

External validation             PASSED
```

---

# Responsible Use

The system is intended as an engineering assistant.

It does not:

- Automatically approve an architecture
- Replace formal architecture governance
- Replace engineer review
- Modify production architecture documents without review

Architecture findings should be treated as engineering assistance and verified by qualified personnel before being used for production decisions.

---

# Disclaimer

This repository is an engineering prototype created for educational and technical demonstration purposes.

The included HLD documents are synthetic test documents and are not production OEM architecture documents.

Public AUTOSAR artifacts used for external validation are obtained separately from official public sources and are not presented as project-owned production data.

Automated findings should be reviewed by a qualified engineer before being used in an automotive engineering workflow.