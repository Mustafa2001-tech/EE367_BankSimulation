"""
data_structures.py
==================
Two manually implemented data structures — NO built-in heapq or deque used.

  SimpleQueue  – list-based FIFO queue          DS1  O(1) enqueue, O(n) search
  MinHeap      – array-based binary min-heap    DS2  O(log n) insert & extract
  HeapNode     – internal node for MinHeap

All Big-O complexities are documented per method.
"""

from __future__ import annotations
from typing import Any, Optional


# ═════════════════════════════════════════════════════════════════════════════
# DS1 — SIMPLE QUEUE  (list-based)
# ═════════════════════════════════════════════════════════════════════════════
class SimpleQueue:
    """
    A basic list-backed queue.

    enqueue  → O(1)  append to end
    dequeue  → O(1)  pop from front  (Python list.pop(0) is O(n) internally,
                      but we model it as O(1) conceptually for small n)
    search   → O(n)  linear scan

    Used in Scenarios 1 and 3.
    """

    def __init__(self) -> None:
        self._data: list = []

    def enqueue(self, item: Any) -> None:
        """Add item to the rear of the queue. O(1)."""
        self._data.append(item)

    def dequeue(self) -> Any:
        """Remove and return the front item. O(n) for list shift."""
        if self.is_empty():
            raise IndexError("dequeue from empty SimpleQueue")
        return self._data.pop(0)

    def peek(self) -> Any:
        """Return front item without removing. O(1)."""
        if self.is_empty():
            raise IndexError("peek on empty SimpleQueue")
        return self._data[0]

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def size(self) -> int:
        return len(self._data)

    def to_list(self) -> list:
        """Return a shallow copy of the internal list. O(n)."""
        return list(self._data)

    def clear(self) -> None:
        self._data.clear()

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"SimpleQueue({self._data})"


# ═════════════════════════════════════════════════════════════════════════════
# DS2 — MIN-HEAP  (manually implemented binary heap)
# ═════════════════════════════════════════════════════════════════════════════
class HeapNode:
    """
    A single node stored inside the MinHeap.

    key     – numeric priority used for heap ordering (lower = higher priority)
    payload – the actual object (Customer or event dict)
    """

    def __init__(self, key: float, payload: Any) -> None:
        self.key:     float = key
        self.payload: Any   = payload

    def __lt__(self, other: HeapNode) -> bool:
        """Comparison used by _heapify methods. O(1)."""
        return self.key < other.key

    def __repr__(self) -> str:
        return f"HeapNode(key={self.key:.3f}, payload={self.payload})"


class MinHeap:
    """
    A manually implemented array-based binary Min-Heap.

    The heap invariant: every parent key ≤ both children keys.

    insert       → O(log n)  — add node then bubble up
    extract_min  → O(log n)  — swap root with last, remove, bubble down
    peek_min     → O(1)      — root is always the minimum
    build_heap   → O(n)      — heapify an existing list in linear time

    Used in Scenarios 2 and 4.
    """

    def __init__(self) -> None:
        self._data: list[HeapNode] = []

    # ── Core operations ───────────────────────────────────────────────────────
    def insert(self, key: float, payload: Any) -> None:
        """
        Insert a new HeapNode and restore the heap property.
        Time Complexity: O(log n)
        """
        node = HeapNode(key, payload)
        self._data.append(node)
        self._heapify_up(len(self._data) - 1)

    def extract_min(self) -> HeapNode:
        """
        Remove and return the node with the smallest key.
        Time Complexity: O(log n)
        """
        if self.is_empty():
            raise IndexError("extract_min from empty MinHeap")
        # Swap root with last element
        self._swap(0, len(self._data) - 1)
        minimum = self._data.pop()          # remove old root (now at end)
        if not self.is_empty():
            self._heapify_down(0)
        return minimum

    def peek_min(self) -> HeapNode:
        """Return the minimum node without removing it. O(1)."""
        if self.is_empty():
            raise IndexError("peek_min on empty MinHeap")
        return self._data[0]

    def build_heap(self, nodes: list[HeapNode]) -> None:
        """
        Build heap from an existing list in O(n) using Floyd's algorithm.
        Time Complexity: O(n)
        """
        self._data = list(nodes)
        # Start from last non-leaf and heapify down each node
        start = (len(self._data) // 2) - 1
        for i in range(start, -1, -1):
            self._heapify_down(i)

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _heapify_up(self, index: int) -> None:
        """
        Bubble node at 'index' upward until heap property is restored.
        Time Complexity: O(log n)
        """
        while index > 0:
            parent = (index - 1) // 2
            if self._data[index] < self._data[parent]:
                self._swap(index, parent)
                index = parent
            else:
                break

    def _heapify_down(self, index: int) -> None:
        """
        Push node at 'index' downward until heap property is restored.
        Time Complexity: O(log n)
        """
        n = len(self._data)
        while True:
            smallest = index
            left     = 2 * index + 1
            right    = 2 * index + 2

            if left < n and self._data[left] < self._data[smallest]:
                smallest = left
            if right < n and self._data[right] < self._data[smallest]:
                smallest = right

            if smallest != index:
                self._swap(index, smallest)
                index = smallest
            else:
                break

    def _swap(self, i: int, j: int) -> None:
        """Swap two nodes in the internal array. O(1)."""
        self._data[i], self._data[j] = self._data[j], self._data[i]

    # ── Utility ───────────────────────────────────────────────────────────────
    def is_empty(self) -> bool:
        return len(self._data) == 0

    def size(self) -> int:
        return len(self._data)

    def to_list(self) -> list:
        """Return payloads in current heap order (NOT sorted). O(n)."""
        return [node.payload for node in self._data]

    def clear(self) -> None:
        self._data.clear()

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"MinHeap(size={len(self._data)}, min={self._data[0] if self._data else None})"
