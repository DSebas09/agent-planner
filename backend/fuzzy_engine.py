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

# Universes
_urgency  = ctrl.Antecedent(np.arange(0, MINUTES_IN_DAY + 1, _UNIVERSE_STEP), "urgency")
_priority = ctrl.Antecedent(np.arange(0, PERCENTAGE_MAX + 1, _UNIVERSE_STEP), "priority")
_score    = ctrl.Consequent(np.arange(0, PERCENTAGE_MAX + 1, _UNIVERSE_STEP), "score")

_urgency["very_high"] = fuzz.trapmf(_urgency.universe, _URGENCY_VERY_HIGH)
_urgency["high"]      = fuzz.trimf(_urgency.universe,  _URGENCY_HIGH)
_urgency["medium"]    = fuzz.trimf(_urgency.universe,  _URGENCY_MEDIUM)
_urgency["low"]       = fuzz.trapmf(_urgency.universe, _URGENCY_LOW)

_priority["high"]   = fuzz.trimf(_priority.universe, _PRIORITY_HIGH)
_priority["medium"] = fuzz.trimf(_priority.universe, _PRIORITY_MEDIUM)
_priority["low"]    = fuzz.trimf(_priority.universe, _PRIORITY_LOW)

_score["very_high"] = fuzz.trapmf(_score.universe, _SCORE_VERY_HIGH)
_score["high"]      = fuzz.trimf(_score.universe, _SCORE_HIGH)
_score["medium"]    = fuzz.trimf(_score.universe, _SCORE_MEDIUM)
_score["low"]       = fuzz.trapmf(_score.universe, _SCORE_LOW)

# Fuzzy rules
_rules = [
    ctrl.Rule(_urgency["very_high"] & _priority["high"], _score["very_high"]),
    ctrl.Rule(_urgency["very_high"] & _priority["medium"], _score["very_high"]),
    ctrl.Rule(_urgency["very_high"] & _priority["low"], _score["high"]),
    ctrl.Rule(_urgency["high"] & _priority["high"], _score["very_high"]),
    ctrl.Rule(_urgency["high"] & _priority["medium"], _score["high"]),
    ctrl.Rule(_urgency["high"] & _priority["low"], _score["medium"]),
    ctrl.Rule(_urgency["medium"] & _priority["high"], _score["high"]),
    ctrl.Rule(_urgency["medium"] & _priority["medium"], _score["medium"]),
    ctrl.Rule(_urgency["medium"] & _priority["low"], _score["low"]),
    ctrl.Rule(_urgency["low"] & _priority["high"], _score["medium"]),
    ctrl.Rule(_urgency["low"] & _priority["medium"], _score["low"]),
    ctrl.Rule(_urgency["low"] & _priority["low"], _score["low"]),
]

_system = ctrl.ControlSystem(_rules)


def compute_task_score(
    minutes_to_deadline: float,
    priority: str,
) -> float:
    simulation = ctrl.ControlSystemSimulation(_system)
    simulation.input["urgency"] = max(0.0, min(MINUTES_IN_DAY, minutes_to_deadline))
    simulation.input["priority"] = float(PRIORITY_MAP[priority])
    simulation.compute()
    return round(float(simulation.output["score"]), 2)
