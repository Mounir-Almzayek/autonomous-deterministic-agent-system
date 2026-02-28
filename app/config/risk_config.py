"""
Risk scoring thresholds and escalation config (Phase 3).
Per-scenario max risk and escalation thresholds.
"""
from app.models import Scenario

# Max risk score allowed before threshold_breach (per scenario). Score in [0, 1].
MAX_RISK_THRESHOLD: dict[Scenario, float] = {
    Scenario.NORMAL: 0.75,
    Scenario.LOW_RISK: 0.5,
    Scenario.HIGH_VOLATILITY: 0.4,
    Scenario.MAINTENANCE: 0.6,
}

# Above this score, escalation_required = True (human/external review).
ESCALATION_THRESHOLD: dict[Scenario, float] = {
    Scenario.NORMAL: 0.6,
    Scenario.LOW_RISK: 0.4,
    Scenario.HIGH_VOLATILITY: 0.3,
    Scenario.MAINTENANCE: 0.5,
}

# Scenario sensitivity multiplier: base score * multiplier. >1 = amplifies risk.
SCENARIO_SENSITIVITY: dict[Scenario, float] = {
    Scenario.NORMAL: 1.0,
    Scenario.LOW_RISK: 0.8,
    Scenario.HIGH_VOLATILITY: 1.4,
    Scenario.MAINTENANCE: 1.1,
}


def get_max_risk_threshold(scenario: Scenario) -> float:
    return MAX_RISK_THRESHOLD.get(scenario, 0.75)


def get_escalation_threshold(scenario: Scenario) -> float:
    return ESCALATION_THRESHOLD.get(scenario, 0.6)


def get_sensitivity(scenario: Scenario) -> float:
    return SCENARIO_SENSITIVITY.get(scenario, 1.0)
