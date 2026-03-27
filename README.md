# Shabat-Cam

Shabat-Cam is an AI-powered safety monitoring system designed for artillery turret controllers. By utilizing synthetic data generation, computer vision, and finite-state machine (FSM) tracking, Shabat-Cam visually monitors the breech of a turret to ensure the correct sequence and type of ammunition (shell and propellant) are loaded before firing.

## Key Features

- **Synthetic Data Generation (Blender):** Automatically generates highly varied, annotated datasets of 3D artillery shells and propellant bags being loaded into a breech by robotic arms.
- **YOLO-OBB Inference:** Utilizes a state-of-the-art YOLO model trained on Oriented Bounding Boxes (OBB) to detect and classify ammunition in real-time, regardless of the camera angle or object rotation.
- **Finite-State Machine (FSM) Logic:** Tracks the exact sequence of loading (Empty -> Shell Loaded -> Propellant Loaded -> Secured) and acts as a strict safety interlock.
- **Mismatch Detection:** Compares the dynamically detected ammunition against a predefined "Fire Mission." If a mismatch occurs (e.g., loading an M825 Smoke shell when an M795 HE was requested), the system immediately halts and throws a safety warning.

## Project Structure

* **`shabbat_cam_poc/blender_sim/`**: Contains the Blender Python API scripts used to programmatically build the 3D environment, animate the loading sequence, and render the YOLO-OBB training data.
    * `generate_dataset.py`: The entry point for rendering thousands of synthetic training images.
    * `build_environment.py`: The core 3D scene builder and kinematics engine.
    * `demo.py`: Launches Blender in GUI mode to visually inspect the environment.
* **`shabbat_cam_poc/ai_training/`**: Scripts for formatting the Blender outputs, performing train/val splits, and fine-tuning the YOLO model.
* **`shabbat_cam_poc/turret_controller/`**: The real-time inference pipeline and FSM logic.
    * `main.py`: The main loop that reads video frames (or live streams), runs the tracker, updates the FSM, and draws the HUD.
    * `fsm_brain.py`: The state machine responsible for sequence validation and safety checks.
    * `vision_inference.py`: Wraps the YOLO model and processes the raw OBB predictions.

## Getting Started

1. **Install Dependencies:**
   Ensure you have the required Python packages (e.g., `ultralytics`, `opencv-python`, `numpy`, `huggingface_hub`).

2. **Download Git LFS Files:**
   The trained YOLO weights (`best.pt`) and 3D assets are tracked using Git LFS. Run `git lfs pull` after cloning the repository.

3. **Run the Demo:**
   Execute `shabbat_cam_poc/turret_controller/main.py` to watch the AI monitor a pre-rendered tactical scenario.

## Future Roadmap
See `TODO.md` for planned features, including LiDAR/Depth integration and advanced synthetic domain randomization.