# Shabat-Cam Project TODOs & Future Improvements

This document outlines the planned improvements and next steps for the Shabat-Cam turret controller AI and synthetic data generation pipeline.

## 1. Advanced Synthetic Data Generation (Harder Data & Randomization)
To bridge the "Domain Gap" between Blender simulations and real-world tactical environments, the dataset generation pipeline (`build_environment.py`) needs extreme variance:
- [ ] **Extreme Lighting:** Implement harsh lighting conditions (explosions, failing LEDs, pitch-black with flashlights). Introduce drastic overexposure and underexposure.
- [ ] **Domain Randomization:** Apply chaotic, non-realistic textures (checkerboards, noise, random colors) to background elements to force the AI to focus on the geometry of the shells rather than memorizing the background.
- [ ] **Severe Camera Jitter & Motion Blur:** Simulate the intense vibration and shockwaves of an artillery cabin by increasing camera translation and rotation jitter significantly.
- [ ] **Intentional Occlusions:** Introduce random objects (e.g., robot arms, human hands, or generic shapes) that partially block the camera's view of the breech.
- [ ] **Atmospheric Effects:** Add smoke, dust, and particle effects using Blender's volume scatter or semi-transparent planes to wash out contrast, mimicking a post-firing environment.

## 2. Sensor Fusion: Integrating LiDAR / Depth Data
Relying solely on RGB vision can be brittle in visually degraded environments. To improve the FSM's reliability and the FSM demo's accuracy:
- [ ] **Simulate LiDAR in Blender:** Utilize Blender's Z-depth pass or raycasting to simulate a 3D point cloud or depth map of the breech zone.
- [ ] **Depth-Aware Tracking:** Update the `VisionTracker` to ingest depth maps alongside RGB frames, ensuring that objects are physically inside the FSM breech zone (3D spatial verification) rather than just overlapping in 2D pixel space.
- [ ] **Multi-Modal AI:** Explore extending the YOLO-OBB model or the tracking logic to utilize LiDAR/Depth data, virtually eliminating false positives caused by objects in the background or foreground.

## 3. General Architecture & Tooling
- [ ] Evaluate model quantization (TensorRT / ONNX) for even faster real-time edge inference.
- [ ] Implement a dynamic configuration file (YAML/JSON) for FSM safety thresholds and bounding box zones, removing hardcoded pixel coordinates.
- [ ] Expand the `AMMO_DB` to include a wider variety of projectiles and propellant charge configurations.