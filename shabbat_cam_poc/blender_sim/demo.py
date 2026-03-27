import subprocess
import os

BLENDER_EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Blender", "blender.exe")
BUILDER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_environment.py")

def launch_demo():
    print("Launching Blender GUI for Demo...")
    # Add '--ammo_type' 'M825' here if you want to test specific ammo in the GUI
    command = [BLENDER_EXE, "--python", BUILDER_SCRIPT, "--", "--demo"]
    
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONHOME", None)
    clean_env.pop("PYTHONPATH", None)

    subprocess.run(command, env=clean_env)

if __name__ == "__main__":
    launch_demo()