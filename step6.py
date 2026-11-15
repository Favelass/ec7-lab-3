"""Safety policy for signs, uncertainty and people (no motor commands here)."""
from __future__ import annotations
from step3 import *

SLOW_FROM_M = 1.2
STOP_FROM_M = 0.7
STOP_TRUST = 0.5
ACT_TRUST = 0.4
# Proposed person detector threshold; the engine supplies only person_ahead.
PERSON_TRUST = 0.3


def policy(detection: dict, state: dict) -> str:
    target = detection.get("target", "unknown")
    distance = detection.get("distance_m")
    confidence = detection.get("confidence", 0.0)
    history = state.get("history", [])
    # Human safety overrides sign recognition and the current traffic rule.
    if state.get("person_ahead"):
        return "stop"
    stopped_here = any(h["action"] == "stop" for h in history[-3:])
    if target == "sign-stop":
        if distance is not None and distance <= SLOW_FROM_M:
            return "stop" if distance <= STOP_FROM_M or confidence < STOP_TRUST else "slow"
        return "slow"
    recent = [h["detection"]["target"] for h in history[-3:]]
    if target == "unknown":
        if "sign-stop" in recent and not stopped_here:
            return "stop"
        return "report"
    if confidence < ACT_TRUST:
        return "report"
    if target == "sign-left":
        return "turn_left"
    if target == "sign-right":
        return "turn_right"
    if target == "sign-down":
        return "stop"
    if target in ("sign-up", "sign-free"):
        return "forward"
    return "report"
