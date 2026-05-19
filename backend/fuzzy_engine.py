import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from config import MINUTES_IN_DAY, PERCENTAGE_MAX

PRIORITY_MAP = {"high": 75, "medium": 50, "low": 25}
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

# Output score membership breakpoints
_SCORE_VERY_HIGH: tuple[int, ...] = (75, 88, 100, 100)
_SCORE_HIGH: tuple[int, ...] = (50, 75, 88)
_SCORE_MEDIUM: tuple[int, ...] = (25, 50, 75)
_SCORE_LOW: tuple[int, ...] = (0, 0, 25, 50)

def _build_control_system() -> ctrl.ControlSystem:
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

    score["very_high"] = fuzz.trapmf(score.universe, _SCORE_VERY_HIGH)
    score["high"]      = fuzz.trimf(score.universe,  _SCORE_HIGH)
    score["medium"]    = fuzz.trimf(score.universe,  _SCORE_MEDIUM)
    score["low"]       = fuzz.trapmf(score.universe, _SCORE_LOW)

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


_system = _build_control_system()


def compute_task_score(
    minutes_to_deadline: float,
    priority: str,
) -> float:
    simulation = ctrl.ControlSystemSimulation(_system)
    simulation.input["urgency"] = max(0.0, min(MINUTES_IN_DAY, minutes_to_deadline))
    simulation.input["priority"] = float(PRIORITY_MAP[priority])
    simulation.compute()
    return round(float(simulation.output["score"]), 2)
