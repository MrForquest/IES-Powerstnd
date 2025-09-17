"""Core data structures for the energy company simulator."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Tuple


@dataclass
class ClimateProfile:
    """Represents the climatic conditions that influence generation."""

    solar: float
    wind: float
    hydro: float
    geothermal: float
    temperature: float
    precipitation: float
    pollution: float

    def clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))

    def modifier(self, climate_weights: Dict[str, float]) -> float:
        """Return a multiplicative modifier for a generator archetype."""

        base = 1.0
        for attr, weight in climate_weights.items():
            climate_value = getattr(self, attr, 0.5)
            normalized = climate_value - 0.5
            base += normalized * weight
        return max(0.2, base)


@dataclass
class Location:
    """A procedurally generated location available in the world."""

    name: str
    climate: ClimateProfile
    grid_complexity: float
    development_cost: float
    maintenance_cost: float
    unlock_year: int
    consumers: List[str] = field(default_factory=list)
    strategic_value: float = 1.0

    def climate_modifier(self, archetype: "GeneratorArchetype") -> float:
        return self.climate.modifier(archetype.climate_weights)


@dataclass(frozen=True)
class GeneratorArchetype:
    """Template that defines the base properties for a generator."""

    name: str
    tech_level: str
    base_capacity: float
    base_efficiency: float
    variability: float
    base_cost: float
    maintenance_cost: float
    fuel_cost_per_mwh: float
    waste_rate: float
    emission_rate: float
    renewable_share: float
    climate_weights: Dict[str, float]
    description: str = ""


@dataclass
class UpgradeModule:
    """Installable improvement for generators or grid nodes."""

    name: str
    cost: float
    maintenance_cost: float
    efficiency_bonus: float = 0.0
    capacity_bonus: float = 0.0
    waste_reduction: float = 0.0
    loss_reduction: float = 0.0
    automation_bonus: float = 0.0
    description: str = ""


@dataclass
class SmartGridNode:
    """Represents the electrical network state within a location."""

    location: str
    capacity_limit: float
    loss_rate: float
    automation: float
    maintenance: float
    storage_capacity: float

    def apply_module(self, module: UpgradeModule) -> None:
        self.loss_rate = max(0.01, self.loss_rate * (1.0 - module.loss_reduction))
        self.automation += module.automation_bonus
        self.storage_capacity *= 1.0 + module.capacity_bonus
        self.maintenance += module.maintenance_cost

    def invest(self, amount: float) -> None:
        if amount <= 0:
            return
        improvement = math.log1p(amount / 100_000) * 0.05
        self.loss_rate = max(0.01, self.loss_rate * (1.0 - improvement))
        self.capacity_limit *= 1.0 + improvement
        self.automation += improvement * 0.5


@dataclass
class Generator:
    """An owned generator with mutable state."""

    name: str
    archetype: GeneratorArchetype
    location: str
    condition: float = 1.0
    capacity_modifier: float = 0.0
    efficiency_modifier: float = 0.0
    modules: List[UpgradeModule] = field(default_factory=list)
    age_months: int = 0

    def monthly_output(
        self,
        climate: Optional[ClimateProfile],
        grid_node: Optional[SmartGridNode],
        rng: random.Random,
    ) -> Tuple[float, float, float, float]:
        """Return (energy_mwh, cost, waste, renewable_energy)."""

        if climate is None:
            climate_factor = 1.0
        else:
            climate_factor = climate.modifier(self.archetype.climate_weights)
        variability = rng.uniform(
            1.0 - self.archetype.variability, 1.0 + self.archetype.variability
        )
        module_capacity = sum(module.capacity_bonus for module in self.modules)
        module_efficiency = sum(module.efficiency_bonus for module in self.modules)
        module_waste_reduction = sum(
            module.waste_reduction for module in self.modules
        )

        base_capacity = self.archetype.base_capacity * (1.0 + self.capacity_modifier)
        effective_capacity = base_capacity * (1.0 + module_capacity)
        effective_efficiency = (
            self.archetype.base_efficiency
            * self.condition
            * (1.0 + self.efficiency_modifier + module_efficiency)
        )
        energy = (
            effective_capacity * effective_efficiency * climate_factor * variability
        )
        if grid_node:
            automation_bonus = 1.0 + grid_node.automation * 0.02
            energy *= automation_bonus
        energy = max(0.0, energy)

        maintenance_cost = self.archetype.maintenance_cost
        fuel_cost = energy * self.archetype.fuel_cost_per_mwh
        module_maintenance = sum(module.maintenance_cost for module in self.modules)
        total_cost = maintenance_cost + module_maintenance + fuel_cost

        waste = (
            energy
            * self.archetype.waste_rate
            * max(0.0, 1.0 - module_waste_reduction)
        )
        renewable_energy = energy * self.archetype.renewable_share
        self.age_months += 1
        self.condition = max(0.5, self.condition - 0.003 - 0.001 * len(self.modules))
        return energy, total_cost, waste, renewable_energy

    def install_module(self, module: UpgradeModule) -> None:
        self.modules.append(module)


@dataclass
class ConsumerContract:
    """Represents an energy delivery contract with a consumer."""

    consumer_name: str
    location: str
    demand_mwh: float
    duration_months: int
    price_per_mwh: float
    penalty_per_mwh: float
    reliability_requirement: float
    renewable_requirement: float
    remaining_months: int
    is_public: bool = False

    def advance(self) -> None:
        self.remaining_months -= 1

    def fulfill(
        self, delivered_mwh: float, renewable_share: float
    ) -> Tuple[float, float, float]:
        shortage = max(0.0, self.demand_mwh - delivered_mwh)
        delivered = min(self.demand_mwh, delivered_mwh)
        revenue = delivered * self.price_per_mwh
        penalty = shortage * self.penalty_per_mwh
        reliability = 1.0 - (shortage / self.demand_mwh if self.demand_mwh else 0.0)
        compliance_penalty = 0.0
        if renewable_share < self.renewable_requirement:
            compliance_penalty = (self.renewable_requirement - renewable_share) * 2000
            penalty += compliance_penalty
        if reliability < self.reliability_requirement:
            penalty += (self.reliability_requirement - reliability) * 1500
        return revenue, penalty, reliability

    @property
    def active(self) -> bool:
        return self.remaining_months > 0


@dataclass
class GovernmentProgram:
    """State-led grant or subsidy programme."""

    name: str
    grant_amount: float
    requirement: Callable[["CompanySnapshot"], bool]
    description: str
    duration_months: int
    remaining_months: int

    def advance(self) -> None:
        self.remaining_months -= 1


@dataclass
class MarketOffer:
    """Offer that appears on the market for auction."""

    offer_id: str
    kind: str
    payload: object
    base_price: float
    min_bid: float
    description: str


@dataclass
class ContractOpportunity:
    """Tender description for consumer contracts."""

    name: str
    location: str
    demand_mwh: float
    duration_months: int
    ceiling_price: float
    floor_price: float
    renewable_requirement: float
    reliability_requirement: float
    is_public: bool


@dataclass
class AuctionResult:
    offer: MarketOffer
    winner: Optional[str]
    clearing_price: Optional[float]


@dataclass
class TenderResult:
    opportunity: ContractOpportunity
    winner: Optional[str]
    price: Optional[float]


@dataclass
class CompanySnapshot:
    """Immutable view of a company used for evaluation logic."""

    name: str
    funds: float
    total_generation: float
    total_demand: float
    renewable_share: float
    reputation: float
    active_locations: List[str]


def distribute_energy(
    demand: Iterable[ConsumerContract], energy: float
) -> Dict[str, float]:
    """Distribute energy greedily between contracts."""

    allocation: Dict[str, float] = {}
    remaining = energy
    for contract in demand:
        supplied = min(contract.demand_mwh, remaining)
        allocation[contract.consumer_name] = supplied
        remaining -= supplied
        if remaining <= 0:
            break
    return allocation


__all__ = [
    "AuctionResult",
    "ClimateProfile",
    "CompanySnapshot",
    "ConsumerContract",
    "ContractOpportunity",
    "Generator",
    "GeneratorArchetype",
    "GovernmentProgram",
    "Location",
    "MarketOffer",
    "SmartGridNode",
    "TenderResult",
    "UpgradeModule",
    "distribute_energy",
]
