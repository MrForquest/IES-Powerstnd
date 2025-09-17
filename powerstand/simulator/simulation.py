"""High level orchestration for the energy company simulator."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .components import (
    AuctionResult,
    ConsumerContract,
    Generator,
    GovernmentProgram,
    SmartGridNode,
    TenderResult,
)
from .company import Company, StrategyPreferences
from .market import EnergyMarket, GENERATOR_CATALOGUE
from .world import World


@dataclass
class SimulationConfig:
    """Parameters controlling the simulation run."""

    years: int = 10
    months_per_year: int = 12
    base_year: int = 2040
    seed: int = 42
    bots: int = 2
    starting_funds: float = 5_000_000.0
    starting_locations: int = 5
    player_name: str = "PlayerCo"


@dataclass
class MonthlyLog:
    month_index: int
    year: int
    auctions: List[AuctionResult] = field(default_factory=list)
    tenders: List[TenderResult] = field(default_factory=list)
    grants: List[str] = field(default_factory=list)
    company_reports: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class SimulationReport:
    monthly_logs: List[MonthlyLog]
    companies: List[Company]

    def standings(self) -> List[Company]:
        return sorted(self.companies, key=lambda company: company.funds, reverse=True)


class Simulation:
    """Main entry point that sets up the world and executes the loop."""

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config = config or SimulationConfig()
        self.world = World(base_year=self.config.base_year, seed=self.config.seed)
        self.market = EnergyMarket(self.world)
        self.rng = random.Random(self.config.seed)
        self.month = 0
        self.companies: List[Company] = []
        self.programs: List[GovernmentProgram] = []
        self.program_awards: Dict[str, Set[str]] = {}
        self._setup_world()
        self._create_companies()
        self._setup_government_programs()

    # ------------------------------------------------------------------ setup
    def _setup_world(self) -> None:
        self.world.generate_locations(self.config.starting_locations)

    def _create_companies(self) -> None:
        total_companies = 1 + self.config.bots
        for index in range(total_companies):
            is_player = index == 0
            name = self.config.player_name if is_player else f"BotCo-{index}"
            preferences = StrategyPreferences(
                risk_appetite=self.rng.uniform(0.35, 0.75),
                innovation_focus=self.rng.uniform(0.4, 0.8),
                ecology_focus=self.rng.uniform(0.3, 0.85),
                reliability_focus=self.rng.uniform(0.4, 0.9),
            )
            company_rng = random.Random(self.config.seed + index * 17)
            company = Company(
                name=name,
                world=self.world,
                funds=self.config.starting_funds,
                preferences=preferences,
                rng=company_rng,
                is_player=is_player,
            )
            self._initialize_company(company)
            self.companies.append(company)

    def _initialize_company(self, company: Company) -> None:
        # Ensure at least one location is active
        company.evaluate_expansion(self.config.base_year)
        if not company.active_locations:
            best_location = max(
                self.world.iterate_locations(), key=lambda loc: loc.strategic_value
            )
            company.active_locations.append(best_location.name)
            company.grid[best_location.name] = SmartGridNode(
                location=best_location.name,
                capacity_limit=best_location.strategic_value * 1_100.0,
                loss_rate=0.18 * best_location.grid_complexity,
                automation=0.08,
                maintenance=best_location.maintenance_cost * 0.12,
                storage_capacity=best_location.strategic_value * 180.0,
            )
            company.funds -= best_location.development_cost * 0.5
        location_name = company.active_locations[0]
        location = self.world.locations[location_name]
        archetype = self.market.rng.choice(GENERATOR_CATALOGUE[:4])
        company.generators.append(
            Generator(
                name=f"Starter-{company.name}",
                archetype=archetype,
                location=location.name,
            )
        )
        contract = ConsumerContract(
            consumer_name=f"Starter-{company.name}",
            location=location.name,
            demand_mwh=520.0,
            duration_months=24,
            price_per_mwh=165.0,
            penalty_per_mwh=120.0,
            reliability_requirement=0.88,
            renewable_requirement=0.3,
            remaining_months=24,
            is_public=True,
        )
        company.contracts.append(contract)

    # ------------------------------------------------------------------- loop
    def run(self) -> SimulationReport:
        monthly_logs: List[MonthlyLog] = []
        total_months = self.config.years * self.config.months_per_year
        for step in range(total_months):
            self.month = step + 1
            year = self.config.base_year + step // self.config.months_per_year
            self.world.apply_climate_drift()
            auctions = self._handle_auctions()
            tenders = self._handle_tenders()
            grants = self._apply_government_programs()
            company_reports = self._operate_companies()
            if (step + 1) % self.config.months_per_year == 0:
                for company in self.companies:
                    company.evaluate_expansion(year + 1)
            monthly_logs.append(
                MonthlyLog(
                    month_index=self.month,
                    year=year,
                    auctions=auctions,
                    tenders=tenders,
                    grants=grants,
                    company_reports=company_reports,
                )
            )
        return SimulationReport(monthly_logs=monthly_logs, companies=self.companies)

    # -------------------------------------------------------------- subroutines
    def _handle_auctions(self) -> List[AuctionResult]:
        generator_offers = self.market.generator_offers(self.month)
        upgrade_offers = self.market.upgrade_offers() if self.month % 2 == 0 else []
        offers = generator_offers + upgrade_offers
        if not offers:
            return []
        return self.market.run_auctions(offers, self.companies)

    def _handle_tenders(self) -> List[TenderResult]:
        if self.month % 3 != 1:
            return []
        locations = self._available_locations()
        demand_factor = 1.0 + self.rng.uniform(-0.05, 0.1)
        opportunities = self.market.contract_opportunities(locations, demand_factor)
        if not opportunities:
            return []
        return self.market.run_contract_tenders(opportunities, self.companies)

    def _operate_companies(self) -> Dict[str, Dict[str, float]]:
        reports: Dict[str, Dict[str, float]] = {}
        for company in self.companies:
            record = company.operate_month()
            reports[company.name] = record
        return reports

    def _available_locations(self) -> List[str]:
        locations = set()
        for company in self.companies:
            locations.update(company.active_locations)
        return sorted(locations)

    # ------------------------------------------------------------ government
    def _setup_government_programs(self) -> None:
        self.programs = [
            GovernmentProgram(
                name="Зелёный переход",
                grant_amount=400_000.0,
                requirement=lambda snapshot: snapshot.renewable_share >= 0.7
                and snapshot.reputation >= 0.8,
                description="Субсидия за высокую долю чистой энергии и надежность.",
                duration_months=36,
                remaining_months=36,
            ),
            GovernmentProgram(
                name="Умная сеть",
                grant_amount=300_000.0,
                requirement=lambda snapshot: len(snapshot.active_locations) >= 2,
                description="Развитие сетевой инфраструктуры в новых регионах.",
                duration_months=48,
                remaining_months=48,
            ),
        ]
        self.program_awards = {program.name: set() for program in self.programs}

    def _apply_government_programs(self) -> List[str]:
        announcements: List[str] = []
        for program in list(self.programs):
            awarded = self.program_awards.setdefault(program.name, set())
            for company in self.companies:
                if company.name in awarded:
                    continue
                snapshot = company.snapshot()
                if program.requirement(snapshot):
                    company.funds += program.grant_amount
                    awarded.add(company.name)
                    announcements.append(
                        f"{company.name} получает программу '{program.name}' на {program.grant_amount:,.0f}"
                    )
            program.advance()
            if program.remaining_months <= 0:
                self.programs.remove(program)
        return announcements


__all__ = ["Simulation", "SimulationConfig", "SimulationReport", "MonthlyLog"]
