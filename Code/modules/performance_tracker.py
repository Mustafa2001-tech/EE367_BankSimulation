"""
performance_tracker.py
======================
PerformanceTracker – records KPIs for one simulation scenario run.

KPIs tracked
------------
1. Execution Time (ms)       – wall-clock time for the full run
2. Average Wait Time (s)     – mean customer wait before service
3. Peak Memory Usage (KB)    – tracemalloc peak snapshot
4. Throughput (customers/s)  – customers served per simulation second
"""

from __future__ import annotations
import time
import tracemalloc
from modules.entities import Customer


class PerformanceTracker:
    """
    Hooks into the simulation engine to measure and store KPIs.
    All measurement methods are O(1) except export which is O(n).
    """

    def __init__(self, scenario_label: str) -> None:
        self.scenario_label = scenario_label

        # Raw data
        self._wait_times:   list[float] = []
        self._start_time:   float       = 0.0
        self._end_time:     float       = 0.0
        self._peak_memory:  int         = 0        # bytes
        self._served_count: int         = 0
        self._sim_duration: float       = 0.0

        # Computed results (filled after stop())
        self.exec_time_ms:   float = 0.0
        self.avg_wait_s:     float = 0.0
        self.memory_kb:      float = 0.0
        self.throughput:     float = 0.0

        self._running = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def start(self) -> None:
        """Begin tracking. O(1)."""
        self._wait_times.clear()
        self._served_count = 0
        tracemalloc.start()
        self._start_time = time.perf_counter()
        self._running = True

    def stop(self, sim_duration: float) -> None:
        """
        Stop tracking and compute final KPIs. O(n) for average.
        sim_duration: total simulated time in seconds.
        """
        self._end_time   = time.perf_counter()
        _, peak          = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._peak_memory  = peak
        self._sim_duration = sim_duration
        self._running      = False
        self._compute()

    def record_customer(self, customer: Customer) -> None:
        """Call after each customer finishes service. O(1)."""
        self._wait_times.append(customer.wait_time())
        self._served_count += 1

    # ── Internal ──────────────────────────────────────────────────────────────
    def _compute(self) -> None:
        """Derive all KPI values from raw data. O(n)."""
        elapsed            = self._end_time - self._start_time
        self.exec_time_ms  = round(elapsed * 1000, 2)
        self.avg_wait_s    = round(
            sum(self._wait_times) / len(self._wait_times)
            if self._wait_times else 0.0, 2
        )
        self.memory_kb     = round(self._peak_memory / 1024, 2)
        self.throughput    = round(
            self._served_count / self._sim_duration
            if self._sim_duration > 0 else 0.0, 4
        )

    # ── Export ────────────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "Scenario":          self.scenario_label,
            "Exec Time (ms)":    self.exec_time_ms,
            "Avg Wait (s)":      self.avg_wait_s,
            "Memory (KB)":       self.memory_kb,
            "Throughput (c/s)":  self.throughput,
        }

    def summary(self) -> str:
        return (
            f"[{self.scenario_label}] "
            f"ExecTime={self.exec_time_ms}ms | "
            f"AvgWait={self.avg_wait_s}s | "
            f"Memory={self.memory_kb}KB | "
            f"Throughput={self.throughput}c/s"
        )
