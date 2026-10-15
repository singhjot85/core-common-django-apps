import typing

QUEUE: typing.TypeAlias = list[typing.Any]


class Queue:
    _start_index: int
    _end_index: int
    _queue: QUEUE

    def __init__(self):
        self.clean_queue()  # Start with clean queue always

    def clean_queue(self):
        """
        Currently to prevent cpu cycle's we are keeping the ``_queue`` attribute as-is,
        but when both the indice's meet, i.e. end of traversal we can clean it to free the space
        """
        self._queue = []
        self._start_index = 0
        self._end_index = 0

    @property
    def indices(self):
        return self._start_index, self._end_index

    @property
    def queue(self):
        """
        Returns the active elements in the queue.
        """
        if not self._queue:
            return []
        if self._start_index > self._end_index:
            self.clean_queue()
            return []
        return self._queue[self._start_index : self._end_index + 1]

    def peep(self) -> typing.Optional[typing.Any]:
        if not self.queue:
            return None

        return self._queue[self._start_index]

    def enqueue(self, value: typing.Any) -> tuple[int, int]:
        """
        Enque an element to queue,
        Internally increase the end_index

        Args:
            value (Any): Value to put in queue

        Returns:
            (int, int): start and end index of the queue
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
        """Pop the first element of the queue,
        Internally move's the start pointer one step ahead,

        Returns:
            (Any, optional): First element of the queue
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
