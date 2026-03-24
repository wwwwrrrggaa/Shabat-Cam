"""main.py

Simple dry-run orchestrator that wires the VisionInference and FSMBrain together
and performs a single inference -> fsm update cycle.
"""
from __future__ import annotations

from .fsm_brain import FSMBrain, PrintObserver
from .vision_inference import VisionInference


def run_once() -> None:
    fsm = FSMBrain()
    fsm.register(PrintObserver())
    vision = VisionInference()

    print("[main] initial state:", fsm.get_state())
    # fake frame
    frame = None
    out = vision.infer(frame)

    # simple logic: if detection of shell => LIDAR_YOLO_CONFIRM_SHELL
    if out.get("detections"):
        fsm.transition("LIDAR_YOLO_CONFIRM_SHELL", detection=out["detections"])

    print("[main] final state:", fsm.get_state())


if __name__ == "__main__":
    run_once()

