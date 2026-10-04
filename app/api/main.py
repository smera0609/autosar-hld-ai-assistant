from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from app.extraction.pdf_architecture_extractor import (
    PDFArchitectureExtractor,
)

from app.validation.consistency_checker import (
    ConsistencyChecker,
)

from app.extraction.functional_flow_extractor import (
    FunctionalFlowExtractor,
)

from app.graph.architecture_graph import (
    ArchitectureGraph,
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="AUTOSAR HLD Intelligence API",
    description=(
        "Backend API for extracting, validating and "
        "analysing AUTOSAR-style High Level Design documents."
    ),
    version="1.0.0",
)


# =========================================================
# SERVICES
# =========================================================

architecture_extractor = PDFArchitectureExtractor()
consistency_checker = ConsistencyChecker()
flow_extractor = FunctionalFlowExtractor()


# =========================================================
# HELPERS
# =========================================================

def component_to_dict(component):
    return {
        "name": component.name,
        "description": component.description,
    }


def interface_to_dict(interface):
    return {
        "name": interface.name,
        "provider": interface.provider,
        "consumer": interface.consumer,
    }


def port_to_dict(port):
    return {
        "component": port.component,
        "name": port.name,
        "port_type": port.port_type,
        "interface": port.interface,
    }


def signal_to_dict(signal):
    return {
        "name": signal.name,
        "interface": signal.interface,
        "unit": signal.unit,
    }


def dependency_to_dict(dependency):
    return {
        "dependent_component": (
            dependency.dependent_component
        ),
        "required_component": (
            dependency.required_component
        ),
    }


def issue_to_dict(issue):
    return {
        "issue_type": issue.issue_type,
        "severity": issue.severity,
        "message": issue.message,
        "entity": issue.entity,
    }


def architecture_to_dict(architecture):
    return {
        "filename": architecture.filename,
        "document_id": architecture.document_id,
        "version": architecture.version,

        "components": [
            component_to_dict(item)
            for item in architecture.components
        ],

        "interfaces": [
            interface_to_dict(item)
            for item in architecture.interfaces
        ],

        "ports": [
            port_to_dict(item)
            for item in architecture.ports
        ],

        "signals": [
            signal_to_dict(item)
            for item in architecture.signals
        ],

        "dependencies": [
            dependency_to_dict(item)
            for item in architecture.dependencies
        ],
    }


def save_uploaded_pdf(
    upload: UploadFile,
):
    """
    Save the uploaded PDF to a temporary file.

    Returns the temporary path.
    """

    suffix = Path(
        upload.filename or ""
    ).suffix.lower()

    if suffix != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    temp_file = NamedTemporaryFile(
        delete=False,
        suffix=".pdf",
    )

    try:
        shutil.copyfileobj(
            upload.file,
            temp_file,
        )

    finally:
        temp_file.close()

    return Path(
        temp_file.name
    )


def remove_temp_file(path):
    try:
        Path(path).unlink(
            missing_ok=True
        )
    except Exception:
        pass


# =========================================================
# HEALTH
# =========================================================

@app.get("/")
def root():
    return {
        "service": (
            "AUTOSAR HLD Intelligence API"
        ),
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# =========================================================
# ARCHITECTURE EXTRACTION
# =========================================================

@app.post("/extract")
def extract_architecture(
    file: UploadFile = File(...),
):

    temp_path = save_uploaded_pdf(
        file
    )

    try:

        architecture = (
            architecture_extractor.extract(
                temp_path
            )
        )

        return {
            "status": "success",
            "architecture": (
                architecture_to_dict(
                    architecture
                )
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Architecture extraction failed: "
                f"{exc}"
            ),
        )

    finally:

        remove_temp_file(
            temp_path
        )


# =========================================================
# CONSISTENCY VALIDATION
# =========================================================

@app.post("/validate")
def validate_architecture(
    file: UploadFile = File(...),
):

    temp_path = save_uploaded_pdf(
        file
    )

    try:

        architecture = (
            architecture_extractor.extract(
                temp_path
            )
        )

        issues = (
            consistency_checker.validate(
                architecture
            )
        )

        return {
            "status": "success",
            "document": {
                "filename": (
                    file.filename
                ),
                "document_id": (
                    architecture.document_id
                ),
                "version": (
                    architecture.version
                ),
            },
            "issue_count": len(
                issues
            ),
            "issues": [
                issue_to_dict(issue)
                for issue in issues
            ],
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Validation failed: "
                f"{exc}"
            ),
        )

    finally:

        remove_temp_file(
            temp_path
        )


# =========================================================
# FUNCTIONAL FLOW
# =========================================================

@app.post("/functional-flow")
def functional_flow(
    file: UploadFile = File(...),
):

    temp_path = save_uploaded_pdf(
        file
    )

    try:

        flow = (
            flow_extractor.extract(
                temp_path
            )
        )

        return {
            "status": "success",
            "filename": (
                file.filename
            ),
            "functional_flow": flow,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Functional-flow extraction failed: "
                f"{exc}"
            ),
        )

    finally:

        remove_temp_file(
            temp_path
        )


# =========================================================
# COMPLETE DOCUMENT ANALYSIS
# =========================================================

@app.post("/analyze")
def analyze_document(
    file: UploadFile = File(...),
):

    temp_path = save_uploaded_pdf(
        file
    )

    try:

        # ---------------------------------------------
        # STRUCTURED ARCHITECTURE
        # ---------------------------------------------

        architecture = (
            architecture_extractor.extract(
                temp_path
            )
        )

        # ---------------------------------------------
        # CONSISTENCY CHECK
        # ---------------------------------------------

        issues = (
            consistency_checker.validate(
                architecture
            )
        )

        # ---------------------------------------------
        # FUNCTIONAL FLOW
        # ---------------------------------------------

        flow = (
            flow_extractor.extract(
                temp_path
            )
        )

        # ---------------------------------------------
        # KNOWLEDGE GRAPH
        # ---------------------------------------------

        graph_builder = (
            ArchitectureGraph()
        )

        graph = graph_builder.build(
            architecture,
            functional_flow=flow,
        )

        graph_summary = (
            graph_builder.summary(
                graph
            )
        )

        # ---------------------------------------------
        # RESPONSE
        # ---------------------------------------------

        return {
            "status": "success",

            "document": {
                "filename": (
                    file.filename
                ),
                "document_id": (
                    architecture.document_id
                ),
                "version": (
                    architecture.version
                ),
            },

            "architecture": (
                architecture_to_dict(
                    architecture
                )
            ),

            "validation": {
                "issue_count": len(
                    issues
                ),
                "issues": [
                    issue_to_dict(issue)
                    for issue in issues
                ],
            },

            "functional_flow": flow,

            "graph_summary": (
                graph_summary
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Document analysis failed: "
                f"{exc}"
            ),
        )

    finally:

        remove_temp_file(
            temp_path
        )