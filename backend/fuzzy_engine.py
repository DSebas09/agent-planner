import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

PRIORITY_MAP = {"high": 75, "medium": 50, "low": 25}

# Universes
_urgency = ctrl.Antecedent(np.arange(0, 1441, 1), "urgency")
_priority = ctrl.Antecedent(np.arange(0, 101, 1), "priority")
_score = ctrl.Consequent(np.arange(0, 101, 1), "score")

# urgency
_urgency["very_high"] = fuzz.trapmf(_urgency.universe, [0, 0, 20, 30])
_urgency["high"] = fuzz.trimf(_urgency.universe, [20, 60, 120])
_urgency["medium"] = fuzz.trimf(_urgency.universe, [60, 180, 300])
_urgency["low"] = fuzz.trapmf(_urgency.universe, [240, 300, 1440, 1440])

# priority and energy
_priority["high"] = fuzz.trimf(_priority.universe, [50, 75, 100])
_priority["medium"] = fuzz.trimf(_priority.universe, [25, 50, 75])
_priority["low"] = fuzz.trimf(_priority.universe, [0, 25, 50])

# output score
_score["very_high"] = fuzz.trapmf(_score.universe, [75, 88, 100, 100])
_score["high"] = fuzz.trimf(_score.universe, [50, 75, 88])
_score["medium"] = fuzz.trimf(_score.universe, [25, 50, 75])
_score["low"] = fuzz.trapmf(_score.universe, [0, 0, 25, 50])

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
    simulation.input["urgency"] = max(0.0, min(1440.0, minutes_to_deadline))
    simulation.input["priority"] = float(PRIORITY_MAP[priority])
    simulation.compute()
    return round(float(simulation.output["score"]), 2)
