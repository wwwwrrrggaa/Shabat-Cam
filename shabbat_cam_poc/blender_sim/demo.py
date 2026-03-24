import subprocess
import os

BLENDER_EXE = r"C:\Users\yonat\PycharmProjects\Shabat-Cam\shabbat_cam_poc\blender_sim\Blender\blender.exe"
BUILDER_SCRIPT = os.path.abspath("build_environment.py")

def launch_demo():
    print("Launching Blender GUI for Demo...")
    # Add '--ammo_type' 'M825' here if you want to test specific ammo in the GUI
    command = [BLENDER_EXE, "--python", BUILDER_SCRIPT, "--", "--demo"]
    subprocess.run(command)

if __name__ == "__main__":
    launch_demo()