"""depth_processor.py

Lightweight depth processing utilities for converting stereo/point-cloud inputs
into depth maps. This is a dry-run stub.
"""
from __future__ import annotations

from typing import Any
import numpy as np


class DepthProcessor:
    def __init__(self) -> None:
        pass

    def compute_depth_map(self, image: Any) -> np.ndarray:
        """Return a fake depth map for the provided image (same shape, single channel)."""
        print("[DepthProcessor] compute_depth_map called")
        if hasattr(image, "shape"):
            h, w = image.shape[:2]
        else:
            h, w = 480, 640
        # return a simple gradient depth map
        return np.tile(np.linspace(0, 1, w), (h, 1)).astype(np.float32)

    def save_depth(self, depth: np.ndarray, path: str) -> None:
        print(f"[DepthProcessor] would save depth map to {path} (shape={depth.shape})")


if __name__ == "__main__":
    dp = DepthProcessor()
    d = dp.compute_depth_map(None)
    dp.save_depth(d, "./depth.png")
