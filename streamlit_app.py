from pathlib import Path

import csv

import io

import json

import tempfile

from datetime import datetime



import streamlit as st



from app.ingestion.document_processor import DocumentProcessor

from app.extraction.pdf_architecture_extractor import PDFArchitectureExtractor
from app.extraction.functional_flow_extractor import FunctionalFlowExtractor

from app.validation.consistency_checker import ConsistencyChecker



from app.rag.vector_store import HLDVectorStore

from app.rag.retriever import HLDRetriever

from app.rag.answer_engine import GroundedAnswerEngine

from app.rag.ollama_provider import OllamaProvider



from app.graph.architecture_graph import ArchitectureGraph

from app.comparison.revision_comparator import RevisionComparator
from app.database.review_store import ReviewStore





# =========================================================

# PAGE CONFIGURATION

# =========================================================



st.set_page_config(

    page_title="AUTOSAR HLD Intelligence Assistant",

    page_icon="🚗",

    layout="wide",

)





# =========================================================

# SESSION STATE

# =========================================================



DEFAULT_STATE = {

    "document": None,

    "chunks": [],

    "architecture": None,

    "issues": [],

    "functional_flow": None,

    "uploaded_filename": None,

    "rag_ready": False,

    "last_answer": None,

    "revision_comparison": None,

    "comparison_architecture": None,

    "review_decisions": {},

    "review_comments": {},

}



for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value





# =========================================================

# HEADER

# =========================================================



st.title("AUTOSAR HLD Intelligence Assistant")



st.caption(

    "Evidence-grounded architecture extraction, validation, "

    "traceability and document intelligence."

)



st.info(

    "AI-assisted engineering prototype. "

    "Generated findings require engineer review."

)





# =========================================================

# SIDEBAR

# =========================================================



with st.sidebar:



    st.header("Project Workspace")



    st.write(

        "Upload an AUTOSAR-style High Level Design document "

        "for architecture analysis."

    )



    uploaded_file = st.file_uploader(

        "Upload HLD",

        type=["pdf"],

        key="main_hld_upload",

    )



    analyse_button = st.button(

        "Analyze Document",

        type="primary",

        use_container_width=True,

    )



    st.divider()



    st.subheader("Analysis Pipeline")



    st.write(

        "PDF → Extraction → Architecture Model → "

        "Validation → RAG → Engineer Review"

    )



    if st.session_state.rag_ready:

        st.success("RAG knowledge base ready")





# =========================================================

# DOCUMENT ANALYSIS

# =========================================================



if analyse_button:



    if uploaded_file is None:



        st.warning("Please upload an HLD PDF first.")



    else:



        with st.spinner(

            "Analyzing and indexing HLD document..."

        ):



            temp_path = None



            try:



                # -----------------------------------------

                # SAVE PDF TEMPORARILY

                # -----------------------------------------



                with tempfile.NamedTemporaryFile(

                    delete=False,

                    suffix=".pdf",

                ) as temp_file:



                    temp_file.write(

                        uploaded_file.getbuffer()

                    )



                    temp_path = Path(temp_file.name)



                # -----------------------------------------

                # DOCUMENT INGESTION

                # -----------------------------------------



                processor = DocumentProcessor()



                document = processor.parser.parse(

                    temp_path

                )



                document.filename = uploaded_file.name



                chunks = (

                    processor.chunker.chunk_document(

                        document

                    )

                )



                for chunk in chunks:

                    chunk.filename = uploaded_file.name



                # -----------------------------------------

                # ARCHITECTURE EXTRACTION

                # -----------------------------------------



                extractor = PDFArchitectureExtractor()



                architecture = extractor.extract(

                    temp_path

                )



                architecture.filename = uploaded_file.name



                # -----------------------------------------

                # FUNCTIONAL FLOW EXTRACTION

                # -----------------------------------------



                flow_extractor = FunctionalFlowExtractor()



                functional_flow = flow_extractor.extract(

                    temp_path

                )



                functional_flow["filename"] = uploaded_file.name



                # -----------------------------------------

                # CONSISTENCY VALIDATION

                # -----------------------------------------



                checker = ConsistencyChecker()



                issues = checker.validate(

                    architecture

                )



                # -----------------------------------------

                # VECTOR INDEXING

                # -----------------------------------------



                vector_store = HLDVectorStore()



                indexed_count = vector_store.add_chunks(

                    chunks

                )



                if indexed_count == 0:

                    raise RuntimeError(

                        "No document chunks were indexed."

                    )



                # -----------------------------------------

                # STORE RESULTS

                # -----------------------------------------



                st.session_state.document = document

                st.session_state.chunks = chunks

                st.session_state.architecture = architecture

                st.session_state.issues = issues

                st.session_state.functional_flow = functional_flow



                st.session_state.uploaded_filename = (

                    uploaded_file.name

                )



                st.session_state.rag_ready = True

                st.session_state.last_answer = None



                # Clear previous comparison/review

                st.session_state.revision_comparison = None

                st.session_state.comparison_architecture = None



                st.session_state.review_decisions = {}

                st.session_state.review_comments = {}



                st.success(

                    "HLD analysis and RAG indexing "

                    "completed successfully."

                )



            except Exception as exc:



                st.session_state.rag_ready = False



                st.error(

                    f"HLD analysis failed: {exc}"

                )



            finally:



                if (

                    temp_path is not None

                    and temp_path.exists()

                ):



                    try:

                        temp_path.unlink()



                    except OSError:

                        pass





# =========================================================

# GET CURRENT RESULTS

# =========================================================



document = st.session_state.document

chunks = st.session_state.chunks

architecture = st.session_state.architecture

issues = st.session_state.issues

functional_flow = st.session_state.functional_flow





# =========================================================

# EMPTY STATE

# =========================================================



if document is None or architecture is None:



    st.subheader("No document analyzed")



    st.write(

        "Upload an HLD PDF from the sidebar "

        "and click **Analyze Document**."

    )



    st.stop()





# =========================================================

# DOCUMENT OVERVIEW

# =========================================================



st.header("Document Overview")



col1, col2, col3, col4 = st.columns(4)



col1.metric(

    "Pages",

    document.page_count,

)



col2.metric(

    "Components",

    len(architecture.components),

)



col3.metric(

    "Interfaces",

    len(architecture.interfaces),

)



col4.metric(

    "Validation Issues",

    len(issues),

)



display_filename = (

    st.session_state.uploaded_filename

    or architecture.filename

)



st.caption(

    f"Analyzed document: {display_filename}"

)





# =========================================================

# TABS

# =========================================================



(

    overview_tab,

    components_tab,

    interfaces_tab,

    validation_tab,

    qa_tab,

    graph_tab,

    comparison_tab,

    review_tab,

) = st.tabs(

    [

        "Overview",

        "Components",

        "Interfaces & Signals",

        "Validation",

        "Ask HLD",

        "Architecture Graph",

        "Revision Comparison",

        "Engineer Review",

    ]

)





# =========================================================

# OVERVIEW TAB

# =========================================================



with overview_tab:



    st.subheader("Architecture Summary")



    m1, m2, m3, m4 = st.columns(4)



    m1.metric(

        "Components",

        len(architecture.components),

    )



    m2.metric(

        "Ports",

        len(architecture.ports),

    )



    m3.metric(

        "Interfaces",

        len(architecture.interfaces),

    )



    m4.metric(

        "Signals",

        len(architecture.signals),

    )



    st.divider()



    st.subheader("Document Information")



    info1, info2, info3 = st.columns(3)



    with info1:



        st.write("**Document ID**")



        st.write(

            architecture.document_id

            or "Not specified"

        )



    with info2:



        st.write("**Version**")



        st.write(

            architecture.version

            or "Not specified"

        )



    with info3:



        st.write("**Filename**")



        st.write(display_filename)



    st.divider()



    st.subheader("Processing Summary")



    st.write(

        f"**Pages processed:** "

        f"{document.page_count}"

    )



    st.write(

        f"**Document chunks created:** "

        f"{len(chunks)}"

    )



    st.write(

        f"**Architecture dependencies:** "

        f"{len(architecture.dependencies)}"

    )



    st.write(

        f"**Potential validation issues:** "

        f"{len(issues)}"

    )



    if st.session_state.rag_ready:



        st.success(

            "Document indexed in local "

            "ChromaDB knowledge base."

        )





# =========================================================

# COMPONENTS TAB

# =========================================================



with components_tab:



    st.subheader(

        "Extracted Software Components"

    )



    if architecture.components:



        component_data = []



        for component in architecture.components:



            component_data.append(

                {

                    "Component": component.name,

                    "Description": component.description,

                }

            )



        st.dataframe(

            component_data,

            use_container_width=True,

            hide_index=True,

        )



    else:



        st.warning(

            "No software components were extracted."

        )



    st.divider()



    st.subheader("Extracted Ports")



    if architecture.ports:



        port_data = []



        for port in architecture.ports:



            port_data.append(

                {

                    "Component": port.component,

                    "Port": port.name,

                    "Port Type": port.port_type,

                    "Interface": port.interface,

                }

            )



        st.dataframe(

            port_data,

            use_container_width=True,

            hide_index=True,

        )



    else:



        st.warning(

            "No ports were extracted."

        )





# =========================================================

# INTERFACES & SIGNALS TAB

# =========================================================



with interfaces_tab:



    st.subheader("Extracted Interfaces")



    if architecture.interfaces:



        interface_data = []



        for interface in architecture.interfaces:



            interface_data.append(

                {

                    "Interface": interface.name,

                    "Provider":

                        interface.provider

                        or "Not specified",

                    "Consumer":

                        interface.consumer

                        or "Not specified",

                }

            )



        st.dataframe(

            interface_data,

            use_container_width=True,

            hide_index=True,

        )



    else:



        st.warning(

            "No interfaces were extracted."

        )



    st.divider()



    st.subheader("Extracted Signals")



    if architecture.signals:



        signal_data = []



        for signal in architecture.signals:



            signal_data.append(

                {

                    "Signal": signal.name,

                    "Interface": signal.interface,

                    "Unit":

                        signal.unit

                        or "Not specified",

                }

            )



        st.dataframe(

            signal_data,

            use_container_width=True,

            hide_index=True,

        )



    else:



        st.warning(

            "No signals were extracted."

        )



    st.divider()



    st.subheader("Component Dependencies")



    if architecture.dependencies:



        dependency_data = []



        for dependency in architecture.dependencies:



            dependency_data.append(

                {

                    "Dependent Component":

                        dependency.dependent_component,

                    "Required Component":

                        dependency.required_component,

                }

            )



        st.dataframe(

            dependency_data,

            use_container_width=True,

            hide_index=True,

        )



    else:



        st.info(

            "No component dependencies were extracted."

        )





# =========================================================

# VALIDATION TAB

# =========================================================



with validation_tab:



    st.subheader(

        "Architecture Consistency Checks"

    )



    st.write(

        "Deterministic validation checks identify "

        "potential architecture inconsistencies "

        "for engineer review."

    )



    if not issues:



        st.success(

            "No deterministic consistency issues "

            "were detected in this document."

        )



    else:



        st.warning(

            f"{len(issues)} potential issue(s) detected."

        )



        for number, issue in enumerate(

            issues,

            start=1,

        ):



            with st.expander(

                f"Issue {number}: "

                f"{issue.issue_type}"

            ):



                st.write(

                    f"**Severity:** "

                    f"{issue.severity}"

                )



                st.write(

                    f"**Entity:** "

                    f"{issue.entity or 'Not specified'}"

                )



                st.write(

                    f"**Finding:** "

                    f"{issue.message}"

                )





# =========================================================

# ASK HLD TAB

# =========================================================



with qa_tab:



    st.subheader(

        "Ask Questions About the HLD"

    )



    st.write(

        "Ask natural-language questions about "

        "the uploaded architecture document. "

        "Answers are generated only from "

        "retrieved HLD evidence."

    )



    question = st.text_input(

        "Architecture question",

        placeholder=(

            "Example: Which component processes "

            "wheel speed information?"

        ),

        key="hld_question",

    )



    ask_button = st.button(

        "Ask HLD",

        type="primary",

        key="ask_hld_button",

    )



    if ask_button:



        if not question.strip():



            st.warning(

                "Enter a question first."

            )



        else:



            with st.spinner(

                "Retrieving HLD evidence "

                "and generating answer..."

            ):



                try:



                    vector_store = HLDVectorStore()



                    retriever = HLDRetriever(

                        vector_store=vector_store

                    )



                    llm = OllamaProvider(

                        model="qwen3:4b-instruct"

                    )



                    answer_engine = (

                        GroundedAnswerEngine(

                            retriever=retriever,

                            llm_provider=llm,

                        )

                    )



                    result = answer_engine.answer(

                        question=question,

                        filename=display_filename,

                        top_k=3,

                    )



                    st.session_state.last_answer = result



                except Exception as exc:



                    st.error(

                        f"Question answering failed: {exc}"

                    )



    result = st.session_state.last_answer



    if result is not None:



        st.divider()



        st.subheader("Answer")



        insufficient_answer = (

            "insufficient evidence"

            in result.answer.lower()

            or

            "insufficient document evidence"

            in result.answer.lower()

        )



        if insufficient_answer:



            st.warning(result.answer)



        else:



            st.success(result.answer)



        st.caption(

            f"Mode: {result.mode}"

        )



        if (

            result.citations

            and not insufficient_answer

        ):



            st.subheader("Source Evidence")



            for citation in result.citations:



                label = (

                    f"Source {citation.citation_id} — "

                    f"{citation.filename}, "

                    f"Page {citation.page_number}"

                )



                with st.expander(label):



                    st.write(

                        f"**Chunk ID:** "

                        f"{citation.chunk_id}"

                    )



                    st.write("**Evidence:**")



                    st.write(

                        citation.excerpt

                    )



        elif insufficient_answer:



            st.info(

                "Retrieved context did not contain "

                "sufficient evidence to support an answer."

            )





# =========================================================

# ARCHITECTURE GRAPH TAB

# =========================================================



with graph_tab:



    st.subheader(

        "Architecture Knowledge Graph"

    )



    st.write(

        "Visual representation of components, "

        "interfaces, signals, dependencies and "

        "functional flow extracted from the HLD."

    )



    graph_builder = ArchitectureGraph()



    architecture_graph = graph_builder.build(

        architecture,

        functional_flow,

    )



    graph_summary = graph_builder.summary(

        architecture_graph

    )



    g1, g2, g3, g4 = st.columns(4)



    g1.metric(

        "Nodes",

        graph_summary["nodes"],

    )



    g2.metric(

        "Relationships",

        graph_summary["edges"],

    )



    g3.metric(

        "Components",

        graph_summary[

            "node_types"

        ].get(

            "component",

            0,

        ),

    )



    g4.metric(

        "Interfaces",

        graph_summary[

            "node_types"

        ].get(

            "interface",

            0,

        ),

    )



    st.divider()



    st.subheader(

        "Architecture Relationships"

    )



    graphviz_lines = [

        "digraph AUTOSAR {",

        'rankdir="LR";',

        'graph [pad="0.5", nodesep="0.7", ranksep="1"];',

    ]



    # -----------------------------------------

    # NODES

    # -----------------------------------------



    for node, attributes in (

        architecture_graph.nodes(

            data=True

        )

    ):



        node_type = attributes.get(

            "node_type",

            "unknown",

        )



        display_label = attributes.get(

            "label",

            node,

        )



        safe_node = (

            str(node)

            .replace('"', '\\\\"')

        )



        safe_label = (

            str(display_label)

            .replace('"', '\\\\"')

        )



        if node_type == "component":



            graphviz_lines.append(

                f'"{safe_node}" '

                f'[label="{safe_label}\\\nComponent", '

                f'shape="box"];'

            )



        elif node_type == "interface":



            graphviz_lines.append(

                f'"{safe_node}" '

                f'[label="{safe_label}\\\nInterface", '

                f'shape="ellipse"];'

            )



        elif node_type == "signal":



            unit = attributes.get(

                "unit",

                "",

            )



            signal_label = safe_label



            if unit:



                safe_unit = (

                    str(unit)

                    .replace('"', '\\\\"')

                )



                signal_label += (

                    f"\\\n[{safe_unit}]"

                )



            graphviz_lines.append(

                f'"{safe_node}" '

                f'[label="{signal_label}\\\nSignal", '

                f'shape="diamond"];'

            )



        else:



            graphviz_lines.append(

                f'"{safe_node}" '

                f'[label="{safe_label}"];'

            )



    # -----------------------------------------

    # EDGES

    # -----------------------------------------



    for (

        source,

        target,

        attributes,

    ) in architecture_graph.edges(

        data=True

    ):



        relationship = attributes.get(

            "relationship",

            "",

        )



        safe_source = (

            str(source)

            .replace('"', '\\\\"')

        )



        safe_target = (

            str(target)

            .replace('"', '\\\\"')

        )



        safe_relationship = (

            str(relationship)

            .replace('"', '\\\\"')

        )



        graphviz_lines.append(

            f'"{safe_source}" -> '

            f'"{safe_target}" '

            f'[label="{safe_relationship}"];'

        )



    graphviz_lines.append("}")



    graphviz_code = "\n".join(

        graphviz_lines

    )



    st.graphviz_chart(

        graphviz_code,

        use_container_width=True,

    )



    st.caption(

        "Boxes = Components | "

        "Ellipses = Interfaces | "

        "Diamonds = Signals | "

        "FLOWS_TO = Functional Flow"

    )



    st.divider()



    st.subheader("Functional Flow")



    if functional_flow and functional_flow.get("nodes"):

        st.info(" → ".join(functional_flow["nodes"]))

        flow_rows = []

        for number, (source, target) in enumerate(

            functional_flow["edges"],

            start=1,

        ):

            flow_rows.append(

                {

                    "Step": number,

                    "Source Component": source,

                    "Target Component": target,

                    "Relationship": "FLOWS_TO",

                }

            )

        st.dataframe(

            flow_rows,

            use_container_width=True,

            hide_index=True,

        )

    else:

        st.info(

            "No structured functional flow was detected in this HLD."

        )



    st.divider()



    st.subheader(

        "Relationship Summary"

    )



    relationship_data = []



    for relationship, count in (

        graph_summary[

            "relationships"

        ].items()

    ):



        relationship_data.append(

            {

                "Relationship": relationship,

                "Count": count,

            }

        )



    if relationship_data:



        st.dataframe(

            relationship_data,

            use_container_width=True,

            hide_index=True,

        )



    st.divider()



    st.subheader(

        "Component Traceability"

    )



    component_names = [

        component.name

        for component

        in architecture.components

    ]



    if component_names:



        selected_component = st.selectbox(

            "Select component",

            component_names,

            key="graph_component",

        )



        neighbors = (

            graph_builder.component_neighbors(

                architecture_graph,

                selected_component,

            )

        )



        incoming_col, outgoing_col = (

            st.columns(2)

        )



        with incoming_col:



            st.markdown(

                "#### Incoming Relationships"

            )



            if neighbors["incoming"]:



                st.dataframe(

                    [

                        {

                            "Entity":

                                item["entity"],

                            "Relationship":

                                item["relationship"],

                        }

                        for item

                        in neighbors["incoming"]

                    ],

                    use_container_width=True,

                    hide_index=True,

                )



            else:



                st.info(

                    "No incoming relationships."

                )



        with outgoing_col:



            st.markdown(

                "#### Outgoing Relationships"

            )



            if neighbors["outgoing"]:



                st.dataframe(

                    [

                        {

                            "Entity":

                                item["entity"],

                            "Relationship":

                                item["relationship"],

                        }

                        for item

                        in neighbors["outgoing"]

                    ],

                    use_container_width=True,

                    hide_index=True,

                )



            else:



                st.info(

                    "No outgoing relationships."

                )





    st.divider()

    st.subheader("Graph Export")

    graph_export = graph_builder.export_json(architecture_graph)
    graph_export["functional_flow"] = functional_flow or {}

    graph_json = json.dumps(
        graph_export,
        indent=2,
        ensure_ascii=False,
    )

    graph_filename = (
        Path(display_filename).stem.replace(" ", "_")
        + "_architecture_graph.json"
    )

    st.download_button(
        "Download Architecture Graph JSON",
        data=graph_json,
        file_name=graph_filename,
        mime="application/json",
        use_container_width=True,
    )



# =========================================================

# REVISION COMPARISON TAB

# =========================================================



with comparison_tab:



    st.subheader(

        "HLD Revision Comparison"

    )



    st.write(

        "Compare the currently analyzed HLD "

        "with a newer revision to identify "

        "architecture changes."

    )



    st.info(

        f"Base revision: {display_filename}"

    )



    newer_revision = st.file_uploader(

        "Upload newer HLD revision",

        type=["pdf"],

        key="revision_comparison_file",

    )



    if newer_revision is not None:



        st.caption(

            f"New revision selected: "

            f"{newer_revision.name}"

        )



        compare_button = st.button(

            "Compare Revisions",

            type="primary",

            key="compare_revisions_button",

        )



        if compare_button:



            comparison_temp_path = None



            with st.spinner(

                "Extracting and comparing "

                "HLD revisions..."

            ):



                try:



                    with tempfile.NamedTemporaryFile(

                        delete=False,

                        suffix=".pdf",

                    ) as comparison_temp:



                        comparison_temp.write(

                            newer_revision.getbuffer()

                        )



                        comparison_temp_path = Path(

                            comparison_temp.name

                        )



                    comparison_extractor = (

                        PDFArchitectureExtractor()

                    )



                    new_architecture = (

                        comparison_extractor.extract(

                            comparison_temp_path

                        )

                    )



                    new_architecture.filename = (

                        newer_revision.name

                    )



                    comparator = RevisionComparator()



                    comparison = comparator.compare(

                        architecture,

                        new_architecture,

                    )



                    st.session_state[

                        "revision_comparison"

                    ] = comparison



                    st.session_state[

                        "comparison_architecture"

                    ] = new_architecture



                    # New comparison means new review queue

                    st.session_state.review_decisions = {}

                    st.session_state.review_comments = {}



                    st.success(

                        "Revision comparison completed."

                    )



                except Exception as exc:



                    st.error(

                        f"Revision comparison failed: "

                        f"{exc}"

                    )



                finally:



                    if (

                        comparison_temp_path

                        is not None

                        and

                        comparison_temp_path.exists()

                    ):



                        try:

                            comparison_temp_path.unlink()



                        except OSError:

                            pass



    comparison = st.session_state.get(

        "revision_comparison"

    )



    if comparison is None:



        st.caption(

            "Upload a newer HLD revision above "

            "to run the comparison."

        )



    else:



        st.divider()



        st.subheader(

            "Comparison Summary"

        )



        c1, c2, c3 = st.columns(3)



        c1.metric(

            "Base Version",

            comparison.old_version

            or "Not specified",

        )



        c2.metric(

            "New Version",

            comparison.new_version

            or "Not specified",

        )



        c3.metric(

            "Total Changes",

            comparison.total_changes,

        )



        added_count = sum(

            1

            for change in comparison.changes

            if change.change_type == "ADDED"

        )



        removed_count = sum(

            1

            for change in comparison.changes

            if change.change_type == "REMOVED"

        )



        renamed_count = sum(

            1

            for change in comparison.changes

            if change.change_type == "RENAMED"

        )



        modified_count = sum(

            1

            for change in comparison.changes

            if change.change_type == "MODIFIED"

        )



        m1, m2, m3, m4 = st.columns(4)



        m1.metric(

            "Added",

            added_count,

        )



        m2.metric(

            "Removed",

            removed_count,

        )



        m3.metric(

            "Renamed",

            renamed_count,

        )



        m4.metric(

            "Modified",

            modified_count,

        )



        st.divider()



        st.subheader(

            "Detected Architecture Changes"

        )



        if comparison.changes:



            change_rows = []



            for change in comparison.changes:



                change_rows.append(

                    {

                        "Category":

                            change.category,

                        "Change Type":

                            change.change_type,

                        "Entity":

                            change.entity,

                        "Description":

                            change.description,

                    }

                )



            st.dataframe(

                change_rows,

                use_container_width=True,

                hide_index=True,

            )



            for number, change in enumerate(

                comparison.changes,

                start=1,

            ):



                with st.expander(

                    f"Change {number}: "

                    f"{change.category} / "

                    f"{change.change_type} — "

                    f"{change.entity}"

                ):



                    st.write(

                        f"**Category:** "

                        f"{change.category}"

                    )



                    st.write(

                        f"**Change Type:** "

                        f"{change.change_type}"

                    )



                    st.write(

                        f"**Entity:** "

                        f"{change.entity}"

                    )



                    st.write(

                        f"**Details:** "

                        f"{change.description}"

                    )



            st.warning(

                "Detected revision changes require "

                "engineer review before architecture "

                "decisions are approved."

            )



        else:



            st.success(

                "No structured architecture changes "

                "were detected between the revisions."

            )





# =========================================================

# ENGINEER REVIEW TAB

# =========================================================



with review_tab:



    st.subheader(

        "Engineer Review & Approval"

    )



    st.write(

        "Review validation findings and revision "

        "changes. AI-generated findings are not "

        "automatically approved."

    )



    review_items = []



    # -----------------------------------------

    # VALIDATION FINDINGS

    # -----------------------------------------



    for number, issue in enumerate(

        issues,

        start=1,

    ):



        review_items.append(

            {

                "id":

                    f"validation-{number}",

                "source":

                    "Validation",

                "category":

                    issue.issue_type,

                "entity":

                    issue.entity

                    or "Not specified",

                "severity":

                    issue.severity,

                "description":

                    issue.message,

            }

        )



    # -----------------------------------------

    # REVISION FINDINGS

    # -----------------------------------------



    current_comparison = (

        st.session_state.get(

            "revision_comparison"

        )

    )



    if current_comparison is not None:



        for number, change in enumerate(

            current_comparison.changes,

            start=1,

        ):



            review_items.append(

                {

                    "id":

                        f"revision-{number}",

                    "source":

                        "Revision Comparison",

                    "category":

                        f"{change.category} "

                        f"{change.change_type}",

                    "entity":

                        change.entity,

                    "severity":

                        "Review",

                    "description":

                        change.description,

                }

            )



    decisions = (

        st.session_state.review_decisions

    )



    comments = (

        st.session_state.review_comments

    )



    # -----------------------------------------

    # LOAD PERSISTED SQLITE REVIEWS

    # -----------------------------------------



    review_store = ReviewStore(

        "data/reviews.db"

    )



    persisted_reviews = (

        review_store.get_reviews(

            display_filename

        )

    )



    persisted_by_id = {

        row["finding_id"]: row

        for row in persisted_reviews

    }



    for item in review_items:



        saved_review = (

            persisted_by_id.get(

                item["id"]

            )

        )



        if saved_review is not None:

            decisions[item["id"]] = (

                saved_review["decision"]

            )

            comments[item["id"]] = (

                saved_review["comment"]

                or ""

            )



    # -----------------------------------------

    # INITIALIZE REVIEW STATUS

    # -----------------------------------------



    valid_ids = {

        item["id"]

        for item in review_items

    }



    for stored_id in list(decisions):



        if stored_id not in valid_ids:

            decisions.pop(

                stored_id,

                None,

            )



    for stored_id in list(comments):



        if stored_id not in valid_ids:

            comments.pop(

                stored_id,

                None,

            )



    for item in review_items:



        decisions.setdefault(

            item["id"],

            "Pending",

        )



        comments.setdefault(

            item["id"],

            "",

        )



    # -----------------------------------------

    # COUNTERS

    # -----------------------------------------



    pending_count = sum(

        1

        for item in review_items

        if decisions[

            item["id"]

        ] == "Pending"

    )



    accepted_count = sum(

        1

        for item in review_items

        if decisions[

            item["id"]

        ] == "Accepted"

    )



    rejected_count = sum(

        1

        for item in review_items

        if decisions[

            item["id"]

        ] == "Rejected"

    )



    r1, r2, r3, r4 = st.columns(4)



    r1.metric(

        "Total Findings",

        len(review_items),

    )



    r2.metric(

        "Pending",

        pending_count,

    )



    r3.metric(

        "Accepted",

        accepted_count,

    )



    r4.metric(

        "Rejected",

        rejected_count,

    )



    st.divider()



    # -----------------------------------------

    # REVIEW QUEUE

    # -----------------------------------------



    if not review_items:



        st.success(

            "There are currently no validation "

            "or revision findings requiring "

            "engineer review."

        )



    else:



        st.subheader(

            "Review Queue"

        )



        for number, item in enumerate(

            review_items,

            start=1,

        ):



            current_status = (

                decisions[item["id"]]

            )



            with st.expander(

                f"{number}. "

                f"[{current_status}] "

                f"{item['source']} — "

                f"{item['category']} — "

                f"{item['entity']}"

            ):



                st.write(

                    f"**Source:** "

                    f"{item['source']}"

                )



                st.write(

                    f"**Category:** "

                    f"{item['category']}"

                )



                st.write(

                    f"**Entity:** "

                    f"{item['entity']}"

                )



                st.write(

                    f"**Severity / Review Type:** "

                    f"{item['severity']}"

                )



                st.write(

                    f"**Finding:** "

                    f"{item['description']}"

                )



                options = [

                    "Pending",

                    "Accepted",

                    "Rejected",

                ]



                selected_status = st.radio(

                    "Engineer decision",

                    options,

                    index=options.index(

                        current_status

                    ),

                    horizontal=True,

                    key=(

                        f"decision_"

                        f"{item['id']}"

                    ),

                )



                engineer_comment = (

                    st.text_area(

                        "Engineer comment",

                        value=comments[

                            item["id"]

                        ],

                        placeholder=(

                            "Optional: explain the "

                            "review decision or "

                            "required follow-up."

                        ),

                        key=(

                            f"comment_"

                            f"{item['id']}"

                        ),

                    )

                )



                if st.button(

                    "Save Review",

                    key=(

                        f"save_"

                        f"{item['id']}"

                    ),

                ):



                    decisions[

                        item["id"]

                    ] = selected_status



                    comments[

                        item["id"]

                    ] = engineer_comment



                    st.session_state[

                        "review_decisions"

                    ] = decisions



                    st.session_state[

                        "review_comments"

                    ] = comments



                    review_store.save_review(

                        document_name=(

                            display_filename

                        ),

                        finding_id=(

                            item["id"]

                        ),

                        finding_type=(

                            item["category"]

                        ),

                        source=(

                            item["source"]

                        ),

                        description=(

                            item["description"]

                        ),

                        decision=(

                            selected_status

                        ),

                        comment=(

                            engineer_comment

                        ),

                    )



                    st.success(

                        "Review decision saved "

                        "persistently to SQLite."

                    )



                    st.rerun()



    # -----------------------------------------

    # STRUCTURED EXPORT

    # -----------------------------------------



    st.divider()



    st.subheader(

        "Structured Review Export"

    )



    export_rows = []



    for item in review_items:



        export_rows.append(

            {

                "finding_id":

                    item["id"],

                "document":

                    display_filename,

                "source":

                    item["source"],

                "category":

                    item["category"],

                "entity":

                    item["entity"],

                "severity_or_type":

                    item["severity"],

                "finding":

                    item["description"],

                "review_status":

                    decisions[item["id"]],

                "engineer_comment":

                    comments[item["id"]],

            }

        )



    review_report = {

        "report_type":

            "AUTOSAR HLD Engineer Review",



        "generated_at":

            datetime.now().isoformat(

                timespec="seconds"

            ),



        "document": {

            "filename":

                display_filename,

            "document_id":

                architecture.document_id,

            "version":

                architecture.version,

        },



        "summary": {

            "total_findings":

                len(review_items),

            "pending":

                pending_count,

            "accepted":

                accepted_count,

            "rejected":

                rejected_count,

        },



        "findings":

            export_rows,

    }



    json_data = json.dumps(

        review_report,

        indent=2,

        ensure_ascii=False,

    )



    csv_buffer = io.StringIO()



    csv_fields = [

        "finding_id",

        "document",

        "source",

        "category",

        "entity",

        "severity_or_type",

        "finding",

        "review_status",

        "engineer_comment",

    ]



    writer = csv.DictWriter(

        csv_buffer,

        fieldnames=csv_fields,

    )



    writer.writeheader()



    writer.writerows(

        export_rows

    )



    safe_stem = (

        Path(display_filename)

        .stem

        .replace(

            " ",

            "_",

        )

    )



    download_col1, download_col2 = (

        st.columns(2)

    )



    with download_col1:



        st.download_button(

            "Download Review JSON",

            data=json_data,

            file_name=(

                f"{safe_stem}"

                f"_engineer_review.json"

            ),

            mime="application/json",

            use_container_width=True,

        )



    with download_col2:



        st.download_button(

            "Download Review CSV",

            data=csv_buffer.getvalue(),

            file_name=(

                f"{safe_stem}"

                f"_engineer_review.csv"

            ),

            mime="text/csv",

            use_container_width=True,

        )



    if (

        review_items

        and pending_count == 0

    ):



        st.success(

            "Engineer review is complete "

            "for all current findings."

        )



    elif review_items:



        st.info(

            f"{pending_count} finding(s) "

            f"still require an engineer decision."

        )





# =========================================================

# FOOTER

# =========================================================



st.divider()



st.caption(

    "AUTOSAR HLD Intelligence Assistant | "

    "Evidence-grounded engineering prototype"

)