from pydantic import BaseModel, Field


# =========================================================
# ARCHITECTURE ENTITY MODELS
# =========================================================

class Component(BaseModel):
    """
    AUTOSAR software component extracted from the HLD.
    """
    name: str
    description: str = ""


class Interface(BaseModel):
    """
    Interface connecting AUTOSAR software components.
    """
    name: str
    provider: str = ""
    consumer: str = ""


class Port(BaseModel):
    """
    AUTOSAR component port.

    P-Port = Provided Port
    R-Port = Required Port
    """
    component: str
    name: str
    port_type: str
    interface: str


class Signal(BaseModel):
    """
    Signal transmitted through an interface.
    """
    name: str
    interface: str
    unit: str = ""


class Dependency(BaseModel):
    """
    Dependency relationship between two components.
    """
    dependent_component: str
    required_component: str


# =========================================================
# COMPLETE ARCHITECTURE MODEL
# =========================================================

class ArchitectureModel(BaseModel):
    """
    Structured architecture representation extracted
    from one HLD document.
    """

    filename: str

    document_id: str = ""

    version: str = ""

    components: list[Component] = Field(
        default_factory=list
    )

    interfaces: list[Interface] = Field(
        default_factory=list
    )

    ports: list[Port] = Field(
        default_factory=list
    )

    signals: list[Signal] = Field(
        default_factory=list
    )

    dependencies: list[Dependency] = Field(
        default_factory=list
    )


# =========================================================
# VALIDATION MODEL
# =========================================================

class ValidationIssue(BaseModel):
    """
    Potential architecture inconsistency detected
    by deterministic validation rules.

    These findings require engineer review.
    """

    issue_type: str

    severity: str

    message: str

    entity: str = ""