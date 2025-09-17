"""World generation utilities."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .components import ClimateProfile, Location


@dataclass
class World:
    """Mutable world state shared by all companies."""

    base_year: int
    seed: int
    waste_disposal_cost: float = 45.0
    environmental_pressure: float = 0.5
    inflation_rate: float = 0.015
    climate_drift: float = 0.01
    rng: random.Random = field(init=False)
    locations: Dict[str, Location] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def add_location(self, location: Location) -> None:
        self.locations[location.name] = location

    def generate_locations(self, count: int) -> List[Location]:
        generated: List[Location] = []
        for index in range(count):
            location = self._create_location(index)
            self.add_location(location)
            generated.append(location)
        return generated

    def _create_location(self, index: int) -> Location:
        rng = self.rng
        climate = ClimateProfile(
            solar=rng.uniform(0.2, 0.95),
            wind=rng.uniform(0.1, 0.9),
            hydro=rng.uniform(0.05, 0.95),
            geothermal=rng.uniform(0.05, 0.8),
            temperature=rng.uniform(0.2, 0.9),
            precipitation=rng.uniform(0.1, 0.9),
            pollution=rng.uniform(0.1, 0.6),
        )
        unlock_year = self.base_year + rng.randint(0, 4)
        base_cost = rng.uniform(1.5, 4.0) * 1_000_000
        maintenance = base_cost * rng.uniform(0.01, 0.025)
        strategic_value = rng.uniform(0.8, 1.5)
        consumers = [f"Consumer-{index}-{i}" for i in range(rng.randint(2, 5))]
        return Location(
            name=f"Zone-{index + 1}",
            climate=climate,
            grid_complexity=rng.uniform(0.6, 1.4),
            development_cost=base_cost,
            maintenance_cost=maintenance,
            unlock_year=unlock_year,
            consumers=consumers,
            strategic_value=strategic_value,
        )

    def iterate_locations(self) -> Iterable[Location]:
        return self.locations.values()

    def apply_climate_drift(self) -> None:
        for location in self.locations.values():
            climate = location.climate
            drift = self.rng.uniform(-self.climate_drift, self.climate_drift)
            climate.temperature = max(0.1, min(0.95, climate.temperature + drift))
            climate.pollution = max(0.05, min(0.95, climate.pollution + drift * 0.5))


__all__ = ["World"]
