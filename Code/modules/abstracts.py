"""
abstracts.py
============
Abstract base classes for the Smart Bank Service Simulation.

AbstractEntity  – base for all moving parts (e.g. Customer)
AbstractResource – base for all constrained resources (e.g. ServiceCounter)

Every concrete class MUST implement the abstract methods or Python will
raise a TypeError at instantiation time.
"""

from abc import ABC, abstractmethod


# ─────────────────────────────────────────────────────────────────────────────
class AbstractEntity(ABC):
    """
    Base class for every entity that moves through the simulation.
    Time Complexity: O(1) for all base operations.
    """

    def __init__(self, entity_id: str, created_at: float) -> None:
        self._entity_id: str   = entity_id
        self._created_at: float = created_at

    def get_id(self) -> str:
        """Return the unique entity identifier."""
        return self._entity_id

    def get_created_at(self) -> float:
        """Return the simulation clock time when this entity was created."""
        return self._created_at

    @abstractmethod
    def get_state(self) -> dict:
        """Return a snapshot of the entity's current state as a dictionary."""
        ...


# ─────────────────────────────────────────────────────────────────────────────
class AbstractResource(ABC):
    """
    Base class for every constrained resource in the simulation.
    Time Complexity: O(1) for all base operations.
    """

    def __init__(self, resource_id: str) -> None:
        self._resource_id: str    = resource_id
        self._is_available: bool  = True

    def get_resource_id(self) -> str:
        return self._resource_id

    def is_free(self) -> bool:
        """Return True if the resource is currently idle."""
        return self._is_available

    @abstractmethod
    def assign(self) -> None:
        """Mark the resource as busy."""
        ...

    @abstractmethod
    def release(self) -> None:
        """Mark the resource as available."""
        ...
