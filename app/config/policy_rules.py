"""
Policy rules configuration (Phase 2).
Dynamic rules per scenario; role-based allowed action types and optional limits.
"""
from __future__ import annotations

from app.models import ActionType, Role, Scenario

# (scenario, role) -> set of allowed ActionTypes. If not present, deny.
# Empty set = no actions allowed for that (scenario, role).
_ALLOWED_ACTIONS: dict[tuple[Scenario, Role], set[ActionType]] = {
    # NORMAL: full access for admin/system; user/agent limited
    (Scenario.NORMAL, Role.SYSTEM): {ActionType.EXECUTE, ActionType.QUERY, ActionType.APPROVE, ActionType.REJECT, ActionType.ESCALATE, ActionType.UNKNOWN},
    (Scenario.NORMAL, Role.ADMIN): {ActionType.EXECUTE, ActionType.QUERY, ActionType.APPROVE, ActionType.REJECT, ActionType.ESCALATE},
    (Scenario.NORMAL, Role.AGENT): {ActionType.QUERY, ActionType.EXECUTE, ActionType.ESCALATE},
    (Scenario.NORMAL, Role.USER): {ActionType.QUERY, ActionType.ESCALATE},
    # LOW_RISK: same as normal, can add tighter rules later
    (Scenario.LOW_RISK, Role.SYSTEM): {ActionType.EXECUTE, ActionType.QUERY, ActionType.APPROVE, ActionType.REJECT, ActionType.ESCALATE, ActionType.UNKNOWN},
    (Scenario.LOW_RISK, Role.ADMIN): {ActionType.EXECUTE, ActionType.QUERY, ActionType.APPROVE, ActionType.REJECT, ActionType.ESCALATE},
    (Scenario.LOW_RISK, Role.AGENT): {ActionType.QUERY, ActionType.EXECUTE, ActionType.ESCALATE},
    (Scenario.LOW_RISK, Role.USER): {ActionType.QUERY, ActionType.ESCALATE},
    # HIGH_VOLATILITY: restrict execute for user/agent
    (Scenario.HIGH_VOLATILITY, Role.SYSTEM): {ActionType.EXECUTE, ActionType.QUERY, ActionType.APPROVE, ActionType.REJECT, ActionType.ESCALATE, ActionType.UNKNOWN},
    (Scenario.HIGH_VOLATILITY, Role.ADMIN): {ActionType.EXECUTE, ActionType.QUERY, ActionType.APPROVE, ActionType.REJECT, ActionType.ESCALATE},
    (Scenario.HIGH_VOLATILITY, Role.AGENT): {ActionType.QUERY, ActionType.ESCALATE},
    (Scenario.HIGH_VOLATILITY, Role.USER): {ActionType.QUERY, ActionType.ESCALATE},
    # MAINTENANCE: only query and escalate for non-system
    (Scenario.MAINTENANCE, Role.SYSTEM): {ActionType.EXECUTE, ActionType.QUERY, ActionType.APPROVE, ActionType.REJECT, ActionType.ESCALATE, ActionType.UNKNOWN},
    (Scenario.MAINTENANCE, Role.ADMIN): {ActionType.QUERY, ActionType.ESCALATE},
    (Scenario.MAINTENANCE, Role.AGENT): {ActionType.QUERY, ActionType.ESCALATE},
    (Scenario.MAINTENANCE, Role.USER): {ActionType.QUERY, ActionType.ESCALATE},
}

# Max number of keys in params (per scenario if we want; for now global).
MAX_PARAM_KEYS = 100

# Param keys that are never allowed (e.g. dangerous injection).
FORBIDDEN_PARAM_KEYS: frozenset[str] = frozenset({"__class__", "__builtins__", "eval", "exec", "system", "shell", "password", "secret", "api_key"})

# Emergency override: if True, policy can be bypassed (e.g. admin override). Set via env in production.
POLICY_OVERRIDE_FOR_EMERGENCY = False


def get_allowed_actions(scenario: Scenario, role: Role) -> set[ActionType]:
    """Return set of action types allowed for (scenario, role). Default deny."""
    return _ALLOWED_ACTIONS.get((scenario, role), set())


def is_action_allowed(scenario: Scenario, role: Role, action_type: ActionType) -> bool:
    """Check if action_type is allowed for (scenario, role)."""
    return action_type in get_allowed_actions(scenario, role)
