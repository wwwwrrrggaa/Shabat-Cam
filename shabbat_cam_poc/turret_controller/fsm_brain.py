class BreechFSM:
    def __init__(
        self, breech_zone_bbox, expected_shell, expected_prop, patience_frames=8
    ):
        self.breech_zone = breech_zone_bbox
        self.patience = patience_frames

        self.expected_shell = expected_shell
        self.expected_prop = expected_prop

        # --- ARCHITECTURE CHANGE: DECOUPLING STATE FROM SAFETY ---
        self.sequence_state = "EMPTY"  # Physical progression
        self.safety_status = "CLEAR"  # Tactical validation
        self.chambered_inventory = []  # The "Final Tally" of what's inside

        self.frames_since_last_seen = 0
        self.last_known_bbox = None
        self.last_known_name = None

    def _intersects_breech(self, bbox):
        bx1, by1, bx2, by2 = self.breech_zone
        ox1, oy1 = min(bbox[0::2]), min(bbox[1::2])
        ox2, oy2 = max(bbox[0::2]), max(bbox[1::2])
        if ox1 < bx2 and ox2 > bx1 and oy1 < by2 and oy2 > by1:
            return True
        return False

    def trigger_danger(self, reason):
        # Once safety is compromised, latch the first error message
        if self.safety_status == "CLEAR":
            self.safety_status = reason
        print(f"\n[!!!] SAFETY COMPROMISED: {reason} [!!!]\n")

    def update(self, tracked_objects):
        shells = [obj for obj in tracked_objects if obj["class"] == 0]
        props = [obj for obj in tracked_objects if obj["class"] == 1]

        # ---------------------------------------------------------
        # STATE: EMPTY
        # ---------------------------------------------------------
        if self.sequence_state == "EMPTY":
            if props:
                self.trigger_danger("PROPELLANT DETECTED BEFORE SHELL.")
            elif shells:
                self.sequence_state = "SHELL_DETECTED"
                self.frames_since_last_seen = 0
                self.last_known_bbox = shells[0]["bbox"]
                self.last_known_name = shells[0]["name"]

        # ---------------------------------------------------------
        # STATE: SHELL_DETECTED
        # ---------------------------------------------------------
        elif self.sequence_state == "SHELL_DETECTED":
            if shells:
                self.frames_since_last_seen = 0
                self.last_known_bbox = shells[0]["bbox"]
                self.last_known_name = shells[0]["name"]
            else:
                self.frames_since_last_seen += 1
                if self.frames_since_last_seen > self.patience:
                    if self._intersects_breech(self.last_known_bbox):
                        # Shell is physically in! Update Tally.
                        self.chambered_inventory.append(self.last_known_name)
                        self.sequence_state = "SHELL_CHAMBERED"

                        # Validate what just went in
                        if self.last_known_name != self.expected_shell:
                            self.trigger_danger(
                                f"WRONG SHELL LOADED: {self.last_known_name}"
                            )

                        self.frames_since_last_seen = 0
                    else:
                        self.trigger_danger("SHELL DROPPED OUTSIDE BREECH.")
                        self.sequence_state = "EMPTY"  # Reset physical state

        # ---------------------------------------------------------
        # STATE: SHELL_CHAMBERED
        # ---------------------------------------------------------
        elif self.sequence_state == "SHELL_CHAMBERED":
            if shells:
                self.trigger_danger(
                    "DOUBLE LOAD DETECTED. SHELL PRESENTED TO LOADED BREECH."
                )
            elif props:
                self.sequence_state = "PROP_DETECTED"
                self.frames_since_last_seen = 0
                self.last_known_bbox = props[0]["bbox"]
                self.last_known_name = props[0]["name"]

        # ---------------------------------------------------------
        # STATE: PROP_DETECTED
        # ---------------------------------------------------------
        elif self.sequence_state == "PROP_DETECTED":
            if props:
                self.frames_since_last_seen = 0
                self.last_known_bbox = props[0]["bbox"]
                self.last_known_name = props[0]["name"]
            else:
                self.frames_since_last_seen += 1
                if self.frames_since_last_seen > self.patience:
                    if self._intersects_breech(self.last_known_bbox):
                        # Propellant is physically in! Update Tally.
                        self.chambered_inventory.append(self.last_known_name)
                        self.sequence_state = "SECURED"

                        # Validate what just went in
                        if self.last_known_name != self.expected_prop:
                            self.trigger_danger(
                                f"WRONG PROPELLANT: {self.last_known_name}"
                            )
                    else:
                        self.trigger_danger("PROPELLANT DROPPED OUTSIDE BREECH.")
                        self.sequence_state = (
                            "SHELL_CHAMBERED"  # Revert to previous physical state
                        )

        return self.sequence_state, self.safety_status, self.chambered_inventory