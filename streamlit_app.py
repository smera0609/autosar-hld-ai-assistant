from pathlib import Path



import csv



import io



import json



import tempfile
import zipfile



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

from app.external_validation.arxml_parser import AUTOSARARXMLParser
from app.external_validation.architecture_adapter import AUTOSARArchitectureAdapter











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







    input_mode = st.radio(
        "Input Mode",
        ["HLD Document Analysis", "Official AUTOSAR External Validation"],
        key="input_mode",
    )

    uploaded_file = None
    uploaded_autosar_zip = None
    analyse_button = False
    external_validation_button = False

    if input_mode == "HLD Document Analysis":
        uploaded_file = st.file_uploader("Upload HLD", type=["pdf"], key="main_hld_upload")
        analyse_button = st.button("Analyze Document", type="primary", use_container_width=True)
    else:
        st.caption(
            "Upload the official AUTOSAR Classic Platform Workflow Example ZIP. "
            "The archive is processed temporarily and is not copied into the project repository."
        )
        uploaded_autosar_zip = st.file_uploader(
            "Upload AUTOSAR dataset ZIP",
            type=["zip"],
            key="official_autosar_zip_upload",
        )
        external_validation_button = st.button(
            "Run Official AUTOSAR Validation",
            type="primary",
            use_container_width=True,
            disabled=uploaded_autosar_zip is None,
        )

    st.divider()







    st.subheader("Analysis Pipeline")







    if input_mode == "HLD Document Analysis":
        st.write(
            "PDF → Extraction → Architecture Model → "
            "Validation → RAG → Engineer Review"
        )
    else:
        st.write(
            "ARXML ZIP → Parsing → Architecture Model → "
            "Dependency Resolution → Graph → External Validation"
        )







    if st.session_state.rag_ready:



        st.success("RAG knowledge base ready")











# =========================================================



# OFFICIAL AUTOSAR EXTERNAL VALIDATION MODE

if input_mode == "Official AUTOSAR External Validation":
    st.header("Official AUTOSAR External Validation")
    st.write(
        "Upload the official public AUTOSAR Classic Platform Workflow Example ZIP. "
        "This mode provides external compatibility/generalization evidence; it is "
        "not a production OEM HLD accuracy benchmark."
    )

    if uploaded_autosar_zip is None:
        st.info("Upload the AUTOSAR Workflow Example ZIP from the sidebar to begin.")
        st.stop()

    st.caption(f"Selected dataset: {uploaded_autosar_zip.name}")

    if not external_validation_button:
        st.info("Dataset uploaded. Click **Run Official AUTOSAR Validation** in the sidebar.")
        st.stop()

    try:
        with st.spinner("Extracting and parsing uploaded AUTOSAR ARXML artifacts..."):
            with tempfile.TemporaryDirectory(prefix="autosar_validation_") as temp_dir:
                extraction_root = Path(temp_dir)
                zip_path = extraction_root / "uploaded_autosar_dataset.zip"
                zip_path.write_bytes(uploaded_autosar_zip.getbuffer())

                with zipfile.ZipFile(zip_path, "r") as archive:
                    safe_members = []
                    root_resolved = extraction_root.resolve()
                    for member in archive.infolist():
                        destination = (extraction_root / member.filename).resolve()
                        try:
                            destination.relative_to(root_resolved)
                        except ValueError:
                            raise ValueError(
                                f"Unsafe path detected in ZIP archive: {member.filename}"
                            )
                        safe_members.append(member)
                    archive.extractall(extraction_root, members=safe_members)

                arxml_files = [
                    path
                    for path in extraction_root.rglob("*.arxml")
                    if "__MACOSX" not in path.parts and not path.name.startswith("._")
                ]
                if not arxml_files:
                    raise ValueError(
                        "No .arxml files were found in the uploaded ZIP. "
                        "Upload the extracted/downloaded AUTOSAR Workflow Example archive."
                    )

                extraction = AUTOSARARXMLParser(extraction_root).parse_directory()
                external_architecture = AUTOSARArchitectureAdapter(
                    extraction
                ).to_architecture_model()
                external_graph_builder = ArchitectureGraph()
                external_graph = external_graph_builder.build(external_architecture)
                external_graph_summary = external_graph_builder.summary(external_graph)

        validation_passed = (
            extraction.files_processed > 0
            and len(extraction.parse_errors) == 0
            and len(external_architecture.components) > 0
            and len(external_architecture.dependencies) > 0
            and all(
                not dependency.dependent_component.startswith("CPT_")
                and not dependency.required_component.startswith("CPT_")
                for dependency in external_architecture.dependencies
            )
        )

        if validation_passed:
            st.success("Official AUTOSAR external validation passed.")
        else:
            st.warning("Validation completed, but one or more checks require review.")

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("ARXML Files", extraction.files_processed)
        a2.metric("Parse Errors", len(extraction.parse_errors))
        a3.metric("Components", len(external_architecture.components))
        a4.metric("Ports", len(external_architecture.ports))

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Active Interfaces", len(external_architecture.interfaces))
        b2.metric("Component Instances", len(extraction.instances))
        b3.metric("Assembly Connectors", len(extraction.connectors))
        b4.metric("Dependencies", len(external_architecture.dependencies))

        c1, c2 = st.columns(2)
        c1.metric("Graph Nodes", external_graph.number_of_nodes())
        c2.metric("Graph Edges", external_graph.number_of_edges())

        comp_tab, int_tab, conn_tab, ext_graph_tab, export_tab = st.tabs(
            [
                "Components & Ports",
                "Interfaces",
                "Connectors & Dependencies",
                "Architecture Graph",
                "Validation Export",
            ]
        )

        with comp_tab:
            st.subheader("Software Components")
            st.dataframe(
                [
                    {"Component": component.name, "Description": component.description}
                    for component in external_architecture.components
                ],
                use_container_width=True,
                hide_index=True,
            )
            st.subheader("Ports")
            st.dataframe(
                [
                    {
                        "Component": port.component,
                        "Port": port.name,
                        "Port Type": port.port_type,
                        "Interface": port.interface,
                    }
                    for port in external_architecture.ports
                ],
                use_container_width=True,
                hide_index=True,
            )

        with int_tab:
            st.caption(
                f"The uploaded package contains {len(extraction.interfaces)} interface "
                "catalogue definitions. Only interfaces referenced by active extracted "
                "ports are shown below."
            )
            st.dataframe(
                [
                    {
                        "Interface": interface.name,
                        "Provider": interface.provider or "Not specified",
                        "Consumer": interface.consumer or "Not specified",
                    }
                    for interface in external_architecture.interfaces
                ],
                use_container_width=True,
                hide_index=True,
            )

        with conn_tab:
            st.subheader("Component Instance Mappings")
            st.dataframe(
                [
                    {
                        "Instance": instance.instance_name,
                        "Component Type": instance.component_type,
                        "Category": instance.component_type_category,
                    }
                    for instance in extraction.instances
                ],
                use_container_width=True,
                hide_index=True,
            )
            st.subheader("Assembly Connectors")
            st.dataframe(
                [
                    {
                        "Connector": connector.name,
                        "Provider Instance": connector.provider_component,
                        "Provider Port": connector.provider_port,
                        "Requester Instance": connector.requester_component,
                        "Requester Port": connector.requester_port,
                    }
                    for connector in extraction.connectors
                ],
                use_container_width=True,
                hide_index=True,
            )
            st.subheader("Resolved Component Dependencies")
            st.dataframe(
                [
                    {
                        "Dependent Component": dependency.dependent_component,
                        "Required Component": dependency.required_component,
                    }
                    for dependency in external_architecture.dependencies
                ],
                use_container_width=True,
                hide_index=True,
            )

        with ext_graph_tab:
            st.subheader("Official AUTOSAR Architecture Graph")
            st.caption(
                "The shared graph engine is reused after ARXML is converted to the "
                "common architecture model."
            )
            gv = [
                "digraph AUTOSARExternal {",
                'rankdir="LR";',
                'graph [pad="0.5", nodesep="0.7", ranksep="1"];',
            ]
            for node, attrs in external_graph.nodes(data=True):
                safe_node = str(node).replace('"', '\"')
                label = str(attrs.get("label", node)).replace('"', '\"')
                node_type = attrs.get("node_type", "unknown")
                shape = "box" if node_type == "component" else "ellipse" if node_type == "interface" else "oval"
                gv.append(f'"{safe_node}" [label="{label}", shape="{shape}"];')
            for source, target, attrs in external_graph.edges(data=True):
                safe_source = str(source).replace('"', '\"')
                safe_target = str(target).replace('"', '\"')
                relationship = str(attrs.get("relationship", "")).replace('"', '\"')
                gv.append(
                    f'"{safe_source}" -> "{safe_target}" [label="{relationship}"];'
                )
            gv.append("}")
            st.graphviz_chart("\n".join(gv), use_container_width=True)

            relationship_rows = [
                {"Relationship": relationship, "Count": count}
                for relationship, count in external_graph_summary.get(
                    "relationships", {}
                ).items()
            ]
            if relationship_rows:
                st.dataframe(
                    relationship_rows,
                    use_container_width=True,
                    hide_index=True,
                )

        with export_tab:
            report = {
                "validation_name": "Official AUTOSAR External Validation",
                "dataset": uploaded_autosar_zip.name,
                "classification": "Uploaded public external AUTOSAR validation artifacts",
                "interpretation": (
                    "External compatibility/generalization evidence; not production OEM "
                    "HLD ground-truth accuracy."
                ),
                "arxml_extraction": {
                    "files_processed": extraction.files_processed,
                    "parse_errors": len(extraction.parse_errors),
                    "component_definitions": len(extraction.components),
                    "port_definitions": len(extraction.ports),
                    "interface_catalogue_definitions": len(extraction.interfaces),
                    "component_instances": len(extraction.instances),
                    "assembly_connectors": len(extraction.connectors),
                },
                "common_architecture_model": {
                    "components": len(external_architecture.components),
                    "active_interfaces": len(external_architecture.interfaces),
                    "ports": len(external_architecture.ports),
                    "signals": len(external_architecture.signals),
                    "dependencies": len(external_architecture.dependencies),
                },
                "graph": {
                    "nodes": external_graph.number_of_nodes(),
                    "edges": external_graph.number_of_edges(),
                    "relationships": external_graph_summary.get("relationships", {}),
                },
                "resolved_dependencies": [
                    {
                        "dependent_component": dependency.dependent_component,
                        "required_component": dependency.required_component,
                    }
                    for dependency in external_architecture.dependencies
                ],
                "validation": {
                    "parse_success": len(extraction.parse_errors) == 0,
                    "overall_passed": validation_passed,
                },
            }
            report_json = json.dumps(report, indent=2, ensure_ascii=False)
            st.json(report)
            st.download_button(
                "Download External Validation JSON",
                data=report_json,
                file_name="external_autosar_validation.json",
                mime="application/json",
                use_container_width=True,
            )

    except zipfile.BadZipFile:
        st.error("The uploaded file is not a valid ZIP archive.")
    except Exception as exc:
        st.error(f"Official AUTOSAR validation failed: {exc}")

    st.stop()

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



            .replace('"', '\\\\\\\\"')



        )







        safe_label = (



            str(display_label)



            .replace('"', '\\\\\\\\"')



        )







        if node_type == "component":







            graphviz_lines.append(



                f'"{safe_node}" '



                f'[label="{safe_label}\\\\\nComponent", '



                f'shape="box"];'



            )







        elif node_type == "interface":







            graphviz_lines.append(



                f'"{safe_node}" '



                f'[label="{safe_label}\\\\\nInterface", '



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



                    .replace('"', '\\\\\\\\"')



                )







                signal_label += (



                    f"\\\\\n[{safe_unit}]"



                )







            graphviz_lines.append(



                f'"{safe_node}" '



                f'[label="{signal_label}\\\\\nSignal", '



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



            .replace('"', '\\\\\\\\"')



        )







        safe_target = (



            str(target)



            .replace('"', '\\\\\\\\"')



        )







        safe_relationship = (



            str(relationship)



            .replace('"', '\\\\\\\\"')



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