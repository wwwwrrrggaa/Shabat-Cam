import subprocess
import os
import random

BLENDER_EXE = r"C:\Users\yonat\PycharmProjects\Shabat-Cam\shabbat_cam_poc\blender_sim\Blender\blender.exe"
BUILDER_SCRIPT = os.path.abspath("build_environment.py")

def generate_full_batch():
    runs = 3
    frames_per_run = 50 # Adjust higher for smoother motion
    ammo_pool = ["M795", "M825", "M107"]

    print(f"--- Starting Synthetic Data Generation: {runs} Runs ---")

    for run_id in range(runs):
        selected_ammo = random.choice(ammo_pool)
        print(f"\n[Run {run_id}] Selected Ammo: {selected_ammo}")

        for frame in range(frames_per_run):
            progress = frame / float(frames_per_run - 1)
            output_name = f"run_{run_id}_ammo_{selected_ammo}_frame_{frame:04d}"

            command = [
                BLENDER_EXE,
                "--background",
                "--python", BUILDER_SCRIPT,
                "--",
                "--render",
                "--progress", str(progress),
                "--output", output_name,
                "--ammo_type", selected_ammo
            ]

            print(f" Rendering {output_name}...", end="\r")
            subprocess.run(command, stdout=subprocess.DEVNULL)

    print("\nBatch Complete. Data saved to 'training_data/'")

if __name__ == "__main__":
    generate_full_batch()