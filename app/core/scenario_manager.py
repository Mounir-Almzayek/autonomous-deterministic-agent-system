"""
Scenario Manager Node (Phase 6).
Resolves scenario from context and optional risk signals; supports scenario switching.
Multi-scenario paths: same graph, different thresholds and rules per scenario.
"""
from __future__ import annotations

import logging
from typing import Any

from app.models import RiskScoreResult, Scenario

logger = logging.getLogger(__name__)

# Optional: switch scenario when risk signals indicate (e.g. high_volatility -> HIGH_VOLATILITY).
SIGNAL_TO_SCENARIO: dict[str, Scenario] = {
    "high_volatility": Scenario.HIGH_VOLATILITY,
    "elevated_exposure": Scenario.HIGH_VOLATILITY,
    "maintenance": Scenario.MAINTENANCE,
}


def resolve(
    scenario: Scenario,
    risk_result: RiskScoreResult | None = None,
    context: dict[str, Any] | None = None,
) -> Scenario:
    """
    Resolve effective scenario from current scenario and optional risk/context.
    If risk signals suggest a different scenario (e.g. high_volatility), can switch.
    Returns Scenario for downstream (sandbox, decision).
    """
    if risk_result and risk_result.signals:
        for signal in risk_result.signals:
            if signal in SIGNAL_TO_SCENARIO:
                next_scenario = SIGNAL_TO_SCENARIO[signal]
                if next_scenario != scenario:
                    logger.info(
                        "scenario_switch",
                        extra={"from": scenario.value, "to": next_scenario.value, "signal": signal},
                    )
                    return next_scenario
    if context and "force_scenario" in context:
        try:
            return Scenario(context["force_scenario"])
        except ValueError:
            pass
    return scenario
