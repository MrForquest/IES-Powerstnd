"""Company model and simple AI for the simulator."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .components import (
    CompanySnapshot,
    ConsumerContract,
    ContractOpportunity,
    Generator,
    MarketOffer,
    SmartGridNode,
    UpgradeModule,
)
from .world import World


@dataclass
class StrategyPreferences:
    """Weights that guide automated decision making."""

    risk_appetite: float = 0.5
    innovation_focus: float = 0.5
    ecology_focus: float = 0.5
    reliability_focus: float = 0.5


@dataclass
class Company:
    """Represents a market participant."""

    name: str
    world: World
    funds: float
    preferences: StrategyPreferences
    rng: random.Random
    is_player: bool = False
    generators: List[Generator] = field(default_factory=list)
    contracts: List[ConsumerContract] = field(default_factory=list)
    grid: Dict[str, SmartGridNode] = field(default_factory=dict)
    active_locations: List[str] = field(default_factory=list)
    reputation: float = 0.6
    waste_debt: float = 0.0
    history: List[Dict[str, float]] = field(default_factory=list)

    def snapshot(self) -> CompanySnapshot:
        demand = sum(contract.demand_mwh for contract in self.contracts if contract.active)
        generation = sum(generator.archetype.base_capacity for generator in self.generators)
        renewable_capacity = sum(
            generator.archetype.base_capacity * generator.archetype.renewable_share
            for generator in self.generators
        )
        renewable_share = renewable_capacity / generation if generation else 0.0
        return CompanySnapshot(
            name=self.name,
            funds=self.funds,
            total_generation=generation,
            total_demand=demand,
            renewable_share=renewable_share,
            reputation=self.reputation,
            active_locations=list(self.active_locations),
        )

    # --- market interactions -------------------------------------------------
    def prepare_bid(self, offer: MarketOffer) -> Optional[float]:
        if offer.kind == "generator":
            return self._prepare_generator_bid(offer)
        if offer.kind == "upgrade":
            return self._prepare_upgrade_bid(offer)
        return None

    def _prepare_generator_bid(self, offer: MarketOffer) -> Optional[float]:
        archetype = offer.payload
        best_location = self._best_location_for_generator(archetype)
        if not best_location:
            return None
        demand_gap = self._location_demand_gap(best_location.name)
        if demand_gap <= 0:
            if self.preferences.risk_appetite < 0.6:
                return None
        base_value = archetype.base_cost * (0.9 + self.preferences.risk_appetite * 0.3)
        climate_bonus = best_location.climate_modifier(archetype)
        demand_factor = 1.0 + max(0.0, demand_gap) / 800.0
        eco_bonus = 1.0 + (archetype.renewable_share - 0.5) * self.preferences.ecology_focus
        estimated_value = base_value * climate_bonus * demand_factor * eco_bonus
        bid = min(offer.base_price * 1.1, estimated_value)
        bid = min(bid, self.funds * 0.85)
        if bid < offer.min_bid or bid <= 0:
            return None
        return bid

    def _prepare_upgrade_bid(self, offer: MarketOffer) -> Optional[float]:
        if not self.generators and not self.grid:
            return None
        module = offer.payload
        benefit = 0.0
        if module.efficiency_bonus or module.capacity_bonus:
            target = self._most_stressed_generator()
            if not target:
                return None
            benefit += (module.efficiency_bonus + module.capacity_bonus) * 180_000
        if module.waste_reduction:
            benefit += module.waste_reduction * 60_000 * self.preferences.ecology_focus
        if module.loss_reduction or module.automation_bonus:
            benefit += (module.loss_reduction + module.automation_bonus) * 120_000
        bid = min(offer.base_price * 1.05, benefit)
        bid = min(bid, self.funds * 0.5)
        if bid < offer.min_bid or bid <= 0:
            return None
        return bid

    def complete_purchase(self, offer: MarketOffer, price: float) -> None:
        if price > self.funds:
            return
        self.funds -= price
        if offer.kind == "generator":
            archetype = offer.payload
            location = self._best_location_for_generator(archetype)
            if not location:
                location = self._ensure_any_location()
            generator = Generator(
                name=f"{archetype.name}-{len(self.generators) + 1}",
                archetype=archetype,
                location=location.name,
            )
            self.generators.append(generator)
        elif offer.kind == "upgrade":
            module = offer.payload
            self._install_module(module)

    def prepare_contract_bid(self, opportunity: ContractOpportunity) -> Optional[float]:
        supply = self._estimate_monthly_supply(opportunity.location)
        demand_gap = opportunity.demand_mwh - supply
        if demand_gap > opportunity.demand_mwh * 0.5:
            return None
        cost_estimate = self._estimate_marginal_cost()
        margin = 0.18 - self.preferences.risk_appetite * 0.08
        reliability = self.preferences.reliability_focus
        price = cost_estimate * (1.0 + margin + reliability * 0.05)
        if opportunity.is_public:
            price *= 0.95
        price = max(opportunity.floor_price, min(price, opportunity.ceiling_price))
        if price <= opportunity.floor_price and self.preferences.risk_appetite < 0.7:
            return None
        return price

    def accept_contract(self, opportunity: ContractOpportunity, price: float) -> None:
        contract = ConsumerContract(
            consumer_name=opportunity.name,
            location=opportunity.location,
            demand_mwh=opportunity.demand_mwh,
            duration_months=opportunity.duration_months,
            price_per_mwh=price,
            penalty_per_mwh=price * 0.9,
            reliability_requirement=opportunity.reliability_requirement,
            renewable_requirement=opportunity.renewable_requirement,
            remaining_months=opportunity.duration_months,
            is_public=opportunity.is_public,
        )
        self.contracts.append(contract)

    # --- operations ---------------------------------------------------------
    def operate_month(self) -> Dict[str, float]:
        total_energy = 0.0
        total_costs = 0.0
        total_waste = 0.0
        renewable_energy = 0.0
        maintenance_costs = 0.0
        for generator in self.generators:
            location = self.world.locations.get(generator.location)
            grid_node = self.grid.get(generator.location)
            energy, cost, waste, renewable = generator.monthly_output(
                climate=location.climate if location else None,
                grid_node=grid_node,
                rng=self.rng,
            )
            if grid_node:
                losses = energy * grid_node.loss_rate
                energy = max(0.0, energy - losses)
                maintenance_costs += grid_node.maintenance
            total_energy += energy
            total_costs += cost
            total_waste += waste
            renewable_energy += renewable
        waste_costs = total_waste * self.world.waste_disposal_cost
        active_contracts = [c for c in self.contracts if c.active]
        active_contracts.sort(key=lambda c: (c.penalty_per_mwh, c.price_per_mwh), reverse=True)
        renewable_share = renewable_energy / total_energy if total_energy else 0.0
        energy_left = total_energy
        revenue = 0.0
        penalties = 0.0
        reliability_total = 0.0
        for contract in active_contracts:
            delivered = min(contract.demand_mwh, energy_left)
            rev, penalty, reliability = contract.fulfill(delivered, renewable_share)
            revenue += rev
            penalties += penalty
            reliability_total += reliability
            energy_left -= delivered
            contract.advance()
        reliability_average = (
            reliability_total / len(active_contracts) if active_contracts else 1.0
        )
        location_maintenance = sum(
            self.world.locations[loc].maintenance_cost for loc in self.active_locations
        )
        total_expenses = total_costs + waste_costs + penalties + maintenance_costs + location_maintenance
        self.funds += revenue - total_expenses
        self.reputation = 0.6 * self.reputation + 0.4 * reliability_average
        record = {
            "revenue": revenue,
            "expenses": total_expenses,
            "energy": total_energy,
            "waste": total_waste,
            "renewable_share": renewable_share,
            "reliability": reliability_average,
            "contracts": float(len(active_contracts)),
        }
        self.history.append(record)
        self._retire_completed_contracts()
        self._maintain_grid()
        return record

    def _maintain_grid(self) -> None:
        for node in self.grid.values():
            if self.funds <= 0:
                break
            if node.loss_rate > 0.12 and self.funds > 200_000:
                invest = min(self.funds * 0.05, 150_000)
                node.invest(invest)
                self.funds -= invest

    def _retire_completed_contracts(self) -> None:
        self.contracts = [contract for contract in self.contracts if contract.active]

    # --- planning -----------------------------------------------------------
    def evaluate_expansion(self, year: int) -> Optional[str]:
        options = [
            loc
            for loc in self.world.iterate_locations()
            if loc.name not in self.active_locations and loc.unlock_year <= year
        ]
        if not options or self.funds < 500_000:
            return None
        options.sort(key=lambda loc: loc.strategic_value, reverse=True)
        for location in options:
            required = location.development_cost * 0.8
            if self.funds > required:
                self.funds -= location.development_cost
                self.active_locations.append(location.name)
                self.grid[location.name] = SmartGridNode(
                    location=location.name,
                    capacity_limit=location.strategic_value * 1_200.0,
                    loss_rate=0.15 * location.grid_complexity,
                    automation=0.1,
                    maintenance=location.maintenance_cost * 0.1,
                    storage_capacity=location.strategic_value * 200.0,
                )
                return location.name
        return None

    # --- helper utilities ---------------------------------------------------
    def _best_location_for_generator(self, archetype) -> Optional[object]:
        candidates = [
            self.world.locations[name]
            for name in self.active_locations
            if name in self.world.locations
        ]
        if not candidates:
            return None
        candidates.sort(
            key=lambda loc: (
                loc.climate_modifier(archetype),
                -self._location_demand_gap(loc.name),
            ),
            reverse=True,
        )
        return candidates[0]

    def _ensure_any_location(self):
        if self.active_locations:
            return self.world.locations[self.active_locations[0]]
        if not self.world.locations:
            raise ValueError("World has no locations")
        any_location = next(iter(self.world.locations.values()))
        self.active_locations.append(any_location.name)
        self.grid[any_location.name] = SmartGridNode(
            location=any_location.name,
            capacity_limit=any_location.strategic_value * 1_000.0,
            loss_rate=0.2,
            automation=0.05,
            maintenance=any_location.maintenance_cost * 0.1,
            storage_capacity=any_location.strategic_value * 150.0,
        )
        return any_location

    def _location_demand_gap(self, location_name: str) -> float:
        demand = sum(
            contract.demand_mwh
            for contract in self.contracts
            if contract.location == location_name and contract.active
        )
        supply = sum(
            generator.archetype.base_capacity * generator.archetype.base_efficiency
            for generator in self.generators
            if generator.location == location_name
        )
        return demand - supply

    def _most_stressed_generator(self) -> Optional[Generator]:
        if not self.generators:
            return None
        self.generators.sort(
            key=lambda gen: (
                self._location_demand_gap(gen.location),
                -gen.condition,
            ),
            reverse=True,
        )
        return self.generators[0]

    def _install_module(self, module: UpgradeModule) -> None:
        if module.loss_reduction or module.automation_bonus:
            if not self.grid:
                return
            target = max(self.grid.values(), key=lambda node: node.loss_rate)
            target.apply_module(module)
            return
        target_generator = self._most_stressed_generator()
        if target_generator:
            target_generator.install_module(module)

    def _estimate_monthly_supply(self, location_name: str) -> float:
        total = 0.0
        for generator in self.generators:
            if generator.location != location_name:
                continue
            total += (
                generator.archetype.base_capacity
                * generator.archetype.base_efficiency
            )
        return total

    def _estimate_marginal_cost(self) -> float:
        if not self.generators:
            return 140.0
        costs: List[float] = []
        for generator in self.generators:
            energy = max(
                1.0,
                generator.archetype.base_capacity * generator.archetype.base_efficiency,
            )
            cost = (
                generator.archetype.maintenance_cost / energy
                + generator.archetype.fuel_cost_per_mwh
                + 8.0
            )
            costs.append(cost)
        return sum(costs) / len(costs)


__all__ = ["Company", "StrategyPreferences"]
