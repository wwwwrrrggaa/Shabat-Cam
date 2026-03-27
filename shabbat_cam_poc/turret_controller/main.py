import cv2
import numpy as np
import os
import subprocess
import glob
from vision_inference import VisionTracker
from fsm_brain import BreechFSM

# --- 1. PATH CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

BLENDER_EXE = os.path.join(PROJECT_ROOT, "blender_sim", "Blender", "blender.exe")
BUILDER_SCRIPT = os.path.join(PROJECT_ROOT, "blender_sim", "build_environment.py")
FRAMES_DIR = os.path.join(PROJECT_ROOT, "blender_sim", "training_data", "images", "train")
MODEL_WEIGHTS = os.path.join(PROJECT_ROOT, "ai_training", "runs", "obb", "Breech_AI", "yolo26_obb_v1", "weights", "best.pt")

OUTPUT_VIDEO = "mafat_poc_demo_final.mp4"

BREECH_ZONE = [240, 320, 400, 480]
AMMO_DB = {0: "M795 HE", 1: "M232A1 Charge"}
FIRE_MISSION = {"shell": "M825 Smoke", "prop": "M232A1 Charge"}


def generate_blender_frames():
    print("\n[1/4] Starting 3D Engine. Rendering 300 tactical frames...")
    command = [
        BLENDER_EXE,
        "--background",
        "--python",
        BUILDER_SCRIPT,
        "--",
        "--run_id",
        "999",
        "--frames",
        "300",
        "--ammo_type",
        "M795",
    ]
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONHOME", None)
    clean_env.pop("PYTHONPATH", None)
    subprocess.run(
        command, env=clean_env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
    )
    print("[1/4] High-Resolution Render complete.")


def draw_hud(frame, tracked_objects, seq_state, safety_status, inventory, frame_count):
    overlay = frame.copy()

    # 1. Top Banner (Safety vs Sequence)
    cv2.rectangle(overlay, (0, 0), (640, 60), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

    if safety_status != "CLEAR":
        if frame_count % 10 < 5:  # Flashing Red Banner
            cv2.rectangle(frame, (0, 0), (640, 60), (0, 0, 200), -1)
        cv2.putText(
            frame,
            f"SYSTEM HALT: {safety_status}",
            (10, 40),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
    else:
        if seq_state == "SECURED":
            cv2.putText(
                frame,
                "STATUS: SECURED - READY TO FIRE",
                (10, 40),
                cv2.FONT_HERSHEY_DUPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
        else:
            cv2.putText(
                frame,
                f"SEQUENCE: {seq_state}",
                (10, 40),
                cv2.FONT_HERSHEY_DUPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

    # 2. Breech Zone
    bx1, by1, bx2, by2 = BREECH_ZONE
    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 255, 255), 2)
    cv2.putText(
        frame, "BREECH", (bx1, by1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1
    )

    # 3. Fire Mission
    fm_x1, fm_y1 = 400, 70
    cv2.rectangle(frame, (fm_x1, fm_y1), (630, fm_y1 + 70), (40, 40, 40), -1)
    cv2.rectangle(frame, (fm_x1, fm_y1), (630, fm_y1 + 70), (200, 200, 200), 1)
    cv2.putText(
        frame,
        "FIRE MISSION",
        (fm_x1 + 10, fm_y1 + 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 200, 0),
        2,
    )
    cv2.putText(
        frame,
        f"Req: {FIRE_MISSION['shell']}",
        (fm_x1 + 10, fm_y1 + 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
    )
    cv2.putText(
        frame,
        f"Req: {FIRE_MISSION['prop']}",
        (fm_x1 + 10, fm_y1 + 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        1,
    )

    # 4. Inventory Box (The Final Tally)
    if len(inventory) > 0:
        inv_y = fm_y1 + 80
        cv2.rectangle(
            frame,
            (fm_x1, inv_y),
            (630, inv_y + 30 + (20 * len(inventory))),
            (20, 20, 80),
            -1,
        )
        cv2.rectangle(
            frame,
            (fm_x1, inv_y),
            (630, inv_y + 30 + (20 * len(inventory))),
            (100, 100, 255),
            1,
        )
        cv2.putText(
            frame,
            "CHAMBER INVENTORY",
            (fm_x1 + 10, inv_y + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (100, 100, 255),
            2,
        )
        for idx, item in enumerate(inventory):
            cv2.putText(
                frame,
                f"- {item}",
                (fm_x1 + 10, inv_y + 45 + (idx * 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
            )

    # 5. OBB Drawings & Real-time Mismatch warning
    mismatch_detected = False
    for obj in tracked_objects:
        obj["name"] = AMMO_DB.get(obj["class"], "UNKNOWN")
        pts = np.array(obj["bbox"], np.int32).reshape((-1, 1, 2))
        color = (0, 255, 0) if obj["class"] == 0 else (255, 100, 0)

        cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)
        cv2.putText(
            frame,
            f"ID:{obj['id']} {obj['name']}",
            (pts[0][0][0], pts[0][0][1] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

        if obj["class"] == 0 and obj["name"] != FIRE_MISSION["shell"]:
            mismatch_detected = True
        if obj["class"] == 1 and obj["name"] != FIRE_MISSION["prop"]:
            mismatch_detected = True

    if mismatch_detected and safety_status == "CLEAR":
        cv2.putText(
            frame,
            "MISMATCH DETECTED!",
            (fm_x1 - 50, fm_y1 + 180),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

    return frame


def run_pipeline():
    print("--- Initializing AI Breech Monitor POC ---")
    # generate_blender_frames() # UNCOMMENT THIS ON FIRST RUN!

    tracker = VisionTracker(MODEL_WEIGHTS)
    fsm = BreechFSM(
        BREECH_ZONE,
        expected_shell=FIRE_MISSION["shell"],
        expected_prop=FIRE_MISSION["prop"],
        patience_frames=8,
    )

    frame_files = sorted(glob.glob(os.path.join(FRAMES_DIR, "run_999_M795_f*.png")))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, 15.0, (640, 640))

    frame_count = 0
    for img_path in frame_files:
        frame = cv2.imread(img_path)
        if frame is None:
            continue
        frame = cv2.resize(frame, (640, 640))
        frame_count += 1

        objects = tracker.process_frame(frame)
        for obj in objects:
            obj["name"] = AMMO_DB.get(obj["class"], "UNKNOWN")

        seq_state, safety_status, inventory = fsm.update(objects)
        final_frame = draw_hud(
            frame, objects, seq_state, safety_status, inventory, frame_count
        )

        out.write(final_frame)
        cv2.imshow("M109 AI Monitor", final_frame)
        if cv2.waitKey(40) & 0xFF == ord("q"):
            break

    out.release()
    cv2.destroyAllWindows()
    print(f"\n[4/4] SUCCESS! Demo Video saved to: {os.path.abspath(OUTPUT_VIDEO)}")

if __name__ == "__main__":
    run_pipeline()