"""
Pointer-based First-In-First-Out (FIFO) Queue implementation.

Maintains start and end index pointers over a backing Python list to avoid
costly O(N) array-shift overhead on dequeuing, automatically cleaning memory
when the queue is emptied.
"""

from __future__ import annotations

import typing

QUEUE_DATA: typing.TypeAlias = list[typing.Any]


class Queue:
    """
    Pointer-based FIFO Queue.

    Uses `_start_index` and `_end_index` cursors over an underlying list,
    providing O(1) amortized enqueue and dequeue operations.

    Attributes:
        _start_index (int): Cursor pointing to the front (head) of the queue.
        _end_index (int): Cursor pointing to the rear (tail) of the queue.
        _queue (list[Any]): Backing storage list.
    """

    _start_index: int
    _end_index: int
    _queue: QUEUE_DATA

    def __init__(self):
        """Initialize an empty queue."""
        self.clean_queue()

    def clean_queue(self) -> None:
        """
        Reset the queue storage and cursor indices to 0.

        Frees previously stored references when traversal finishes.
        """
        self._queue = []
        self._start_index = 0
        self._end_index = 0

    @property
    def indices(self) -> tuple[int, int]:
        """
        Get the current cursor positions (start_index, end_index).

        Returns:
            tuple[int, int]: Current head and tail integer indices.
        """
        return self._start_index, self._end_index

    @property
    def queue(self) -> list[typing.Any]:
        """
        Get all active elements currently pending in the queue.

        Returns:
            list[Any]: Slice of active items from head to tail.
        """
        if not self._queue:
            return []
        if self._start_index > self._end_index:
            self.clean_queue()
            return []
        return self._queue[self._start_index : self._end_index + 1]

    def peep(self) -> typing.Optional[typing.Any]:
        """
        Inspect the front element of the queue without removing it.

        Returns:
            Any | None: Head element if queue is non-empty, otherwise None.
        """
        if not self.queue:
            return None

        return self._queue[self._start_index]

    def enqueue(self, value: typing.Any) -> tuple[int, int]:
        """
        Add an element to the rear of the queue.

        Args:
            value (Any): The element to enqueue.

        Returns:
            tuple[int, int]: Updated (start_index, end_index) cursors.
        """
        is_empty = len(self.queue) == 0
        self._queue.append(value)
        if is_empty:
            self._start_index = 0
            self._end_index = 0
        else:
            self._end_index += 1
        return self.indices

    def dequeue(self) -> typing.Optional[typing.Any]:
        """
        Remove and return the front element of the queue.

        Advances `_start_index` pointer, automatically resetting storage
        when the last remaining element is dequeued.

        Returns:
            Any | None: Head element if queue was non-empty, otherwise None.
        """
        active_q = self.queue
        if not active_q:
            self.clean_queue()
            return None

        return_value = self._queue[self._start_index]
        if len(active_q) == 1:
            self.clean_queue()
        else:
            self._start_index += 1

        return return_value
