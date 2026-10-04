from app.models.architecture import (
    ArchitectureModel,
    ValidationIssue,
)


class ConsistencyChecker:

    def validate(
        self,
        architecture: ArchitectureModel,
    ) -> list[ValidationIssue]:

        issues = []

        issues.extend(
            self._check_port_components(
                architecture
            )
        )

        issues.extend(
            self._check_port_interfaces(
                architecture
            )
        )

        issues.extend(
            self._check_interface_ports(
                architecture
            )
        )

        issues.extend(
            self._check_signal_interfaces(
                architecture
            )
        )

        issues.extend(
            self._check_dependencies(
                architecture
            )
        )

        return issues

    def _check_port_components(
        self,
        architecture,
    ):

        issues = []

        component_names = {
            component.name
            for component
            in architecture.components
        }

        for port in architecture.ports:

            if port.component not in component_names:

                issues.append(
                    ValidationIssue(
                        issue_type=(
                            "UNKNOWN_COMPONENT"
                        ),
                        severity="high",
                        entity=port.name,
                        message=(
                            f"Port '{port.name}' "
                            f"references unknown component "
                            f"'{port.component}'."
                        ),
                    )
                )

        return issues

    def _check_port_interfaces(
        self,
        architecture,
    ):

        issues = []

        interface_names = {
            interface.name
            for interface
            in architecture.interfaces
        }

        for port in architecture.ports:

            if (
                port.interface
                not in interface_names
            ):

                issues.append(
                    ValidationIssue(
                        issue_type=(
                            "UNDEFINED_INTERFACE"
                        ),
                        severity="high",
                        entity=port.name,
                        message=(
                            f"Port '{port.name}' "
                            f"references undefined "
                            f"interface "
                            f"'{port.interface}'."
                        ),
                    )
                )

        return issues

    def _check_interface_ports(
        self,
        architecture,
    ):

        issues = []

        for interface in architecture.interfaces:

            provider_ports = [
                port
                for port in architecture.ports
                if (
                    port.interface
                    == interface.name
                    and port.port_type
                    == "P-Port"
                )
            ]

            consumer_ports = [
                port
                for port in architecture.ports
                if (
                    port.interface
                    == interface.name
                    and port.port_type
                    == "R-Port"
                )
            ]

            if not provider_ports:

                issues.append(
                    ValidationIssue(
                        issue_type=(
                            "MISSING_PROVIDER_PORT"
                        ),
                        severity="high",
                        entity=interface.name,
                        message=(
                            f"Interface "
                            f"'{interface.name}' "
                            f"has no provider P-Port."
                        ),
                    )
                )

            if not consumer_ports:

                issues.append(
                    ValidationIssue(
                        issue_type=(
                            "MISSING_CONSUMER_PORT"
                        ),
                        severity="medium",
                        entity=interface.name,
                        message=(
                            f"Interface "
                            f"'{interface.name}' "
                            f"has no consumer R-Port."
                        ),
                    )
                )

        return issues

    def _check_signal_interfaces(
        self,
        architecture,
    ):

        issues = []

        interface_names = {
            interface.name
            for interface
            in architecture.interfaces
        }

        for signal in architecture.signals:

            if (
                signal.interface
                not in interface_names
            ):

                issues.append(
                    ValidationIssue(
                        issue_type=(
                            "SIGNAL_INTERFACE_MISSING"
                        ),
                        severity="high",
                        entity=signal.name,
                        message=(
                            f"Signal '{signal.name}' "
                            f"references undefined "
                            f"interface "
                            f"'{signal.interface}'."
                        ),
                    )
                )

        return issues

    def _check_dependencies(
        self,
        architecture,
    ):

        issues = []

        component_names = {
            component.name
            for component
            in architecture.components
        }

        for dependency in architecture.dependencies:

            if (
                dependency.dependent_component
                not in component_names
            ):

                issues.append(
                    ValidationIssue(
                        issue_type=(
                            "INVALID_DEPENDENCY"
                        ),
                        severity="high",
                        entity=(
                            dependency
                            .dependent_component
                        ),
                        message=(
                            f"Dependency references "
                            f"unknown component "
                            f"'{dependency.dependent_component}'."
                        ),
                    )
                )

            if (
                dependency.required_component
                not in component_names
            ):

                issues.append(
                    ValidationIssue(
                        issue_type=(
                            "INVALID_DEPENDENCY"
                        ),
                        severity="high",
                        entity=(
                            dependency
                            .required_component
                        ),
                        message=(
                            f"Dependency references "
                            f"unknown component "
                            f"'{dependency.required_component}'."
                        ),
                    )
                )

        return issues