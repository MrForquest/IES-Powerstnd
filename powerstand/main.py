"""Command line entry point for the energy company simulator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .simulator.simulation import Simulation, SimulationConfig, SimulationReport


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Процедурный симулятор управления энергокомпанией.",
    )
    parser.add_argument("--years", type=int, default=10, help="Продолжительность симуляции в годах.")
    parser.add_argument(
        "--months-per-year",
        type=int,
        default=12,
        help="Количество игровых тиков в одном году.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Базовое значение генератора случайных чисел.")
    parser.add_argument("--bots", type=int, default=2, help="Количество конкурирующих компаний-ботов.")
    parser.add_argument(
        "--starting-funds",
        type=float,
        default=5_000_000.0,
        help="Начальный капитал каждой компании.",
    )
    parser.add_argument(
        "--locations",
        type=int,
        default=6,
        help="Количество локаций, доступных в мире.",
    )
    parser.add_argument(
        "--player-name",
        type=str,
        default="PlayerCo",
        help="Название компании игрока.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Показать краткую сводку по месяцам.",
    )
    parser.add_argument(
        "--export",
        type=Path,
        help="Путь к JSON-файлу для сохранения результатов симуляции.",
    )
    return parser


def render_standings(report: SimulationReport) -> str:
    lines: List[str] = []
    header = f"{'Компания':<16} {'Капитал':>12} {'Репутация':>10} {'Обновл. доля':>13}"
    lines.append(header)
    lines.append("-" * len(header))
    for company in report.standings():
        snapshot = company.snapshot()
        renewable = f"{snapshot.renewable_share:.2f}"
        lines.append(
            f"{company.name:<16} {company.funds:>12,.0f} {company.reputation:>10.2f} {renewable:>13}"
        )
    return "\n".join(lines)


def summarise_history(history: List[Dict[str, float]]) -> Dict[str, float]:
    totals = {"revenue": 0.0, "expenses": 0.0, "energy": 0.0, "waste": 0.0}
    if not history:
        return totals
    for record in history:
        totals["revenue"] += record.get("revenue", 0.0)
        totals["expenses"] += record.get("expenses", 0.0)
        totals["energy"] += record.get("energy", 0.0)
        totals["waste"] += record.get("waste", 0.0)
    totals["profit"] = totals["revenue"] - totals["expenses"]
    return totals


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = SimulationConfig(
        years=args.years,
        months_per_year=args.months_per_year,
        seed=args.seed,
        bots=args.bots,
        starting_funds=args.starting_funds,
        starting_locations=args.locations,
        player_name=args.player_name,
    )
    simulation = Simulation(config)
    report = simulation.run()
    print("=" * 72)
    print(f"Симуляция завершена. Итоговый год: {config.base_year + config.years - 1}")
    print(render_standings(report))

    for company in report.companies:
        totals = summarise_history(company.history)
        print()
        print(f"Компания {company.name}:")
        print(
            f"  Совокупная выручка: {totals['revenue']:,.0f} | Расходы: {totals['expenses']:,.0f} | Прибыль: {totals['profit']:,.0f}"
        )
        print(
            f"  Выпущено энергии: {totals['energy']:,.0f} МВт⋅ч | Отходы: {totals['waste']:,.0f} усл. ед."
        )
        if company.active_locations:
            print(f"  Освоенные локации: {', '.join(company.active_locations)}")
        print(f"  Действующих контрактов: {len(company.contracts)}")

    if args.details:
        print("\nКраткий поквартальный отчёт:")
        for log in report.monthly_logs:
            if log.month_index % max(1, args.months_per_year // 4) != 0:
                continue
            best = max(log.company_reports.items(), key=lambda item: item[1].get("revenue", 0.0))
            print(
                f"  Месяц {log.month_index:02d} ({log.year}): лидирует {best[0]}"
                f" с выручкой {best[1].get('revenue', 0.0):,.0f}"
            )
            for grant in log.grants:
                print(f"    {grant}")

    if args.export:
        payload: Dict[str, Any] = {
            "config": vars(config),
            "standings": [
                {
                    "name": company.name,
                    "funds": company.funds,
                    "reputation": company.reputation,
                    "renewable_share": company.snapshot().renewable_share,
                    "history": company.history,
                }
                for company in report.companies
            ],
            "grants": [
                {
                    "month": log.month_index,
                    "year": log.year,
                    "events": log.grants,
                }
                for log in report.monthly_logs
                if log.grants
            ],
        }
        args.export.parent.mkdir(parents=True, exist_ok=True)
        args.export.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nДанные симуляции сохранены в {args.export}")


if __name__ == "__main__":
    main()
