"""
simulation_engine.py
====================
SimulationEngine  – abstract parent: event loop, clock, threading glue
BankSimulation    – concrete child: bank-specific arrival & serving logic

Four scenarios
--------------
  1 → SimpleQueue  + InsertionSort
  2 → MinHeap      + InsertionSort
  3 → SimpleQueue  + BinarySearch
  4 → MinHeap      + BinarySearch
"""

from __future__ import annotations
import random
import queue
import threading
import time
from abc import ABC, abstractmethod
from typing import Callable, Optional

from modules.entities    import Customer, ServiceCounter, PRIORITY_NORMAL, PRIORITY_ELDERLY, PRIORITY_VIP
from modules.algorithms  import InsertionSortScheduler, BinarySearchScheduler
from modules.performance_tracker import PerformanceTracker


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
SCENARIO_LABELS = {
    1: "Sc.1  Queue + Insertion Sort",
    2: "Sc.2  Heap  + Insertion Sort",
    3: "Sc.3  Queue + Binary Search",
    4: "Sc.4  Heap  + Binary Search",
}


def build_scheduler(scenario: int):
    """Factory: return the correct scheduler for the given scenario. O(1)."""
    ds_mode = "queue" if scenario in (1, 3) else "heap"
    if scenario in (1, 2):
        return InsertionSortScheduler(ds_mode=ds_mode)
    else:
        return BinarySearchScheduler(ds_mode=ds_mode)


# ═════════════════════════════════════════════════════════════════════════════
# ABSTRACT ENGINE
# ═════════════════════════════════════════════════════════════════════════════
class SimulationEngine(ABC):
    """
    Parent class responsible for:
      - Maintaining the simulation clock
      - Running the event loop on a background thread
      - Communicating updates to the GUI via a thread-safe queue
    """

    def __init__(
        self,
        num_counters: int,
        arrival_rate: float,
        service_min:  float,
        service_max:  float,
        sim_duration: float,
        speed:        float = 1.0,
    ) -> None:
        self.num_counters = num_counters
        self.arrival_rate = arrival_rate      # customers per second
        self.service_min  = service_min
        self.service_max  = service_max
        self.sim_duration = sim_duration      # total simulated seconds
        self.speed        = speed             # wall-clock multiplier

        self.clock:   float = 0.0
        self.running: bool  = False
        self._thread: Optional[threading.Thread] = None

        # GUI communication channel
        self.ui_queue: queue.Queue = queue.Queue()

    def start(self) -> None:
        """Launch simulation on a background thread."""
        self.running = True
        self.clock   = 0.0
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the event loop to halt."""
        self.running = False

    def _push(self, event_type: str, data: dict) -> None:
        """Send a UI update message. O(1)."""
        self.ui_queue.put({"type": event_type, "data": data})

    @abstractmethod
    def _run_loop(self) -> None:
        """The main event loop — implemented by child class."""
        ...


# ═════════════════════════════════════════════════════════════════════════════
# BANK SIMULATION  (concrete child)
# ═════════════════════════════════════════════════════════════════════════════
class BankSimulation(SimulationEngine):
    """
    Simulates bank customer arrivals, queuing, and service for one scenario.

    The simulation runs in simulated time (not real time).
    A sleep is added between events to allow the GUI to animate smoothly.
    """

    def __init__(
        self,
        scenario:     int,
        num_counters: int   = 3,
        arrival_rate: float = 0.5,    # customers per sim-second
        service_min:  float = 3.0,
        service_max:  float = 10.0,
        sim_duration: float = 120.0,  # simulated seconds
        speed:        float = 1.0,
        log_cb:       Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(num_counters, arrival_rate, service_min, service_max, sim_duration, speed)
        self.scenario      = scenario
        self.label         = SCENARIO_LABELS[scenario]
        self.log_cb        = log_cb or (lambda msg: None)

        # Data structures & algorithm
        self.scheduler     = build_scheduler(scenario)
        self.tracker       = PerformanceTracker(self.label)

        # Resources
        Customer.reset_counter()
        self.counters: list[ServiceCounter] = [
            ServiceCounter(i + 1) for i in range(num_counters)
        ]

        # Statistics
        self.served_customers: list[Customer] = []
        self.total_arrivals:   int = 0

    # ── Main event loop ───────────────────────────────────────────────────────
    def _run_loop(self) -> None:
        """
        Discrete-event simulation loop.
        Advances the clock by inter-arrival times drawn from an
        exponential distribution (realistic for queuing theory).

        Time Complexity per iteration: O(log n) with heap, O(n) with queue.
        """
        self.tracker.start()
        next_arrival = random.expovariate(self.arrival_rate)
        finish_events: list[tuple[float, ServiceCounter]] = []  # (finish_time, counter)

        self.clock = 0.0

        while self.running and self.clock < self.sim_duration:

            # ── 1. Process any finish events that are due ──────────────────
            due = [fe for fe in finish_events if fe[0] <= self.clock]
            for (finish_time, counter) in due:
                finish_events.remove((finish_time, counter))
                counter.finish_serving(finish_time)
                self.log_cb(f"[{finish_time:.1f}s] {counter._resource_id} finished serving")
                self._push("counter_free", {"counter_id": counter.counter_id})

            # ── 2. Assign waiting customers to free counters ───────────────
            for counter in self.counters:
                if counter.is_free() and not self.scheduler.is_empty():
                    customer = self.scheduler.next_customer()
                    finish_t = counter.start_serving(customer, self.clock)
                    finish_events.append((finish_t, counter))
                    self.log_cb(
                        f"[{self.clock:.1f}s] {counter._resource_id} serving "
                        f"{customer.get_id()} ({customer.priority_label()}, "
                        f"svc={customer.service_time:.1f}s)"
                    )
                    self._push("serving", {
                        "counter_id": counter.counter_id,
                        "customer":   customer.get_state(),
                    })

            # ── 3. Generate next arrival if due ───────────────────────────
            if next_arrival <= self.clock:
                priority = random.choices(
                    [PRIORITY_VIP, PRIORITY_ELDERLY, PRIORITY_NORMAL],
                    weights=[10, 20, 70]
                )[0]
                svc_time = round(random.uniform(self.service_min, self.service_max), 2)
                cust = Customer(
                    arrival_time=self.clock,
                    service_time=svc_time,
                    priority=priority,
                )
                self.scheduler.add_customer(cust)
                self.total_arrivals += 1
                self.log_cb(
                    f"[{self.clock:.1f}s] {cust.get_id()} arrived "
                    f"({cust.priority_label()}, svc={svc_time:.1f}s)"
                )
                self._push("arrival", {
                    "customer":    cust.get_state(),
                    "queue_size":  self.scheduler.size(),
                    "queue_list":  [c.get_state() for c in self.scheduler.waiting_list()],
                })

                # schedule next arrival
                next_arrival += random.expovariate(self.arrival_rate)

            # ── 4. Advance clock ──────────────────────────────────────────
            self.clock += 0.5   # step 0.5 simulated seconds
            time.sleep(0.05 / self.speed)   # real-time pacing

            # ── 5. Periodic KPI push ──────────────────────────────────────
            if int(self.clock) % 5 == 0:
                self._push("kpi_tick", {
                    "clock":      self.clock,
                    "queue_size": self.scheduler.size(),
                })

        # ── Drain remaining finish events ──────────────────────────────────
        for (finish_time, counter) in finish_events:
            customer = counter.current_customer()
            if customer:
                counter.finish_serving(finish_time)
                self.tracker.record_customer(customer)
                self.served_customers.append(customer)

        # ── Drain remaining queue ──────────────────────────────────────────
        while not self.scheduler.is_empty():
            c = self.scheduler.next_customer()
            if c:
                self.served_customers.append(c)
                self.tracker.record_customer(c)

        self.tracker.stop(self.sim_duration)
        self.running = False
        self._push("done", {"tracker": self.tracker.to_dict(), "label": self.label})
        self.log_cb(f"\n{'─'*40}")
        self.log_cb(self.tracker.summary())
        self.log_cb(f"{'─'*40}\n")
