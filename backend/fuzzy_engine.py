import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from config import MINUTES_IN_DAY, PERCENTAGE_MAX

PRIORITY_MAP = {"high": 75, "medium": 50, "low": 25}
ENERGY_MAP: dict[str, float] = {"high": 75.0, "medium": 50.0, "low": 25.0}
_UNIVERSE_STEP: int = 1

# Urgency membership breakpoints (minutes to deadline)
_URGENCY_VERY_HIGH: tuple[int, ...] = (0, 0, 20, 30)
_URGENCY_HIGH: tuple[int, ...] = (20, 60, 120)
_URGENCY_MEDIUM: tuple[int, ...] = (60, 180, 300)
_URGENCY_LOW: tuple[int, ...] = (240, 300, 1440, 1440)

# Priority membership breakpoints (mapped score 0–100)
_PRIORITY_HIGH: tuple[int, ...] = (50, 75, 100)
_PRIORITY_MEDIUM: tuple[int, ...] = (25, 50, 75)
_PRIORITY_LOW: tuple[int, ...] = (0, 25, 50)

_ENERGY_HIGH: tuple[int, ...] = (50, 75, 100)
_ENERGY_MEDIUM: tuple[int, ...] = (25, 50, 75)
_ENERGY_LOW: tuple[int, ...] = (0, 25, 50)

# Output score membership breakpoints
_SCORE_VERY_HIGH: tuple[int, ...] = (75, 88, 100, 100)
_SCORE_HIGH: tuple[int, ...] = (50, 75, 88)
_SCORE_MEDIUM: tuple[int, ...] = (25, 50, 75)
_SCORE_LOW: tuple[int, ...] = (0, 0, 25, 50)


def _apply_score_memberships(variable: ctrl.Antecedent | ctrl.Consequent) -> None:
    variable["very_high"] = fuzz.trapmf(variable.universe, _SCORE_VERY_HIGH)
    variable["high"]      = fuzz.trimf(variable.universe,  _SCORE_HIGH)
    variable["medium"]    = fuzz.trimf(variable.universe,  _SCORE_MEDIUM)
    variable["low"]       = fuzz.trapmf(variable.universe, _SCORE_LOW)


def _build_base_system() -> ctrl.ControlSystem:
    urgency  = ctrl.Antecedent(np.arange(0, MINUTES_IN_DAY + 1, _UNIVERSE_STEP), "urgency")
    priority = ctrl.Antecedent(np.arange(0, PERCENTAGE_MAX + 1, _UNIVERSE_STEP), "priority")
    score    = ctrl.Consequent(np.arange(0, PERCENTAGE_MAX + 1, _UNIVERSE_STEP), "score")

    urgency["very_high"]  = fuzz.trapmf(urgency.universe, _URGENCY_VERY_HIGH)
    urgency["high"]       = fuzz.trimf(urgency.universe,  _URGENCY_HIGH)
    urgency["medium"]     = fuzz.trimf(urgency.universe,  _URGENCY_MEDIUM)
    urgency["low"]        = fuzz.trapmf(urgency.universe, _URGENCY_LOW)

    priority["high"]   = fuzz.trimf(priority.universe, _PRIORITY_HIGH)
    priority["medium"] = fuzz.trimf(priority.universe, _PRIORITY_MEDIUM)
    priority["low"]    = fuzz.trimf(priority.universe, _PRIORITY_LOW)

    _apply_score_memberships(score)

    rules = [
        ctrl.Rule(urgency["very_high"] & priority["high"],   score["very_high"]),
        ctrl.Rule(urgency["very_high"] & priority["medium"], score["very_high"]),
        ctrl.Rule(urgency["very_high"] & priority["low"],    score["high"]),
        ctrl.Rule(urgency["high"]      & priority["high"],   score["very_high"]),
        ctrl.Rule(urgency["high"]      & priority["medium"], score["high"]),
        ctrl.Rule(urgency["high"]      & priority["low"],    score["medium"]),
        ctrl.Rule(urgency["medium"]    & priority["high"],   score["high"]),
        ctrl.Rule(urgency["medium"]    & priority["medium"], score["medium"]),
        ctrl.Rule(urgency["medium"]    & priority["low"],    score["low"]),
        ctrl.Rule(urgency["low"]       & priority["high"],   score["medium"]),
        ctrl.Rule(urgency["low"]       & priority["medium"], score["low"]),
        ctrl.Rule(urgency["low"]       & priority["low"],    score["low"]),
    ]

    return ctrl.ControlSystem(rules)


def _build_energy_system() -> ctrl.ControlSystem:
    score_base  = ctrl.Antecedent(np.arange(0, PERCENTAGE_MAX + 1, _UNIVERSE_STEP), "score_base")
    energy      = ctrl.Antecedent(np.arange(0, PERCENTAGE_MAX + 1, _UNIVERSE_STEP), "energy")
    score_final = ctrl.Consequent(np.arange(0, PERCENTAGE_MAX + 1, _UNIVERSE_STEP), "score_final")

    _apply_score_memberships(score_base)

    energy["high"]   = fuzz.trimf(energy.universe, _ENERGY_HIGH)
    energy["medium"] = fuzz.trimf(energy.universe, _ENERGY_MEDIUM)
    energy["low"]    = fuzz.trimf(energy.universe, _ENERGY_LOW)

    _apply_score_memberships(score_final)

    rules = [
        ctrl.Rule(score_base["very_high"] & energy["high"],   score_final["high"]),
        ctrl.Rule(score_base["very_high"] & energy["medium"], score_final["very_high"]),
        ctrl.Rule(score_base["very_high"] & energy["low"],    score_final["very_high"]),
        ctrl.Rule(score_base["high"]      & energy["high"],   score_final["medium"]),
        ctrl.Rule(score_base["high"]      & energy["medium"], score_final["high"]),
        ctrl.Rule(score_base["high"]      & energy["low"],    score_final["high"]),
        ctrl.Rule(score_base["medium"]    & energy["high"],   score_final["low"]),
        ctrl.Rule(score_base["medium"]    & energy["medium"], score_final["medium"]),
        ctrl.Rule(score_base["medium"]    & energy["low"],    score_final["medium"]),
        ctrl.Rule(score_base["low"]       & energy["high"],   score_final["low"]),
        ctrl.Rule(score_base["low"]       & energy["medium"], score_final["low"]),
        ctrl.Rule(score_base["low"]       & energy["low"],    score_final["medium"]),
    ]

    return ctrl.ControlSystem(rules)


_base_system   = _build_base_system()
_energy_system = _build_energy_system()


def compute_task_score(
    minutes_to_deadline: float,
    priority: str,
    energy: str,
) -> float:
    base_sim = ctrl.ControlSystemSimulation(_base_system)
    base_sim.input["urgency"] = max(0.0, min(float(MINUTES_IN_DAY), minutes_to_deadline))
    base_sim.input["priority"] = PRIORITY_MAP[priority]
    base_sim.compute()

    energy_sim = ctrl.ControlSystemSimulation(_energy_system)
    energy_sim.input["score_base"] = base_sim.output["score"]
    energy_sim.input["energy"] = ENERGY_MAP[energy]
    energy_sim.compute()

    return round(float(energy_sim.output["score_final"]), 2)
