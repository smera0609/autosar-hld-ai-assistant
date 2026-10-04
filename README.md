# AUTOSAR HLD Intelligence & Validation Assistant

An AI-assisted engineering tool for analyzing AUTOSAR-style High-Level Design (HLD) documents.

The system converts automotive architecture documents into searchable and structured engineering knowledge by combining document processing, architecture extraction, consistency validation, Retrieval-Augmented Generation (RAG), knowledge graphs, revision comparison, OCR, and human review.

> This repository is a prototype built using synthetic AUTOSAR-style HLD documents for controlled evaluation. It is intended to assist engineers, not replace engineering review or architecture governance.

---

## Key Features

### HLD Document Ingestion
- Upload and process automotive HLD PDF documents
- Page-aware text extraction
- Section-aware document chunking
- Metadata preservation
- Native PDF and scanned PDF support

### OCR Support
Scanned documents are processed using Tesseract OCR when native text extraction is insufficient.

### Architecture Extraction
Extracts structured architecture entities including:

- Software Components
- Interfaces
- P-Ports and R-Ports
- Signals
- Component Dependencies
- Functional Flows

### Architecture Consistency Validation
Automatically checks for structural issues such as:

- Missing provider ports
- Missing consumer ports
- Undefined interfaces
- Unknown components
- Invalid dependencies
- Signal/interface inconsistencies

### Evidence-Grounded RAG

The assistant uses:

- Sentence Transformer embeddings
- ChromaDB vector storage
- Semantic retrieval
- Local Qwen LLM through Ollama
- Evidence-grounded prompting
- Page/source citation metadata

When the HLD does not contain sufficient evidence, the system is designed to respond:

> Insufficient evidence in the provided HLD.

This reduces unsupported answers instead of encouraging the model to guess.

### Architecture Knowledge Graph

Architecture relationships are reconstructed as a graph containing relationships such as:

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

This enables architecture traceability and dependency exploration.

### Functional Flow Extraction

Example:

```text
WheelSpeedSensor
        ↓
VehicleSpeedController
        ↓
InstrumentCluster
```

Functional flows are also incorporated into the architecture graph.

### Revision Comparison

The system compares HLD revisions and identifies architectural changes including:

- Added/removed components
- Added/removed interfaces
- Port changes
- Signal changes
- Dependency changes
- Signal renaming

### Engineer Review Workflow

Detected findings can be:

- Pending
- Accepted
- Rejected

Engineer decisions and comments are persisted using SQLite.

### FastAPI Backend

The project exposes API endpoints including:

```text
GET  /health
POST /extract
POST /validate
POST /functional-flow
POST /analyze
```

Interactive API documentation is available through Swagger UI.

### Streamlit Interface

The user interface provides views for:

- Architecture overview
- Components
- Interfaces and signals
- Validation findings
- HLD question answering
- Architecture graph
- Revision comparison
- Engineer review

---

## System Architecture

```text
                     AUTOSAR-Style HLD PDF
                              |
                              v
                    Document Ingestion
                  PyMuPDF / PDFPlumber
                              |
                    +---------+---------+
                    |                   |
               Native Text          Scanned PDF
                    |                   |
                    |              Tesseract OCR
                    |                   |
                    +---------+---------+
                              |
                              v
                    Structured Extraction
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
     Components          Interfaces            Ports
          |                   |                   |
          +-------------------+-------------------+
                              |
                       Signals / Dependencies
                              |
               +--------------+--------------+
               |                             |
               v                             v
       Consistency Checker            Functional Flow
               |                             |
               +--------------+--------------+
                              |
                              v
                    Architecture Graph
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
      Revision Comparison                  RAG Pipeline
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

---

## Technology Stack

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
| Graph Processing | NetworkX |
| Persistent Review Store | SQLite |
| Containerization | Docker |
| Validation | Custom deterministic rules |

---

## Controlled Evaluation Results

The project includes a synthetic AUTOSAR-style HLD corpus with known ground truth.

### Native PDF Architecture Extraction

Across five controlled synthetic native-PDF HLD documents:

```text
Components      Precision 1.000 | Recall 1.000 | F1 1.000
Interfaces      Precision 1.000 | Recall 1.000 | F1 1.000
Ports           Precision 1.000 | Recall 1.000 | F1 1.000
Signals         Precision 1.000 | Recall 1.000 | F1 1.000
Dependencies    Precision 1.000 | Recall 1.000 | F1 1.000

Overall:
TP = 69
FP = 0
FN = 0
Micro-F1 = 1.000
```

These results apply only to the controlled synthetic evaluation corpus and should not be interpreted as general accuracy on arbitrary automotive documents.

### OCR Architecture Extraction

Across five controlled synthetic scanned HLDs:

```text
Precision = 0.985
Recall    = 0.928
Micro-F1  = 0.955

TP = 64
FP = 1
FN = 5
```

The remaining OCR errors primarily demonstrate the impact of character-level OCR corruption on architecture entity extraction.

### Structural Validation

Two known structural defects were deliberately introduced into the controlled corpus.

```text
Injected defects detected: 2 / 2
False positives:            0
False negatives:            0
```

Examples include missing provider ports for defined interfaces.

### Revision Comparison

For the controlled Vehicle Control HLD V1 → V2 pair, the comparator identified all six known architecture changes:

```text
1. DiagnosticsManager component added
2. DiagnosticStatusInterface added
3. DiagnosticStatusIn R-Port added
4. WheelSpeed renamed to Wheel_Speed
5. DiagnosticStatus signal added
6. DiagnosticsManager dependency added
```

### Controlled RAG Benchmark

A 10-question benchmark was used:

```text
Evidence-supported questions: 6
Correct supported answers:    6 / 6

Unsupported questions:        4
Correct refusals:             4 / 4

Supported citation coverage:  6 / 6
Citation metadata validity:   6 / 6
```

The citation validity measurement verifies source metadata/evidence availability; it is not an independent semantic-entailment metric.

---

## Dataset

The repository contains synthetic AUTOSAR-style HLD documents designed specifically for prototype development and controlled evaluation.

Documents include:

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

The synthetic corpus avoids dependence on confidential OEM architecture documents while allowing deterministic evaluation against known architecture entities and injected defects.

---

## Project Structure

```text
autosar-hld-ai-assistant/
│
├── app/
│   ├── api/
│   ├── comparison/
│   ├── database/
│   ├── evaluation/
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
│   └── sample_hlds/
│
├── scripts/
├── tests/
│
├── streamlit_app.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/smera0609/autosar-hld-ai-assistant.git
cd autosar-hld-ai-assistant
```

### 2. Create a Python environment

Windows:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Install Tesseract OCR

Tesseract must be available on the system for scanned-document OCR.

### 5. Install Ollama

Install Ollama and make the required local Qwen model available before using LLM-based HLD Q&A.

The prototype uses:

```text
qwen3:4b-instruct
```

---

## Running the Streamlit Application

```powershell
streamlit run streamlit_app.py
```

---

## Running the FastAPI Backend

```powershell
python -m uvicorn app.api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

---

## Docker Deployment

Build the image:

```bash
docker build -t autosar-hld-assistant .
```

Run the container:

```bash
docker run --name autosar-hld-container -p 8000:8000 autosar-hld-assistant
```

Health endpoint:

```text
http://localhost:8000/health
```

Swagger API documentation:

```text
http://localhost:8000/docs
```

The Docker image includes Tesseract OCR support.

---

## Design Principles

The system follows several important engineering principles:

**Evidence grounding**  
LLM responses are generated from retrieved HLD evidence rather than unrestricted generation.

**Human-in-the-loop review**  
Automated findings remain subject to engineer acceptance or rejection.

**Traceability**  
Architecture entities, dependencies, functional flows and retrieved evidence are retained for inspection.

**Deterministic validation where appropriate**  
Structural consistency checks use explicit rules instead of relying entirely on an LLM.

**Local-first AI architecture**  
The prototype uses local embeddings, local vector storage and a locally hosted LLM.

---

## Current Limitations

This is a prototype rather than a production AUTOSAR engineering platform.

Current limitations include:

- Evaluation corpus is synthetic and relatively small.
- HLD layouts are controlled and do not represent every real OEM document format.
- OCR errors can propagate into architecture extraction.
- Complex diagrams are not yet interpreted using dedicated computer-vision models.
- RAG citation metadata validation is not equivalent to independent semantic entailment verification.
- Enterprise RBAC and project isolation are future deployment enhancements.
- Engineer validation remains necessary before findings are used for engineering decisions.

---

## Future Enhancements

Potential extensions include:

- Larger and more diverse HLD evaluation corpus
- Diagram-aware architecture extraction
- Extraction provenance at entity level
- Interactive impact analysis
- Graph-based architecture queries
- Cross-document architecture consistency checking
- Role-based access control
- Project/workspace isolation
- Container orchestration for enterprise deployment
- Integration with approved engineering repositories

---

## Disclaimer

This repository is an engineering prototype created for educational and technical demonstration purposes.

The included HLD documents are synthetic test documents and are not production OEM architecture documents. Automated findings should be reviewed by a qualified engineer before being used in an automotive engineering workflow.