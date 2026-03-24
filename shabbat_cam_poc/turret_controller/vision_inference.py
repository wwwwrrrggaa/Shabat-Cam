"""vision_inference.py

Stub vision inference module that would run the trained YOLO model and depth processor
and emit simple detection events suitable for the FSM.
"""
from __future__ import annotations

from typing import Any, Dict
import numpy as np


class VisionInference:
    def __init__(self) -> None:
        # placeholder for model handles
        self.model = None

    def infer(self, frame: Any) -> Dict[str, Any]:
        """Run inference on a single frame and return detections + depth.

        This is a fake implementation for dry-run/testing.
        """
        print("[VisionInference] infer called")
        # fake detection: say we found a shell at center
        h, w = (frame.shape[0], frame.shape[1]) if hasattr(frame, "shape") else (480, 640)
        detection = {
            "class": "shell",
            "confidence": 0.95,
            "bbox": [w // 2 - 10, h // 2 - 10, w // 2 + 10, h // 2 + 10],
        }
        depth_map = np.zeros((h, w), dtype=float)
        return {"detections": [detection], "depth": depth_map}


if __name__ == "__main__":
    vi = VisionInference()
    out = vi.infer(None)
    print(out)

