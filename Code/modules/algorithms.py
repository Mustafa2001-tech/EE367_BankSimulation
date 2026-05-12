"""
algorithms.py
=============
Two algorithms implemented from scratch:

  InsertionSortScheduler  – Algorithm 1
      Keeps the customer queue sorted by service_time using Insertion Sort.
      O(n²) worst-case per full sort, O(n) per single insertion.

  BinarySearchScheduler   – Algorithm 2
      Uses Binary Search to find the correct insertion position in an
      already-sorted queue, then inserts the customer there.
      O(log n) to find position, O(n) to shift — overall O(n) per insert
      but far fewer comparisons than Insertion Sort.

Both schedulers expose the same interface so the simulation engine
can swap them without any other code changes.
"""

from __future__ import annotations
from typing import List
from modules.entities import Customer
from modules.data_structures import SimpleQueue, MinHeap


# ═════════════════════════════════════════════════════════════════════════════
# ALGORITHM 1 — INSERTION SORT SCHEDULER
# ═════════════════════════════════════════════════════════════════════════════
class InsertionSortScheduler:
    """
    Maintains a sorted list of waiting customers using Insertion Sort.

    Every time a new customer arrives it is inserted into the correct
    position so the queue stays sorted by service_time (shortest first).

    Works with BOTH DS1 (SimpleQueue) and DS2 (MinHeap):
      - DS1 mode: sorts the internal list directly.
      - DS2 mode: inserts into the heap using service_time as the key
                  (heap ordering gives us the min naturally, but we
                   still perform the insertion-sort pass on the raw list
                   before building the heap so the comparison is fair).

    Time Complexity (insertion): O(n)   — one pass over the sorted array
    Time Complexity (full sort): O(n²)  — classic insertion sort
    """

    def __init__(self, ds_mode: str = "queue") -> None:
        """
        ds_mode: "queue"  → use SimpleQueue (DS1)
                 "heap"   → use MinHeap     (DS2)
        """
        self.ds_mode   = ds_mode
        self._queue: SimpleQueue = SimpleQueue()  # always kept sorted
        self._heap:  MinHeap     = MinHeap()

    # ── Public interface ──────────────────────────────────────────────────────
    def add_customer(self, customer: Customer) -> None:
        """
        Insert customer into the sorted structure.
        Insertion Sort: find the right spot and insert. O(n).
        """
        if self.ds_mode == "queue":
            self._insertion_sort_into_list(customer)
        else:
            # For heap mode: maintain a sorted shadow list,
            # then rebuild the heap — demonstrates insertion sort + heap
            self._insertion_sort_into_list(customer)
            self._rebuild_heap()

    def next_customer(self) -> Customer | None:
        """Return and remove the next customer (shortest service time). O(log n) heap / O(n) queue."""
        if self.ds_mode == "queue":
            if self._queue.is_empty():
                return None
            return self._queue.dequeue()
        else:
            if self._heap.is_empty():
                return None
            return self._heap.extract_min().payload

    def peek_next(self) -> Customer | None:
        if self.ds_mode == "queue":
            if self._queue.is_empty():
                return None
            return self._queue.peek()
        else:
            if self._heap.is_empty():
                return None
            return self._heap.peek_min().payload

    def size(self) -> int:
        if self.ds_mode == "queue":
            return self._queue.size()
        return self._heap.size()

    def is_empty(self) -> bool:
        return self.size() == 0

    def waiting_list(self) -> list:
        """Return all waiting customers in order (for GUI display)."""
        if self.ds_mode == "queue":
            return self._queue.to_list()
        return self._heap.to_list()

    def clear(self) -> None:
        self._queue.clear()
        self._heap.clear()

    # ── Core algorithm ────────────────────────────────────────────────────────
    def _insertion_sort_into_list(self, customer: Customer) -> None:
        """
        Classic Insertion Sort — insert customer into the sorted internal list.

        Scan from right to left, shift elements that are larger than
        the new customer's service_time one position to the right,
        then place the new customer in the gap.

        Time Complexity: O(n) per insertion into a sorted array.
        Space Complexity: O(1) extra.
        """
        lst = self._queue.to_list()
        lst.append(customer)                     # add at end temporarily

        # Insertion sort pass (only need to place the last element)
        i = len(lst) - 1
        while i > 0 and lst[i - 1].service_time > lst[i].service_time:
            lst[i], lst[i - 1] = lst[i - 1], lst[i]   # shift right
            i -= 1

        # Rebuild the SimpleQueue from the sorted list
        self._queue.clear()
        for c in lst:
            self._queue.enqueue(c)

    def _rebuild_heap(self) -> None:
        """Rebuild MinHeap from the sorted shadow list. O(n)."""
        from modules.data_structures import HeapNode
        nodes = [HeapNode(c.service_time, c) for c in self._queue.to_list()]
        self._heap.clear()
        self._heap.build_heap(nodes)


# ═════════════════════════════════════════════════════════════════════════════
# ALGORITHM 2 — BINARY SEARCH SCHEDULER
# ═════════════════════════════════════════════════════════════════════════════
class BinarySearchScheduler:
    """
    Uses Binary Search to find the correct insertion position for each
    new customer in an already-sorted queue (sorted by service_time).

    Binary Search reduces the number of comparisons from O(n) to O(log n)
    when finding the insertion point. The actual shift is still O(n),
    but the search phase is dramatically faster under large loads.

    Works with BOTH DS1 (SimpleQueue) and DS2 (MinHeap):
      - DS1 mode: binary search on the sorted list, then insert.
      - DS2 mode: binary search on shadow list, insert, rebuild heap.

    Time Complexity (find position): O(log n)
    Time Complexity (insert + shift): O(n)
    """

    def __init__(self, ds_mode: str = "queue") -> None:
        self.ds_mode   = ds_mode
        self._sorted:  list       = []          # always-sorted shadow list
        self._heap:    MinHeap    = MinHeap()

    # ── Public interface ──────────────────────────────────────────────────────
    def add_customer(self, customer: Customer) -> None:
        """
        Find insertion position with Binary Search, then insert. O(log n) search + O(n) shift.
        """
        pos = self._binary_search_position(customer.service_time)
        self._sorted.insert(pos, customer)      # O(n) list shift

        if self.ds_mode == "heap":
            self._rebuild_heap()

    def next_customer(self) -> Customer | None:
        """Return and remove the next customer (front of sorted list). O(1) / O(log n)."""
        if not self._sorted:
            return None
        customer = self._sorted.pop(0)          # O(n) shift — inherent to list
        if self.ds_mode == "heap" and not self._heap.is_empty():
            self._heap.extract_min()
        return customer

    def peek_next(self) -> Customer | None:
        if not self._sorted:
            return None
        return self._sorted[0]

    def size(self) -> int:
        return len(self._sorted)

    def is_empty(self) -> bool:
        return len(self._sorted) == 0

    def waiting_list(self) -> list:
        return list(self._sorted)

    def clear(self) -> None:
        self._sorted.clear()
        self._heap.clear()

    # ── Core algorithm ────────────────────────────────────────────────────────
    def _binary_search_position(self, target_key: float) -> int:
        """
        Classic Binary Search — find the index where target_key should
        be inserted to keep self._sorted in ascending order.

        Invariant: self._sorted is always sorted by service_time.

        Time Complexity: O(log n)
        Space Complexity: O(1)

        Returns the insertion index (0 ≤ index ≤ len(self._sorted)).
        """
        low  = 0
        high = len(self._sorted)

        while low < high:
            mid = (low + high) // 2
            if self._sorted[mid].service_time < target_key:
                low = mid + 1       # target is in the right half
            else:
                high = mid          # target is in the left half or at mid

        return low                  # insertion point

    def _rebuild_heap(self) -> None:
        """Sync the MinHeap with the current sorted list. O(n)."""
        from modules.data_structures import HeapNode
        nodes = [HeapNode(c.service_time, c) for c in self._sorted]
        self._heap.clear()
        self._heap.build_heap(nodes)
