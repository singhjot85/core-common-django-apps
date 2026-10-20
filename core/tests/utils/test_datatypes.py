"""
Unit tests for core.utils.datatypes (Queue, Graph, DirectedGraph, InstanceDAGBuilder).
"""

import pytest

from core.exceptions import CycleError
from core.utils.datatypes.graph import DirectedGraph, Graph
from core.utils.datatypes.implementations import BaseDAGBuilder, InstanceDAGBuilder
from core.utils.datatypes.queue import Queue


class TestQueue:
    """Tests for the pointer-based Queue data structure."""

    def test_queue_initial_state(self):
        q = Queue()
        assert q.queue == []
        assert q.peep() is None
        assert q.indices == (0, 0)

    def test_enqueue_single_item(self):
        q = Queue()
        indices = q.enqueue("item1")
        assert indices == (0, 0)
        assert q.queue == ["item1"]
        assert q.peep() == "item1"

    def test_enqueue_multiple_items(self):
        q = Queue()
        q.enqueue("a")
        q.enqueue("b")
        indices = q.enqueue("c")
        assert indices == (0, 2)
        assert q.queue == ["a", "b", "c"]
        assert q.peep() == "a"

    def test_dequeue_returns_fifo_order(self):
        q = Queue()
        q.enqueue("first")
        q.enqueue("second")
        q.enqueue("third")

        assert q.dequeue() == "first"
        assert q.queue == ["second", "third"]
        assert q.peep() == "second"

        assert q.dequeue() == "second"
        assert q.queue == ["third"]
        assert q.peep() == "third"

        assert q.dequeue() == "third"
        assert q.queue == []
        assert q.peep() is None

    def test_dequeue_empty_queue(self):
        q = Queue()
        assert q.dequeue() is None
        assert q.queue == []

    def test_queue_resets_indices_when_exhausted(self):
        q = Queue()
        q.enqueue("x")
        q.enqueue("y")
        q.dequeue()
        q.dequeue()
        assert q.queue == []
        assert q.indices == (0, 0)


class TestGraph:
    """Tests for the base Graph data structure."""

    def test_graph_initialization_directed(self):
        g = Graph(directed=True)
        assert g.adjacency_list == {}
        assert g.total_nodes == 0
        assert g.get_all_nodes() == set()

    def test_add_node_directed(self):
        g = Graph(directed=True)
        g.add_node(1, 2)
        assert g.adjacency_list[1] == [2]
        assert g.adjacency_list[2] == []
        assert g.get_all_nodes() == {1, 2}
        assert g.total_nodes == 2

    def test_add_node_undirected(self):
        g = Graph(directed=False)
        g.add_node(1, 2)
        assert g.adjacency_list[1] == [2]
        assert g.adjacency_list[2] == [1]
        assert g.get_all_nodes() == {1, 2}

    def test_remove_node(self):
        g = Graph(directed=True)
        g.add_node(1, 2)
        g.add_node(2, 3)
        g.add_node(1, 3)

        g.remove_node(2)
        assert 2 not in g.adjacency_list
        assert 2 not in g.adjacency_list[1]
        assert g.get_all_nodes() == {1, 3}


class TestDirectedGraph:
    """Tests for DirectedGraph and Kahn's algorithm BFS topological sort."""

    def test_empty_graph_topological_sort(self):
        dg = DirectedGraph()
        assert dg.bfs_topological_sort() == []

    def test_linear_dependency_topological_sort(self):
        # 1 -> 2 -> 3
        dg = DirectedGraph()
        dg.add_node(1, 2)
        dg.add_node(2, 3)

        indegree = dg.get_in_degree()
        assert indegree[1] == 0
        assert indegree[2] == 1
        assert indegree[3] == 1

        order = dg.bfs_topological_sort()
        assert order == [1, 2, 3]

    def test_diamond_dag_topological_sort(self):
        # 1 -> 2, 1 -> 3, 2 -> 4, 3 -> 4
        dg = DirectedGraph()
        dg.add_node(1, 2)
        dg.add_node(1, 3)
        dg.add_node(2, 4)
        dg.add_node(3, 4)

        order = dg.bfs_topological_sort()
        assert order[0] == 1
        assert order[-1] == 4
        assert set(order[1:3]) == {2, 3}

    def test_cycle_detection_raises_cycle_error(self):
        # 1 -> 2 -> 3 -> 1 (Cycle)
        dg = DirectedGraph()
        dg.add_node(1, 2)
        dg.add_node(2, 3)
        dg.add_node(3, 1)

        with pytest.raises(CycleError, match="cycle / circular dependency"):
            dg.bfs_topological_sort()

    def test_self_loop_raises_cycle_error(self):
        # 1 -> 1
        dg = DirectedGraph()
        dg.add_node(1, 1)

        with pytest.raises(CycleError, match="cycle / circular dependency"):
            dg.bfs_topological_sort()


class DummyItem:
    def __init__(self, name: str, depends_on: list = None, is_initial: bool = False):
        self.name = name
        self.depends_on = depends_on or []
        self.is_initial = is_initial

    def __repr__(self):
        return f"DummyItem({self.name})"


class DummyDAGBuilder(InstanceDAGBuilder):
    def __init__(self, items: list[DummyItem]):
        self.items = items
        super().__init__()

    def get_instance_sequence(self) -> list[DummyItem]:
        return self.items

    def instance_label(self, instance: DummyItem) -> str:
        return instance.name

    def get_dependencies(self, instance: DummyItem) -> list[DummyItem]:
        return instance.depends_on

    def is_initial_attribute(self, instance: DummyItem) -> bool:
        return instance.is_initial


class TestInstanceDAGBuilder:
    """Tests for InstanceDAGBuilder topological sort and initial instance resolution."""

    def test_unimplemented_abstract_methods_raise(self):
        builder = InstanceDAGBuilder()
        with pytest.raises(NotImplementedError):
            builder.get_instance_sequence()
        with pytest.raises(NotImplementedError):
            builder.is_initial_attribute(None)
        with pytest.raises(NotImplementedError):
            builder.get_dependencies(None)

    def test_base_dag_builder_resolve_dependencies_raises(self):
        base_builder = BaseDAGBuilder()
        with pytest.raises(NotImplementedError):
            base_builder.resolve_dependencies()

    def test_instance_dag_builder_sorts_by_dependency(self):
        # C depends on B, B depends on A
        a = DummyItem("A")
        b = DummyItem("B", depends_on=[a])
        c = DummyItem("C", depends_on=[b])

        # Sequence given in reverse order
        builder = DummyDAGBuilder(items=[c, b, a])
        sorted_instances = builder.topo_sorted_instances()

        names = [item.name for item in sorted_instances]
        assert names == ["A", "B", "C"]

    def test_instance_dag_builder_respects_initial_instance(self):
        # X and Y have no dependencies, but Y is marked is_initial
        x = DummyItem("X")
        y = DummyItem("Y", is_initial=True)
        z = DummyItem("Z", depends_on=[x])

        builder = DummyDAGBuilder(items=[x, z, y])
        sorted_instances = builder.topo_sorted_instances()

        names = [item.name for item in sorted_instances]
        assert names[0] == "Y"
        assert names.index("X") < names.index("Z")

    def test_instance_dag_builder_detects_cycles(self):
        a = DummyItem("A")
        b = DummyItem("B")
        a.depends_on = [b]
        b.depends_on = [a]

        builder = DummyDAGBuilder(items=[a, b])
        with pytest.raises(CycleError):
            builder.topo_sorted_instances()
