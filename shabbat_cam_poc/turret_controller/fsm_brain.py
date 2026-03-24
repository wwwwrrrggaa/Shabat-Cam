"""fsm_brain.py

Finite State Machine controller for the turret interlock (observer pattern).
This is a simple, testable FSM implemented without external dependencies.
"""
from __future__ import annotations

from typing import Any, List


class Observer:
    def update(self, event_name: str, **data: Any) -> None:
        raise NotImplementedError


class Observable:
    def __init__(self) -> None:
        self._observers: List[Observer] = []

    def register(self, o: Observer) -> None:
        if o not in self._observers:
            self._observers.append(o)

    def unregister(self, o: Observer) -> None:
        if o in self._observers:
            self._observers.remove(o)

    def notify(self, event_name: str, **data: Any) -> None:
        for o in list(self._observers):
            try:
                o.update(event_name, **data)
            except Exception:
                pass


class FSMBrain(Observable):
    STATES = [
        "Tray_Empty",
        "Shell_Loaded",
        "Charge_Loaded",
        "Breech_Locked",
        "Fatal_Error",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state = "Tray_Empty"

    def transition(self, event: str, **data: Any) -> None:
        """Apply a transition event and notify observers. This follows the diagram in fsm_diagram.md."""
        prev = self.state
        # very simple transition logic for demo purposes
        if self.state == "Tray_Empty":
            if event == "LIDAR_YOLO_CONFIRM_SHELL":
                self.state = "Shell_Loaded"
            elif event == "LIDAR_CONFIRM_BAG":
                self.state = "Fatal_Error"
        elif self.state == "Shell_Loaded":
            if event == "LIDAR_CONFIRM_BAG":
                self.state = "Charge_Loaded"
            elif event == "LIDAR_YOLO_CONFIRM_SHELL":
                self.state = "Fatal_Error"
            elif event == "LIDAR_REVERSE_MOTION":
                self.state = "Tray_Empty"
        elif self.state == "Charge_Loaded":
            if event == "BREECH_SENSOR_CLOSED":
                self.state = "Breech_Locked"
            elif event == "LIDAR_REVERSE_MOTION":
                self.state = "Shell_Loaded"
            elif event == "LIDAR_YOLO_CONFIRM_SHELL":
                self.state = "Fatal_Error"
        elif self.state == "Breech_Locked":
            if event == "FIRE_SHOCKWAVE_DETECTED":
                self.state = "Tray_Empty"
            elif event == "BREECH_SENSOR_OPENED":
                self.state = "Charge_Loaded"
        elif self.state == "Fatal_Error":
            if event == "MANUAL_SYSTEM_RESET":
                self.state = "Tray_Empty"

        if prev != self.state:
            self.notify("state_changed", source=prev, dest=self.state, event=event, data=data)

    def get_state(self) -> str:
        return self.state


# Simple print observer for quick testing
class PrintObserver(Observer):
    def update(self, event_name: str, **data: Any) -> None:
        print(f"[PrintObserver] {event_name}: {data}")


if __name__ == "__main__":
    f = FSMBrain()
    f.register(PrintObserver())
    print("initial:", f.get_state())
    f.transition("LIDAR_YOLO_CONFIRM_SHELL")
    f.transition("LIDAR_CONFIRM_BAG")
    f.transition("BREECH_SENSOR_CLOSED")
    f.transition("FIRE_SHOCKWAVE_DETECTED")
    print("final:", f.get_state())
