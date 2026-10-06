import re

from app.models.architecture import ArchitectureModel


class ArchitectureQueryRouter:
    """
    Answers deterministic architecture questions directly from the
    extracted ArchitectureModel.

    The router handles questions about:
    - component inventory
    - interface inventory
    - signal inventory
    - port inventory
    - interface providers
    - interface consumers
    - component ports
    - component dependencies

    If the question is not suitable for deterministic structured
    answering, the method returns None so that the application can
    fall back to the normal RAG pipeline.

    Ground-truth data is NOT used here.
    """

    def answer(
        self,
        question: str,
        architecture: ArchitectureModel,
    ) -> str | None:

        if not question or architecture is None:
            return None

        q = self._normalize(question)

        # =================================================
        # COMPONENT INVENTORY
        # =================================================

        component_inventory_patterns = [
            "what components are present",
            "which components are present",
            "list components",
            "list the components",
            "what are the components",
            "show components",
            "show the components",
        ]

        if any(
            pattern in q
            for pattern in component_inventory_patterns
        ):
            names = [
                component.name.strip()
                for component in architecture.components
                if component.name
                and component.name.strip()
            ]

            if not names:
                return (
                    "No components were extracted "
                    "from the HLD."
                )

            return ", ".join(names)

        # =================================================
        # INTERFACE INVENTORY
        # =================================================

        interface_inventory_patterns = [
            "what interfaces are present",
            "which interfaces are present",
            "list interfaces",
            "list the interfaces",
            "what are the interfaces",
            "show interfaces",
            "show the interfaces",
        ]

        if any(
            pattern in q
            for pattern in interface_inventory_patterns
        ):
            names = [
                interface.name.strip()
                for interface in architecture.interfaces
                if interface.name
                and interface.name.strip()
            ]

            if not names:
                return (
                    "No interfaces were extracted "
                    "from the HLD."
                )

            return ", ".join(names)

        # =================================================
        # SIGNAL INVENTORY
        # =================================================

        signal_inventory_patterns = [
            "what signals are present",
            "which signals are present",
            "list signals",
            "list the signals",
            "what are the signals",
            "show signals",
            "show the signals",
        ]

        if any(
            pattern in q
            for pattern in signal_inventory_patterns
        ):
            names = [
                signal.name.strip()
                for signal in architecture.signals
                if signal.name
                and signal.name.strip()
            ]

            if not names:
                return (
                    "No signals were extracted "
                    "from the HLD."
                )

            return ", ".join(names)

        # =================================================
        # PORT INVENTORY
        # =================================================

        port_inventory_patterns = [
            "what ports are present",
            "which ports are present",
            "list ports",
            "list the ports",
            "what are the ports",
            "show ports",
            "show the ports",
        ]

        if any(
            pattern in q
            for pattern in port_inventory_patterns
        ):
            names = [
                port.name.strip()
                for port in architecture.ports
                if port.name
                and port.name.strip()
            ]

            if not names:
                return (
                    "No ports were extracted "
                    "from the HLD."
                )

            return ", ".join(names)

        # =================================================
        # INTERFACE PROVIDER / CONSUMER
        # =================================================

        question_compact = self._compact(question)

        for interface in architecture.interfaces:

            interface_name = (
                interface.name.strip()
                if interface.name
                else ""
            )

            if not interface_name:
                continue

            interface_compact = self._compact(
                interface_name
            )

            # The question must actually mention this
            # interface before provider/consumer logic runs.
            if interface_compact not in question_compact:
                continue

            provider_patterns = [
                "provide",
                "provider",
                "provides",
                "provided",
                "providing",
            ]

            if any(
                pattern in q
                for pattern in provider_patterns
            ):
                provider = (
                    interface.provider.strip()
                    if interface.provider
                    else ""
                )

                if provider:
                    return provider

                return (
                    "No provider is identified for "
                    f"{interface_name} in the "
                    "extracted architecture."
                )

            consumer_patterns = [
                "consume",
                "consumer",
                "consumes",
                "consumed",
                "requiring",
            ]

            if any(
                pattern in q
                for pattern in consumer_patterns
            ):
                consumer = (
                    interface.consumer.strip()
                    if interface.consumer
                    else ""
                )

                if consumer:
                    return consumer

                return (
                    "No consumer is identified for "
                    f"{interface_name} in the "
                    "extracted architecture."
                )

        # =================================================
        # PORTS OF A SPECIFIC COMPONENT
        # =================================================

        if "port" in q:

            for component in architecture.components:

                component_name = (
                    component.name.strip()
                    if component.name
                    else ""
                )

                if not component_name:
                    continue

                component_compact = self._compact(
                    component_name
                )

                if (
                    component_compact
                    not in question_compact
                ):
                    continue

                component_ports = [
                    port
                    for port in architecture.ports
                    if (
                        port.component
                        and self._compact(
                            port.component
                        )
                        == component_compact
                    )
                ]

                if component_ports:

                    formatted_ports = []

                    for port in component_ports:

                        port_name = (
                            port.name.strip()
                            if port.name
                            else "UnnamedPort"
                        )

                        port_type = (
                            port.port_type.strip()
                            if port.port_type
                            else "UnknownType"
                        )

                        interface_name = (
                            port.interface.strip()
                            if port.interface
                            else "UnknownInterface"
                        )

                        formatted_ports.append(
                            f"{port_name} "
                            f"({port_type}, "
                            f"{interface_name})"
                        )

                    return ", ".join(
                        formatted_ports
                    )

                return (
                    "No ports were extracted for "
                    f"{component_name}."
                )

        # =================================================
        # DEPENDENCIES OF A SPECIFIC COMPONENT
        # =================================================

        dependency_words = [
            "depend",
            "depends",
            "dependency",
            "dependencies",
            "require",
            "requires",
            "required",
        ]

        if any(
            word in q
            for word in dependency_words
        ):

            for component in architecture.components:

                component_name = (
                    component.name.strip()
                    if component.name
                    else ""
                )

                if not component_name:
                    continue

                component_compact = self._compact(
                    component_name
                )

                if (
                    component_compact
                    not in question_compact
                ):
                    continue

                required_components = [
                    dependency.required_component.strip()
                    for dependency
                    in architecture.dependencies
                    if (
                        dependency.dependent_component
                        and self._compact(
                            dependency.dependent_component
                        )
                        == component_compact
                        and dependency.required_component
                        and dependency.required_component.strip()
                    )
                ]

                if required_components:
                    return ", ".join(
                        required_components
                    )

                return (
                    "No component dependencies were "
                    f"extracted for {component_name}."
                )

        # =================================================
        # NOT A STRUCTURED ARCHITECTURE QUESTION
        # =================================================
        #
        # Returning None is intentional.
        #
        # The Streamlit application will later use this
        # result to decide that the normal RAG pipeline
        # should answer the question.
        # =================================================

        return None

    # =====================================================
    # TEXT NORMALISATION
    # =====================================================

    @staticmethod
    def _normalize(value: str) -> str:
        """
        Normal form used for natural-language matching.

        Example:
        'What Components are Present?'
            ->
        'what components are present'
        """

        value = value.lower().strip()

        # Convert punctuation and separators to spaces.
        value = re.sub(
            r"[^a-z0-9]+",
            " ",
            value,
        )

        # Remove repeated spaces.
        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @staticmethod
    def _compact(value: str) -> str:
        """
        Compact form used for entity-name matching.

        Examples:
        'LightRequestInterface'
            ->
        'lightrequestinterface'

        'Light Request Interface'
            ->
        'lightrequestinterface'
        """

        return re.sub(
            r"[^a-z0-9]+",
            "",
            value.lower(),
        )