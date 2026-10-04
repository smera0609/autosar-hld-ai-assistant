from dataclasses import dataclass, field

from app.models.architecture import ArchitectureModel


@dataclass
class RevisionChange:
    category: str
    change_type: str
    entity: str
    description: str


@dataclass
class RevisionComparison:
    old_file: str
    new_file: str
    old_version: str
    new_version: str

    changes: list[RevisionChange] = field(
        default_factory=list
    )

    @property
    def total_changes(self) -> int:
        return len(self.changes)


class RevisionComparator:
    """
    Compare two extracted HLD architecture models.

    Comparison is deterministic and does not use an LLM.
    """

    def compare(
        self,
        old: ArchitectureModel,
        new: ArchitectureModel,
    ) -> RevisionComparison:

        result = RevisionComparison(
            old_file=old.filename,
            new_file=new.filename,
            old_version=old.version,
            new_version=new.version,
        )

        self._compare_named_entities(
            old.components,
            new.components,
            "COMPONENT",
            result,
        )

        self._compare_named_entities(
            old.interfaces,
            new.interfaces,
            "INTERFACE",
            result,
        )

        self._compare_ports(
            old,
            new,
            result,
        )

        self._compare_signals(
            old,
            new,
            result,
        )

        self._compare_dependencies(
            old,
            new,
            result,
        )

        return result

    def _compare_named_entities(
        self,
        old_items,
        new_items,
        category,
        result,
    ):
        old_names = {
            item.name
            for item in old_items
        }

        new_names = {
            item.name
            for item in new_items
        }

        for name in sorted(
            new_names - old_names
        ):
            result.changes.append(
                RevisionChange(
                    category=category,
                    change_type="ADDED",
                    entity=name,
                    description=(
                        f"{category.title()} "
                        f"'{name}' was added."
                    ),
                )
            )

        for name in sorted(
            old_names - new_names
        ):
            result.changes.append(
                RevisionChange(
                    category=category,
                    change_type="REMOVED",
                    entity=name,
                    description=(
                        f"{category.title()} "
                        f"'{name}' was removed."
                    ),
                )
            )

    def _compare_ports(
        self,
        old,
        new,
        result,
    ):
        def port_key(port):
            return (
                port.component,
                port.name,
                port.port_type,
                port.interface,
            )

        old_ports = {
            port_key(port)
            for port in old.ports
        }

        new_ports = {
            port_key(port)
            for port in new.ports
        }

        for port in sorted(
            new_ports - old_ports
        ):
            component, name, port_type, interface = port

            result.changes.append(
                RevisionChange(
                    category="PORT",
                    change_type="ADDED",
                    entity=name,
                    description=(
                        f"Port '{name}' was added to "
                        f"'{component}' as {port_type} "
                        f"using '{interface}'."
                    ),
                )
            )

        for port in sorted(
            old_ports - new_ports
        ):
            component, name, port_type, interface = port

            result.changes.append(
                RevisionChange(
                    category="PORT",
                    change_type="REMOVED",
                    entity=name,
                    description=(
                        f"Port '{name}' was removed from "
                        f"'{component}'."
                    ),
                )
            )

    def _compare_signals(
        self,
        old,
        new,
        result,
    ):
        old_by_interface = {
            signal.interface: signal
            for signal in old.signals
        }

        new_by_interface = {
            signal.interface: signal
            for signal in new.signals
        }

        shared_interfaces = (
            old_by_interface.keys()
            & new_by_interface.keys()
        )

        # Detect changes to signals carried by the
        # same interface.
        for interface in sorted(
            shared_interfaces
        ):
            old_signal = old_by_interface[
                interface
            ]

            new_signal = new_by_interface[
                interface
            ]

            if old_signal.name != new_signal.name:

                result.changes.append(
                    RevisionChange(
                        category="SIGNAL",
                        change_type="RENAMED",
                        entity=interface,
                        description=(
                            f"Signal on interface "
                            f"'{interface}' changed from "
                            f"'{old_signal.name}' to "
                            f"'{new_signal.name}'."
                        ),
                    )
                )

            if old_signal.unit != new_signal.unit:

                result.changes.append(
                    RevisionChange(
                        category="SIGNAL",
                        change_type="MODIFIED",
                        entity=new_signal.name,
                        description=(
                            f"Signal '{new_signal.name}' "
                            f"unit changed from "
                            f"'{old_signal.unit}' to "
                            f"'{new_signal.unit}'."
                        ),
                    )
                )

        old_interfaces = set(
            old_by_interface
        )

        new_interfaces = set(
            new_by_interface
        )

        for interface in sorted(
            new_interfaces - old_interfaces
        ):
            signal = new_by_interface[
                interface
            ]

            result.changes.append(
                RevisionChange(
                    category="SIGNAL",
                    change_type="ADDED",
                    entity=signal.name,
                    description=(
                        f"Signal '{signal.name}' "
                        f"was added on interface "
                        f"'{interface}'."
                    ),
                )
            )

        for interface in sorted(
            old_interfaces - new_interfaces
        ):
            signal = old_by_interface[
                interface
            ]

            result.changes.append(
                RevisionChange(
                    category="SIGNAL",
                    change_type="REMOVED",
                    entity=signal.name,
                    description=(
                        f"Signal '{signal.name}' "
                        f"was removed from interface "
                        f"'{interface}'."
                    ),
                )
            )

    def _compare_dependencies(
        self,
        old,
        new,
        result,
    ):
        def dep_key(dependency):
            return (
                dependency.dependent_component,
                dependency.required_component,
            )

        old_dependencies = {
            dep_key(item)
            for item in old.dependencies
        }

        new_dependencies = {
            dep_key(item)
            for item in new.dependencies
        }

        for dependency in sorted(
            new_dependencies
            - old_dependencies
        ):
            dependent, required = dependency

            result.changes.append(
                RevisionChange(
                    category="DEPENDENCY",
                    change_type="ADDED",
                    entity=dependent,
                    description=(
                        f"Dependency added: "
                        f"'{dependent}' requires "
                        f"'{required}'."
                    ),
                )
            )

        for dependency in sorted(
            old_dependencies
            - new_dependencies
        ):
            dependent, required = dependency

            result.changes.append(
                RevisionChange(
                    category="DEPENDENCY",
                    change_type="REMOVED",
                    entity=dependent,
                    description=(
                        f"Dependency removed: "
                        f"'{dependent}' no longer "
                        f"requires '{required}'."
                    ),
                )
            )