from ultralytics import YOLO


class VisionTracker:
    def __init__(self, model_path="best.pt"):
        print(f"[Vision] Loading Tactical Model: {model_path}")
        self.model = YOLO(model_path)
        # Dictionary to map YOLO class indices to names
        self.names = {0: "Shell", 1: "Propellant"}

    def process_frame(self, frame):
        """
        Runs YOLO OBB + BoT-SORT tracking on a single frame.
        Returns a list of detected objects formatted for the FSM.
        """
        # persist=True keeps the tracker memory alive across frames
        # tracker="botsort.yaml" is the modern, highly-accurate alternative to DeepSORT
        results = self.model.track(
            frame, persist=True, tracker="botsort.yaml", verbose=False
        )

        tracked_objects = []

        if results[0].obb is not None:
            obbs = results[0].obb
            for i in range(len(obbs)):
                # Extract class and confidence
                cls_id = int(obbs.cls[i].item())
                conf = obbs.conf[i].item()

                # Extract Tracking ID (if tracker lost it momentarily, skip)
                if obbs.id is None:
                    continue
                track_id = int(obbs.id[i].item())

                # Extract the 4 corners of the OBB [x1, y1, x2, y2, x3, y3, x4, y4]
                # Flatten the (4, 2) array into a flat list of 8 floats
                points = obbs.xyxyxyxy[i].cpu().numpy().flatten().tolist()

                tracked_objects.append(
                    {
                        "id": track_id,
                        "class": cls_id,
                        "name": self.names[cls_id],
                        "conf": conf,
                        "bbox": points,
                    }
                )

        return tracked_objects