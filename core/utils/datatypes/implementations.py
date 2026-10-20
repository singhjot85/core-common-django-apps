"""
DAG builder implementations for resolving dependency orders among Python objects and classes.

Provides BaseDAGBuilder and InstanceDAGBuilder which map arbitrary Python objects to
graph nodes, construct dependency edges, execute topological sorts, and ensure initial
execution constraints are satisfied.
"""

from __future__ import annotations

import typing

from core.utils.datatypes.graph import DirectedGraph


class BaseDAGBuilder(DirectedGraph):
    """
    Abstract Base Class for Directed Acyclic Graph (DAG) builders.

    Subclasses must implement `resolve_dependencies()` to construct graph edges
    prior to topological sort execution.
    """

    def resolve_dependencies(self) -> None:
        """
        Construct nodes and directed edges in the underlying graph.

        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("Dependency resolution logic not found.")


class InstanceDAGBuilder(BaseDAGBuilder):
    """
    Builds and resolves a DAG for an arbitrary sequence of Python classes or objects.

    Maps instances to integer indices, queries per-instance dependencies, builds
    directed edges `(prerequisite -> dependent)`, and executes a BFS topological sort
    using Kahn's algorithm.

    Attributes:
        _instance_to_num (dict[str, int]): Map of instance label to unique integer index.
        _num_to_instance (dict[int, typing.Any]): Map of integer index back to instance.
        _first_instance (typing.Any): Optional instance pinned to execute first.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the instance DAG builder with empty node mappings."""
        self._instance_to_num: dict[str, int] = {}
        self._num_to_instance: dict[int, typing.Any] = {}
        self._first_instance: typing.Optional[typing.Any] = None
        super().__init__(*args, **kwargs)

    def get_instance_sequence(self) -> typing.Union[list, tuple]:
        """
        Get the sequence of instances or classes that need to be topologically sorted.

        Returns:
            list | tuple: Sequence of instances to sort.

        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("get_instance_sequence is needed to build DAG.")

    def is_initial_attribute(self, instance: typing.Any) -> bool:
        """
        Check if a given instance qualifies as the initial / root execution node.

        Args:
            instance (Any): The instance or class to evaluate.

        Returns:
            bool: True if instance is designated as an initial node, False otherwise.

        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("is_initial_attribute not implemented.")

    def get_dependencies(self, instance: typing.Any) -> list:
        """
        Get all prerequisite dependencies that must execute BEFORE the given instance.

        Args:
            instance (Any): The instance or class whose prerequisites are queried.

        Returns:
            list: List of prerequisite instances or classes.

        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("get_dependencies not implemented.")

    def instance_label(self, kls: typing.Any) -> str:
        """
        Compute a unique string identifier for a given instance or class.

        Defaults to `kls.__name__`. Can be overridden for custom labeling.

        Args:
            kls (Any): The object or class.

        Returns:
            str: String label used in internal index mapping.
        """
        return getattr(kls, "__name__", str(kls))

    def _instance_to_number_map(self) -> None:
        """
        Assign a unique positive integer index to each instance in the sequence.

        Populates `_instance_to_num` and `_num_to_instance` lookup tables.
        """
        kls_sequence = self.get_instance_sequence()
        for i, kls in enumerate(kls_sequence):
            self._instance_to_num[self.instance_label(kls)] = i
            self._num_to_instance[i] = kls

    def _resolve_and_build_adjacency_list(self) -> None:
        """
        Construct graph nodes and dependency edges from instance dependencies.

        For each dependency `dep` of `instance`, adds a directed edge:
            `(dep) ---> (instance)`
        signifying that `dep` has in-degree 0 and must execute before `instance`.
        Also determines the optional `_first_instance`.
        """
        self._instance_to_number_map()
        self._first_instance = None
        for i in self._num_to_instance.keys():
            if i not in self._adjanceny_list:
                self._adjanceny_list[i] = []

        for instance in self.get_instance_sequence():
            # Add dependency edges: prerequisite (dep) -> dependent (instance)
            if depends_on := self.get_dependencies(instance):
                for dep in depends_on:
                    self.add_node(
                        from_index=self._instance_to_num[self.instance_label(dep)],
                        to_index=self._instance_to_num[self.instance_label(instance)],
                    )

            # Identify initial node
            if self.is_initial_attribute(instance):
                self._first_instance = instance

        # To be safe, when no instance is found assign any random as first
        if not self._first_instance:
            self._first_instance = self.adjacency_list[1][0]

    def resolve_dependencies(self):
        """
        Hook to resolve instance dependencies into graph adjacency lists.
        """
        self._resolve_and_build_adjacency_list()

    def topo_sorted_instances(self) -> list[typing.Any]:
        """
        Compute the topologically sorted order of instances based on dependencies.

        Executes Kahn's algorithm BFS topological sort, then positions `_first_instance`
        at the head of the sequence if configured.

        Returns:
            list[Any]: Topologically ordered list of instances.

        Raises:
            CycleError: If circular dependencies exist among instances.
        """
        self.resolve_dependencies()
        sorted_graph: list[int] = self.bfs_topological_sort()

        sorted_instances: list[typing.Any] = []
        for index in sorted_graph:
            sorted_instances.append(self._num_to_instance[index])

        # Pin the designated first instance at the start of the sequence
        if self._first_instance:
            if self._first_instance in sorted_instances:
                sorted_instances.remove(self._first_instance)
            return [self._first_instance] + sorted_instances

        return sorted_instances
