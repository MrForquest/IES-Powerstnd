"""Market and auction logic for the simulator."""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, TYPE_CHECKING

from .components import (
    AuctionResult,
    ContractOpportunity,
    GeneratorArchetype,
    MarketOffer,
    TenderResult,
    UpgradeModule,
)
from .world import World

if TYPE_CHECKING:
    from .company import Company


GENERATOR_CATALOGUE: Tuple[GeneratorArchetype, ...] = (
    GeneratorArchetype(
        name="Helios Solar Farm",
        tech_level="current",
        base_capacity=620.0,
        base_efficiency=0.82,
        variability=0.22,
        base_cost=1_350_000.0,
        maintenance_cost=18_000.0,
        fuel_cost_per_mwh=0.0,
        waste_rate=0.006,
        emission_rate=0.02,
        renewable_share=1.0,
        climate_weights={"solar": 0.7, "temperature": 0.3},
        description="Модульные солнечные панели с автоматической очисткой.",
    ),
    GeneratorArchetype(
        name="Borealis Offshore Wind",
        tech_level="current",
        base_capacity=710.0,
        base_efficiency=0.78,
        variability=0.28,
        base_cost=1_800_000.0,
        maintenance_cost=24_000.0,
        fuel_cost_per_mwh=0.0,
        waste_rate=0.008,
        emission_rate=0.03,
        renewable_share=1.0,
        climate_weights={"wind": 0.8, "precipitation": 0.2},
        description="Крупные морские ветровые турбины со скоростным монтажом.",
    ),
    GeneratorArchetype(
        name="Cascade Hydro Complex",
        tech_level="current",
        base_capacity=900.0,
        base_efficiency=0.88,
        variability=0.15,
        base_cost=2_700_000.0,
        maintenance_cost=36_000.0,
        fuel_cost_per_mwh=0.0,
        waste_rate=0.004,
        emission_rate=0.02,
        renewable_share=1.0,
        climate_weights={"hydro": 0.7, "precipitation": 0.3},
        description="Гибкая ГЭС с системой быстрой регулировки потока.",
    ),
    GeneratorArchetype(
        name="Cyclone Gas Turbine",
        tech_level="current",
        base_capacity=820.0,
        base_efficiency=0.65,
        variability=0.1,
        base_cost=1_100_000.0,
        maintenance_cost=42_000.0,
        fuel_cost_per_mwh=23.0,
        waste_rate=0.02,
        emission_rate=0.35,
        renewable_share=0.1,
        climate_weights={"temperature": -0.2},
        description="Высокоэффективная газовая турбина с улавливанием CO₂.",
    ),
    GeneratorArchetype(
        name="Aquila Fusion Torch",
        tech_level="experimental",
        base_capacity=2500.0,
        base_efficiency=0.94,
        variability=0.05,
        base_cost=7_500_000.0,
        maintenance_cost=90_000.0,
        fuel_cost_per_mwh=6.0,
        waste_rate=0.012,
        emission_rate=0.05,
        renewable_share=0.85,
        climate_weights={"temperature": 0.1},
        description="Экспериментальный термоядерный реактор с магнитным удержанием.",
    ),
    GeneratorArchetype(
        name="Gaia Geo-Tap",
        tech_level="near_future",
        base_capacity=780.0,
        base_efficiency=0.9,
        variability=0.12,
        base_cost=2_100_000.0,
        maintenance_cost=30_000.0,
        fuel_cost_per_mwh=4.0,
        waste_rate=0.01,
        emission_rate=0.08,
        renewable_share=0.7,
        climate_weights={"geothermal": 0.8, "temperature": -0.1},
        description="Геотермальная станция глубокого бурения.",
    ),
    GeneratorArchetype(
        name="Stratos Solar Kite",
        tech_level="near_future",
        base_capacity=540.0,
        base_efficiency=0.87,
        variability=0.2,
        base_cost=1_600_000.0,
        maintenance_cost=20_000.0,
        fuel_cost_per_mwh=0.0,
        waste_rate=0.003,
        emission_rate=0.01,
        renewable_share=1.0,
        climate_weights={"solar": 0.6, "wind": 0.4},
        description="Парящие солнечно-ветровые платформы.",
    ),
    GeneratorArchetype(
        name="Luna Beam Relay",
        tech_level="future",
        base_capacity=1300.0,
        base_efficiency=0.96,
        variability=0.04,
        base_cost=5_500_000.0,
        maintenance_cost=110_000.0,
        fuel_cost_per_mwh=0.0,
        waste_rate=0.002,
        emission_rate=0.01,
        renewable_share=1.0,
        climate_weights={"solar": 0.9},
        description="Орбитальная солнечная станция с лазерной передачей энергии.",
    ),
)


UPGRADE_LIBRARY: Tuple[UpgradeModule, ...] = (
    UpgradeModule(
        name="AI Dispatch Core",
        cost=380_000.0,
        maintenance_cost=6_000.0,
        efficiency_bonus=0.08,
        description="Предиктивное управление нагрузкой и ремонтом.",
    ),
    UpgradeModule(
        name="Quantum Storage Matrix",
        cost=520_000.0,
        maintenance_cost=9_000.0,
        capacity_bonus=0.12,
        loss_reduction=0.15,
        description="Высокоемкая система хранения для сглаживания пиков.",
    ),
    UpgradeModule(
        name="Biofilter Loop",
        cost=210_000.0,
        maintenance_cost=4_000.0,
        waste_reduction=0.45,
        description="Модуль глубокой очистки отходов и выбросов.",
    ),
    UpgradeModule(
        name="Autonomous Drone Maintenance",
        cost=160_000.0,
        maintenance_cost=3_500.0,
        automation_bonus=0.4,
        description="Дроны для осмотра и мелкого ремонта сетей.",
    ),
)


@dataclass
class EnergyMarket:
    """Handles auctions, tenders and government interaction."""

    world: World
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        base_seed = self.seed if self.seed is not None else self.world.seed + 137
        self.rng = random.Random(base_seed)
        self.offer_counter = itertools.count(1)

    def _new_offer_id(self) -> str:
        return f"OFF-{next(self.offer_counter):04d}"

    def generator_offers(self, month: int) -> List[MarketOffer]:
        offers: List[MarketOffer] = []
        count = 2 + (month % 3 == 0)
        for archetype in self.rng.sample(GENERATOR_CATALOGUE, k=count):
            premium = self.rng.uniform(-0.08, 0.15)
            base_price = archetype.base_cost * (1.0 + premium)
            min_bid = base_price * 0.85
            offers.append(
                MarketOffer(
                    offer_id=self._new_offer_id(),
                    kind="generator",
                    payload=archetype,
                    base_price=base_price,
                    min_bid=min_bid,
                    description=archetype.description,
                )
            )
        return offers

    def upgrade_offers(self) -> List[MarketOffer]:
        count = self.rng.randint(1, 3)
        offers: List[MarketOffer] = []
        for module in self.rng.sample(UPGRADE_LIBRARY, k=count):
            price = module.cost * self.rng.uniform(0.9, 1.2)
            offers.append(
                MarketOffer(
                    offer_id=self._new_offer_id(),
                    kind="upgrade",
                    payload=module,
                    base_price=price,
                    min_bid=price * 0.9,
                    description=module.description,
                )
            )
        return offers

    def contract_opportunities(
        self, available_locations: Sequence[str], demand_factor: float
    ) -> List[ContractOpportunity]:
        opportunities: List[ContractOpportunity] = []
        if not available_locations:
            return opportunities
        count = self.rng.randint(1, max(1, len(available_locations)))
        for _ in range(count):
            location_name = self.rng.choice(available_locations)
            demand = self.rng.uniform(380.0, 1_200.0) * demand_factor
            duration = self.rng.choice([12, 18, 24, 36])
            ceiling = self.rng.uniform(110.0, 180.0)
            floor = ceiling * self.rng.uniform(0.65, 0.85)
            renewable_req = self.rng.uniform(0.2, 0.75)
            reliability_req = self.rng.uniform(0.85, 0.98)
            opportunities.append(
                ContractOpportunity(
                    name=f"Contract-{next(self.offer_counter):03d}",
                    location=location_name,
                    demand_mwh=demand,
                    duration_months=duration,
                    ceiling_price=ceiling,
                    floor_price=floor,
                    renewable_requirement=renewable_req,
                    reliability_requirement=reliability_req,
                    is_public=self.rng.random() > 0.4,
                )
            )
        return opportunities

    def run_auctions(
        self, offers: Sequence[MarketOffer], companies: Sequence["Company"]
    ) -> List[AuctionResult]:
        results: List[AuctionResult] = []
        for offer in offers:
            bids: List[Tuple[float, "Company"]] = []
            for company in companies:
                bid = company.prepare_bid(offer)
                if bid is None:
                    continue
                if bid >= offer.min_bid:
                    bids.append((bid, company))
            if not bids:
                results.append(AuctionResult(offer=offer, winner=None, clearing_price=None))
                continue
            bids.sort(key=lambda item: item[0], reverse=True)
            best_bid, winner = bids[0]
            clearing_price = max(best_bid, offer.base_price)
            winner.complete_purchase(offer, clearing_price)
            results.append(
                AuctionResult(
                    offer=offer,
                    winner=winner.name,
                    clearing_price=clearing_price,
                )
            )
        return results

    def run_contract_tenders(
        self,
        opportunities: Sequence[ContractOpportunity],
        companies: Sequence["Company"],
    ) -> List[TenderResult]:
        results: List[TenderResult] = []
        for opportunity in opportunities:
            bids: List[Tuple[float, "Company"]] = []
            for company in companies:
                price = company.prepare_contract_bid(opportunity)
                if price is None:
                    continue
                if opportunity.floor_price <= price <= opportunity.ceiling_price:
                    bids.append((price, company))
            if not bids:
                results.append(TenderResult(opportunity, None, None))
                continue
            bids.sort(key=lambda item: item[0])
            winning_price, winner = bids[0]
            winner.accept_contract(opportunity, winning_price)
            results.append(TenderResult(opportunity, winner.name, winning_price))
        return results


__all__ = ["EnergyMarket", "GENERATOR_CATALOGUE", "UPGRADE_LIBRARY"]
