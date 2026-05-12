"""
entities.py
===========
Concrete entity and resource classes:

  Customer        – a bank customer (extends AbstractEntity)
  ServiceCounter  – a bank teller counter (extends AbstractResource)
"""

from __future__ import annotations
from modules.abstracts import AbstractEntity, AbstractResource


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY LEVELS  (lower number = higher priority)
# ─────────────────────────────────────────────────────────────────────────────
PRIORITY_VIP     = 0
PRIORITY_ELDERLY = 1
PRIORITY_NORMAL  = 2

PRIORITY_LABELS = {
    PRIORITY_VIP:     "VIP",
    PRIORITY_ELDERLY: "Elderly",
    PRIORITY_NORMAL:  "Normal",
}

PRIORITY_COLORS = {
    PRIORITY_VIP:     "#FFD700",   # gold
    PRIORITY_ELDERLY: "#74B9FF",   # light blue
    PRIORITY_NORMAL:  "#B2BEC3",   # grey
}


# ─────────────────────────────────────────────────────────────────────────────
class Customer(AbstractEntity):
    """
    Represents one bank customer.

    Attributes
    ----------
    customer_id   : unique string identifier
    arrival_time  : simulation clock time of arrival
    service_time  : how many seconds this customer needs at the counter
    priority      : 0=VIP, 1=Elderly, 2=Normal
    start_service : clock time service began (set by counter)
    end_service   : clock time service ended  (set by counter)

    Time Complexity: O(1) for all operations.
    """

    _counter: int = 0   # class-level auto-increment

    def __init__(
        self,
        arrival_time: float,
        service_time: float,
        priority: int = PRIORITY_NORMAL,
    ) -> None:
        Customer._counter += 1
        super().__init__(f"C{Customer._counter:04d}", arrival_time)

        self.arrival_time:  float = arrival_time
        self.service_time:  float = service_time   # used by Insertion Sort / Binary Search
        self.priority:      int   = priority
        self.start_service: float = -1.0
        self.end_service:   float = -1.0
        self.assigned_counter: int = -1

    # ── derived KPIs ──────────────────────────────────────────────────────────
    def wait_time(self) -> float:
        """Time spent waiting before service began. O(1)."""
        if self.start_service < 0:
            return 0.0
        return max(0.0, self.start_service - self.arrival_time)

    def turnaround_time(self) -> float:
        """Total time in the system. O(1)."""
        if self.end_service < 0:
            return 0.0
        return max(0.0, self.end_service - self.arrival_time)

    def get_state(self) -> dict:
        return {
            "id":            self._entity_id,
            "arrival":       self.arrival_time,
            "service_time":  self.service_time,
            "priority":      PRIORITY_LABELS[self.priority],
            "wait":          self.wait_time(),
            "turnaround":    self.turnaround_time(),
        }

    def priority_label(self) -> str:
        return PRIORITY_LABELS[self.priority]

    def color(self) -> str:
        return PRIORITY_COLORS[self.priority]

    @classmethod
    def reset_counter(cls) -> None:
        cls._counter = 0

    def __repr__(self) -> str:
        return (f"Customer({self._entity_id}, arr={self.arrival_time:.1f}, "
                f"svc={self.service_time:.1f}, pri={self.priority_label()})")


# ─────────────────────────────────────────────────────────────────────────────
class ServiceCounter(AbstractResource):
    """
    Represents one bank teller counter.

    Time Complexity: O(1) for all operations.
    """

    def __init__(self, counter_id: int) -> None:
        super().__init__(f"Counter-{counter_id}")
        self.counter_id:      int            = counter_id
        self._current_customer: Customer | None = None
        self._idle_since:     float          = 0.0
        self._total_idle:     float          = 0.0
        self._served:         int            = 0

    # ── AbstractResource implementation ───────────────────────────────────────
    def assign(self) -> None:
        self._is_available = False

    def release(self) -> None:
        self._is_available = True
        self._current_customer = None

    # ── Business logic ────────────────────────────────────────────────────────
    def start_serving(self, customer: Customer, clock: float) -> float:
        """
        Assign customer to this counter and return the finish time.
        Also accumulates idle time. O(1).
        """
        self._total_idle += max(0.0, clock - self._idle_since)
        self._current_customer = customer
        customer.start_service    = clock
        customer.assigned_counter = self.counter_id
        self.assign()
        finish = clock + customer.service_time
        customer.end_service = finish
        self._served += 1
        return finish

    def finish_serving(self, clock: float) -> None:
        """Release the counter at the given clock time. O(1)."""
        self._idle_since = clock
        self.release()

    def idle_time(self) -> float:
        return self._total_idle

    def customers_served(self) -> int:
        return self._served

    def current_customer(self) -> Customer | None:
        return self._current_customer

    def __repr__(self) -> str:
        status = "FREE" if self._is_available else f"BUSY({self._current_customer})"
        return f"ServiceCounter({self._resource_id}, {status})"
