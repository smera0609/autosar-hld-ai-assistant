import networkx as nx

from app.models.architecture import ArchitectureModel


class ArchitectureGraph:
    """
    Builds a graph representation of an extracted
    AUTOSAR-style HLD architecture.

    Supported relationships:

        Component -> Interface
            PROVIDES

        Interface -> Component
            CONSUMED_BY

        Interface -> Signal
            CARRIES

        Component -> Component
            DEPENDS_ON

        Component -> Component
            FLOWS_TO
    """

    def build(
        self,
        architecture: ArchitectureModel,
        functional_flow: dict | None = None,
    ) -> nx.MultiDiGraph:

        # MultiDiGraph is used because two components can have
        # multiple relationships between them.
        #
        # Example:
        #
        # VehicleSpeedController
        #     DEPENDS_ON -> WheelSpeedSensor
        #
        # WheelSpeedSensor
        #     FLOWS_TO -> VehicleSpeedController

        graph = nx.MultiDiGraph()

        # =====================================================
        # COMPONENT NODES
        # =====================================================

        for component in architecture.components:

            graph.add_node(
                component.name,
                node_type="component",
                description=component.description,
            )

        # =====================================================
        # INTERFACE NODES + RELATIONSHIPS
        # =====================================================

        for interface in architecture.interfaces:

            graph.add_node(
                interface.name,
                node_type="interface",
            )

            if interface.provider:

                graph.add_edge(
                    interface.provider,
                    interface.name,
                    relationship="PROVIDES",
                )

            if interface.consumer:

                graph.add_edge(
                    interface.name,
                    interface.consumer,
                    relationship="CONSUMED_BY",
                )

        # =====================================================
        # SIGNAL NODES + RELATIONSHIPS
        # =====================================================

        for signal in architecture.signals:

            signal_node = (
                f"signal::{signal.name}"
            )

            graph.add_node(
                signal_node,
                node_type="signal",
                label=signal.name,
                unit=signal.unit,
            )

            graph.add_edge(
                signal.interface,
                signal_node,
                relationship="CARRIES",
            )

        # =====================================================
        # COMPONENT DEPENDENCIES
        # =====================================================

        for dependency in architecture.dependencies:

            graph.add_edge(
                dependency.dependent_component,
                dependency.required_component,
                relationship="DEPENDS_ON",
            )

        # =====================================================
        # FUNCTIONAL FLOW
        # =====================================================

        if functional_flow:

            flow_edges = functional_flow.get(
                "edges",
                [],
            )

            for source, target in flow_edges:

                # If OCR or extraction returns an entity that is
                # not already in the architecture model, retain it
                # but explicitly mark it as unknown rather than
                # silently treating it as a valid component.

                if source not in graph:

                    graph.add_node(
                        source,
                        node_type="unknown",
                    )

                if target not in graph:

                    graph.add_node(
                        target,
                        node_type="unknown",
                    )

                graph.add_edge(
                    source,
                    target,
                    relationship="FLOWS_TO",
                )

        return graph

    # =========================================================
    # GRAPH SUMMARY
    # =========================================================

    @staticmethod
    def summary(
        graph: nx.MultiDiGraph,
    ) -> dict:

        node_types = {}

        for _, attributes in graph.nodes(
            data=True
        ):

            node_type = attributes.get(
                "node_type",
                "unknown",
            )

            node_types[node_type] = (
                node_types.get(
                    node_type,
                    0,
                )
                + 1
            )

        relationships = {}

        for _, _, attributes in graph.edges(
            data=True
        ):

            relationship = attributes.get(
                "relationship",
                "unknown",
            )

            relationships[relationship] = (
                relationships.get(
                    relationship,
                    0,
                )
                + 1
            )

        return {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "node_types": node_types,
            "relationships": relationships,
        }

    # =========================================================
    # COMPONENT NEIGHBORS
    # =========================================================

    @staticmethod
    def component_neighbors(
        graph: nx.MultiDiGraph,
        component: str,
    ) -> dict:

        if component not in graph:

            return {
                "incoming": [],
                "outgoing": [],
            }

        incoming = []

        for source, _, _, data in graph.in_edges(
            component,
            keys=True,
            data=True,
        ):

            incoming.append(
                {
                    "entity": source,
                    "relationship": data.get(
                        "relationship"
                    ),
                }
            )

        outgoing = []

        for _, target, _, data in graph.out_edges(
            component,
            keys=True,
            data=True,
        ):

            outgoing.append(
                {
                    "entity": target,
                    "relationship": data.get(
                        "relationship"
                    ),
                }
            )

        return {
            "incoming": incoming,
            "outgoing": outgoing,
        }

    # =========================================================
    # JSON EXPORT
    # =========================================================

    @staticmethod
    def export_json(
        graph: nx.MultiDiGraph,
    ) -> dict:

        nodes = []

        for node, attributes in graph.nodes(
            data=True
        ):

            nodes.append(
                {
                    "id": node,
                    **attributes,
                }
            )

        edges = []

        for (
            source,
            target,
            key,
            attributes,
        ) in graph.edges(
            keys=True,
            data=True,
        ):

            edges.append(
                {
                    "source": source,
                    "target": target,
                    "edge_id": key,
                    **attributes,
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
        }