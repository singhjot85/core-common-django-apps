"""
Graph data structures supporting directed and undirected graph operations.

Provides in-degree computation, Kahn's algorithm breadth-first topological sorting,
and cycle detection for dependency resolution engines.
"""

from __future__ import annotations

import typing

from core.exceptions import CycleError
from core.utils.datatypes.queue import Queue


class Graph:
    """
    General-purpose Graph implementation supporting directed and undirected topologies.

    Attributes:
        _directed (bool): Flag indicating whether edges are unidirectional.
        _adjanceny_list (dict[int, list[int]]): Adjacency list mapping node index to targets.
    """

    def __init__(self, directed: bool = True):
        """
        Initialize an empty graph.

        Args:
            directed (bool): True for directed graph (Node A -> Node B),
                             False for undirected (Node A <-> Node B). Defaults to True.
        """
        self._directed: bool = directed
        self._adjanceny_list: dict[int, list[int]] = {}

    @property
    def total_nodes(self) -> int:
        """
        Get the total count of unique nodes in the graph.

        Returns:
            int: Number of vertices.
        """
        return len(self.get_all_nodes())

    def get_all_nodes(self) -> set[int]:
        """
        Retrieve all distinct node indices present in the graph.

        Returns:
            set[int]: Set of unique node identifiers.
        """
        nodes = set(self.adjacency_list.keys())
        for targets in self.adjacency_list.values():
            nodes.update(targets)

        return nodes

    @property
    def adjacency_list(self) -> dict[int, list[int]]:
        """
        Retrieve the graph's internal adjacency list representation.

        Returns:
            dict[int, list[int]]: Mapping of source node to list of destination nodes.
        """
        if not self._adjanceny_list:
            return {}

        return self._adjanceny_list

    def add_node(self, from_index: int, to_index: int) -> None:
        """
        Add a directed or undirected edge between two nodes.

        Directed Graph:
            ``(from_index) ---> (to_index)``
        Undirected Graph:
            ``(from_index) <---> (to_index)``

        Args:
            from_index (int): Source node index.
            to_index (int): Destination node index.
        """
        if from_index not in self._adjanceny_list:
            self._adjanceny_list[from_index] = []
        # Ensure the to_index node also exists in the adjacency list map
        if to_index not in self._adjanceny_list:
            self._adjanceny_list[to_index] = []

        self._adjanceny_list[from_index].append(to_index)
        if not self._directed:
            self._adjanceny_list[to_index].append(from_index)

    def remove_node(self, node_index: int) -> None:
        """
        Remove a node and all incoming and outgoing edges associated with it.

        Args:
            node_index (int): Identifier of the node to remove.
        """
        self._adjanceny_list.pop(node_index, None)

        # Traverse the entire _adjanceny_list and remove from every node's mapping
        for key, val in self._adjanceny_list.items():
            new_val = [v for v in val if v != node_index]
            self._adjanceny_list[key] = new_val


class DirectedGraph(Graph):
    """
    Directed Acyclic Graph (DAG) implementation with topological sorting and cycle detection.

    Inherits from Graph with `directed=True` by default.
    """

    def __init__(self):
        """Initialize a directed graph."""
        super().__init__(directed=True)

    def get_in_degree(self) -> dict[int, int]:
        """
        Compute the in-degree (count of incoming edges) for every vertex in the graph.

        Returns:
            dict[int, int]: Mapping from node index to incoming edge count.
        """
        nodes = self.get_all_nodes()

        indegree_dict = {node: 0 for node in nodes}

        for targets in self.adjacency_list.values():
            for node in targets:
                if node in indegree_dict:
                    indegree_dict[node] += 1
                else:
                    indegree_dict[node] = 1

        return indegree_dict

    def bfs_topological_sort(self) -> list[int]:
        """
        Topologically sort the graph using Kahn's algorithm (Breadth-First Search).

        Time Complexity: O(V + E) where V is vertices and E is edges.
        Space Complexity: O(V).

        Returns:
            list[int]: Ordered list of node indices where every prerequisite appears
                       before dependent nodes.

        Raises:
            CycleError: If the graph contains a directed cycle (circular dependency).
        """
        topo_sort: list[int] = []
        if not self.adjacency_list:
            return topo_sort

        indegree: dict[int, typing.Union[int, str]] = self.get_in_degree()
        queue = Queue()

        def enqueue_zero_indegree():
            for node in list(indegree.keys()):
                indegree_val = indegree[node]
                if isinstance(indegree_val, int) and indegree_val == 0:
                    queue.enqueue(node)
                    indegree[node] = "X"

        enqueue_zero_indegree()  # Start Topo Sort
        while queue.peep() is not None:
            head = queue.dequeue()
            topo_sort.append(head)

            for node in self.adjacency_list.get(head, []):
                if node in indegree and isinstance(indegree[node], int):
                    indegree[node] -= 1

            enqueue_zero_indegree()

        if len(topo_sort) < len(self.get_all_nodes()):
            raise CycleError("Graph contains a cycle / circular dependency")

        return topo_sort
