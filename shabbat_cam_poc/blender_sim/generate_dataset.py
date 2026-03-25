import subprocess
import os

BLENDER_EXE = r"C:\Users\yonat\PycharmProjects\Shabat-Cam\shabbat_cam_poc\blender_sim\Blender\blender.exe"
BUILDER_SCRIPT = os.path.abspath("build_environment.py")

def generate_full_batch():
    runs = 50
    frames_per_run = 50
    ammo_pool = ["M795", "M825", "M107"]

    print(f"--- Starting Synthetic Data Generation: {runs} Runs ---")

    for run_id in range(runs):
        selected_ammo = ammo_pool[run_id % len(ammo_pool)]
        print(f"\n[Run {run_id + 1}/{runs}] Ammo: {selected_ammo} | Rendering {frames_per_run} frames...")

        command = [
            BLENDER_EXE,
            "--background",
            "--python", BUILDER_SCRIPT,
            "--",
            "--run_id", str(run_id),
            "--frames", str(frames_per_run),
            "--ammo_type", selected_ammo
        ]

        # Sanitize environment to prevent PyCharm from crashing Blender's internal Python
        clean_env = os.environ.copy()
        clean_env.pop("PYTHONHOME", None)
        clean_env.pop("PYTHONPATH", None)

        # Removed DEVNULL so you can actually watch Blender's progress frame-by-frame
        subprocess.run(command, env=clean_env)

    print("\n\nBatch Complete! Your YOLO dataset and Scene Metadata are ready.")

if __name__ == "__main__":
    generate_full_batch()