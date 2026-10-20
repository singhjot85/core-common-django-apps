# Datatypes & Graph Resolution Utilities (`core.utils.datatypes`)

Location: [`core/utils/datatypes/`](./__init__.py)

## Overview

The `core.utils.datatypes` module provides fundamental data structures, graph primitives, and topological dependency builders. These components serve as the backbone for dependency resolution engines such as database seeders and modular task pipelines.

---

## Components

### 1. [`Queue`](./queue.py)

A pointer-based First-In-First-Out (FIFO) queue implemented with internal head and tail cursors over a Python list.

#### Key Mechanics:
* **Amortized O(1) Operations**: Rather than shifting all elements on `pop(0)` (which incurs $O(N)$ overhead), `dequeue()` advances `_start_index`.
* **Automatic Storage Cleanup**: When the queue is drained (`len(active_q) == 1`), `clean_queue()` resets the underlying list and index pointers, releasing memory.

```python
from core.utils.datatypes import Queue

q = Queue()
q.enqueue("task_a")
q.enqueue("task_b")

assert q.peep() == "task_a"   # Inspect head without popping
item = q.dequeue()            # "task_a"
assert q.queue == ["task_b"]  # Active elements slice
```

---

### 2. [`Graph`](./graph.py) & [`DirectedGraph`](./graph.py)

Adjacency-list based graph representations supporting both directed and undirected topologies.

#### [`Graph`](./graph.py)
* `add_node(from_index, to_index)`: Adds an edge between vertices.
* `remove_node(node_index)`: Purges a vertex and all its incident edges.
* `total_nodes`: Number of unique vertices.
* `get_all_nodes()`: Set of all unique vertex indices.

#### [`DirectedGraph`](./graph.py)
Extends `Graph` with directed-specific traversal and sorting:
* `get_in_degree()`: Computes incoming edge counts for all vertices.
* `bfs_topological_sort()`: **Kahn's Algorithm** (Breadth-First Search).
  * Enqueues vertices with in-degree 0 into a [`Queue`](./queue.py).
  * Iteratively dequeues vertices, appends them to the sorted result, and decrements the in-degree of neighboring nodes.
  * Time Complexity: **$O(V + E)$** where $V$ is vertices and $E$ is edges.
  * Space Complexity: **$O(V)$**.
  * Raises [`CycleError`](../../exceptions.py) if a directed cycle is encountered.

```python
from core.utils.datatypes import DirectedGraph

dg = DirectedGraph()
# Edge: 1 -> 2 (Node 1 must execute before Node 2)
dg.add_node(1, 2)
dg.add_node(2, 3)

assert dg.bfs_topological_sort() == [1, 2, 3]
```

---

### 3. [`BaseDAGBuilder`](./implementations.py) & [`InstanceDAGBuilder`](./implementations.py)

Higher-level builders that map arbitrary Python objects, models, or classes to integer-indexed graph nodes and execute dependency-ordered resolution.

#### [`InstanceDAGBuilder`](./implementations.py) Lifecycle:

1. **Mapping**: `_instance_to_number_map()` assigns a unique sequential index to each object label (`instance_label(kls)`).
2. **Edge Construction**: Iterates over instances via `get_instance_sequence()`, queries prerequisites via `get_dependencies(instance)`, and adds edges:
   $$\text{prerequisite} \longrightarrow \text{dependent}$$
   This ensures prerequisites have in-degree 0 and are dequeued first.
3. **Initial Node Pinning**: Queries `is_initial_attribute(instance)` to designate a root node, which is prepended to the sorted sequence.
4. **Topological Sort**: Calls `bfs_topological_sort()` to compute the final ordered list.

#### Implementing a Custom DAG Builder:

```python
from core.utils.datatypes import InstanceDAGBuilder


class ServiceDAGBuilder(InstanceDAGBuilder):
    def __init__(self, services):
        self.services = services
        super().__init__()

    def get_instance_sequence(self):
        return self.services

    def instance_label(self, service):
        return service.name

    def get_dependencies(self, service):
        # Return list of service objects that this service depends on
        return service.prerequisites

    def is_initial_attribute(self, service):
        return getattr(service, "is_root", False)


builder = ServiceDAGBuilder(services=[billing_service, auth_service, crm_service])
execution_plan = builder.topo_sorted_instances()
```
