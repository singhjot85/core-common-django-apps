import typing

from core.utils.datatypes.graph import DirectedGraph


class BaseDAGBuilder(DirectedGraph):
    """
    Base class DirectedAcyclicGraph Implementation.
    """

    def resolve_dependencies(self):
        """
        Resolve dependencies based on your own logic
        """
        raise NotImplementedError("Dependecy resolution logic not found.")


class InstanceDAGBuilder(BaseDAGBuilder):
    """
    Build DAG for an given sequence of classes/objects
    """

    _instance_to_num: dict
    _num_to_instance: dict
    _first_instance: typing.Any

    def __init__(self, *args, **kwargs):
        self._instance_to_num = {}
        self._num_to_instance = {}
        super().__init__(*args, **kwargs)

    def get_instance_sequence(self) -> typing.Union[list, tuple]:
        """
        Get sequence of instance that need to Sorted using DAG
        """
        raise NotImplementedError("get_instance_sequence is needer to build DAG.")

    def is_initial_attribute(self) -> bool:
        """
        Get the attribute representing inital instance.

        Example:
        >>> instance.initial
        """
        raise NotImplementedError("is_initial_attribute not implemented")

    def get_dependencies(self, instance) -> list:
        """
        Get the all the dependencies for the instance.

        Example:
        >>> instance.depends_on
        """
        raise NotImplementedError("get_dependencies not implemented")

    def instance_label(self, kls):
        """
        Get stringified notation of the instance.
        Overridable for instance specific string notation logic.
        """
        return kls.__name__

    def _instance_to_number_map(self):
        """
        Hepler method, that label's a positive integer to each object for DAG topological sort.
        The idea is to make object dependecy sorting easier.
        """
        kls_sequence: list[type] = self.get_instance_sequence()
        for i, kls in enumerate(kls_sequence):
            self._instance_to_num[self.instance_label(kls)] = i
            self._num_to_instance[i] = kls

    def _resolve_and_build_adjacency_list(self):
        """
        Resolve dependecies/nodes of the graph into weights
        and build an adjaceny list out of that.
        """
        self._instance_to_number_map()
        self._first_instance = None
        for i in self._num_to_instance.keys():
            if i not in self._adjanceny_list:
                self._adjanceny_list[i] = []

        for instance in self.get_instance_sequence():

            # Add a dependency to adjanceny list
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
        Overridable resolve dependency module.
        """
        self._resolve_and_build_adjacency_list()

    def topo_sorted_instances(self) -> list[type]:
        """
        Get sorted Instances in the order of the dependencies
        """
        self.resolve_dependencies()
        sorted_graph: list[int] = self.bfs_topological_sort()

        sorted_instances: list[type] = []
        for index in sorted_graph:
            sorted_instances.append(self._num_to_instance[index])

        # Append the first at start
        if self._first_instance:
            if self._first_instance in sorted_instances:
                sorted_instances.remove(self._first_instance)
            return [self._first_instance] + sorted_instances

        return sorted_instances
