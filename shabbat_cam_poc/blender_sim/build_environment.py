import bpy
import bmesh
import sys
import os
import argparse
import math
import random
import mathutils
import json
from bpy_extras.object_utils import world_to_camera_view

# --- 1. PARSE ARGUMENTS ---
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1 :]
else:
    argv = []

parser = argparse.ArgumentParser()
parser.add_argument("--demo", action="store_true")
parser.add_argument("--run_id", type=int, default=0)
parser.add_argument("--frames", type=int, default=50)
parser.add_argument("--ammo_type", type=str, default="M795")
args, unknown = parser.parse_known_args(argv)

selected_ammo = args.ammo_type
YOLO_CLASSES = {"Shell": 0, "Propellant": 1}

# --- CONTROLLED SCENE JITTER ---
cam_j_x = random.uniform(-0.08, 0.08)
cam_j_y = random.uniform(-0.08, 0.08)
cam_rot_j = random.uniform(-0.05, 0.05)
place_j_x = random.uniform(-0.04, 0.04)
gun_yaw = random.uniform(-0.5, 0.5)
gun_pitch = random.uniform(0.0, 0.5)

bot_color = (
    random.uniform(0.05, 0.2),
    random.uniform(0.2, 0.4),
    random.uniform(0.05, 0.2),
)

# --- 2. CLEAN ENVIRONMENT ---
for obj in bpy.data.objects:
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in bpy.data.meshes:
    bpy.data.meshes.remove(mesh, do_unlink=True)
base_dir = os.path.dirname(os.path.abspath(__file__))


# --- 3. MATERIALS ---
def create_material(name, base_color, emission=0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (
            base_color[0],
            base_color[1],
            base_color[2],
            1,
        )
        if emission > 0:
            em_input = bsdf.inputs.get("Emission") or bsdf.inputs.get("Emission Color")
            if em_input:
                em_input.default_value = (
                    base_color[0],
                    base_color[1],
                    base_color[2],
                    1,
                )
            strength_input = bsdf.inputs.get("Emission Strength")
            if strength_input:
                strength_input.default_value = emission
    return mat


def create_textured_wall():
    mat = bpy.data.materials.new("Textured_Wall")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    wall_tint = random.uniform(-0.05, 0.05)
    bsdf.inputs["Base Color"].default_value = (
        0.45 + wall_tint,
        0.45 + wall_tint,
        0.40 + wall_tint,
        1.0,
    )
    bsdf.inputs["Roughness"].default_value = random.uniform(0.6, 0.9)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = random.uniform(100.0, 200.0)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    mat.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    mat.node_tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


materials = {
    "M795": create_material("M795_Olive", (0.2, 0.3, 0.1)),
    "M825": create_material("M825_Seafoam", (0.3, 0.6, 0.4)),
    "M107": create_material("M107_Olive", (0.15, 0.25, 0.1)),
    "WhiteBag": create_material("White_Cloth", (0.8, 0.8, 0.8)),
    "RedBag": create_material("Red_Cloth", (0.8, 0.1, 0.1)),
    "BotGreen": create_material("Bot_Green", bot_color),
    "BlackHelmet": create_material("Helmet_Black", (0.015, 0.015, 0.015)),
    "HelmetStripe": create_material("Helmet_Stripe", (0.9, 0.9, 0.9)),
    "VisorWhite": create_material("Visor_White", (1.0, 1.0, 1.0), emission=15.0),
    "BlackMetal": create_material("Black_Metal", (0.02, 0.02, 0.02)),
    "GunMetal": create_material("Gun_Metal", (0.05, 0.05, 0.05)),
    "TexturedRoom": create_textured_wall(),
}


def spawn_robot_crew(name, location):
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.0, location=(0, 0, 0.5))
    body = bpy.context.view_layer.objects.active
    body.data.materials.append(materials["BotGreen"])
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.2, location=(0, 0, 1.1))
    neck = bpy.context.view_layer.objects.active
    neck.data.materials.append(materials["BlackMetal"])
    bpy.ops.mesh.primitive_cube_add(size=0.45, location=(0, 0, 1.45))
    head = bpy.context.view_layer.objects.active
    head.data.materials.append(materials["BotGreen"])
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.08, depth=0.05, location=(-0.12, 0.23, 1.45)
    )
    eye_l = bpy.context.view_layer.objects.active
    eye_l.rotation_euler[0] = 1.5708
    eye_l.data.materials.append(materials["VisorWhite"])
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.08, depth=0.05, location=(0.12, 0.23, 1.45)
    )
    eye_r = bpy.context.view_layer.objects.active
    eye_r.rotation_euler[0] = 1.5708
    eye_r.data.materials.append(materials["VisorWhite"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.38, location=(0, 0, 1.60))
    helmet = bpy.context.view_layer.objects.active
    helmet.scale[2] = 0.6
    helmet.data.materials.append(materials["BlackHelmet"])
    bpy.ops.mesh.primitive_cylinder_add(radius=0.39, depth=0.03, location=(0, 0, 1.50))
    stripe = bpy.context.view_layer.objects.active
    stripe.data.materials.append(materials["HelmetStripe"])
    bpy.ops.object.select_all(action="DESELECT")
    for p in [body, neck, head, eye_l, eye_r, helmet, stripe]:
        p.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    bot = bpy.context.view_layer.objects.active
    bot.name = name
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="BOUNDS")
    bot.location = location
    return bot


def import_asset(
    filepaths, name, material, scale=(0.001, 0.001, 0.001), yolo_class=None
):
    imported = []
    for path in filepaths:
        if os.path.exists(path):
            before = set(bpy.data.objects)
            if path.endswith(".stl"):
                bpy.ops.wm.stl_import(filepath=path)
            imported.extend(list(set(bpy.data.objects) - before))
    meshes = [o for o in imported if o.type == "MESH"]
    if meshes:
        bpy.ops.object.select_all(action="DESELECT")
        for m in meshes:
            m.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        if len(meshes) > 1:
            bpy.ops.object.join()
        final = bpy.context.view_layer.objects.active
        final.name, final.scale = name, scale
        final.data.materials.clear()
        final.data.materials.append(material)
        if yolo_class is not None:
            final["yolo_class"] = yolo_class
        return final
    return None


# --- 4. ENVIRONMENT ---
room_obj = bpy.ops.mesh.primitive_cube_add(size=5, location=(0, 0, 1.75))
room_obj = bpy.context.view_layer.objects.active
room_obj.scale[2] = 3.5 / 5.0
room_obj.data.materials.append(materials["TexturedRoom"])
bm = bmesh.new()
bm.from_mesh(room_obj.data)
bmesh.ops.reverse_faces(bm, faces=bm.faces)
bm.to_mesh(room_obj.data)
bm.free()

LOAD_Z = 1.38
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 1.5, LOAD_Z))
gun_pivot = bpy.context.view_layer.objects.active
gun_pivot.rotation_euler = (gun_pitch, 0, gun_yaw)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.25 - LOAD_Z))
tray_obj = bpy.context.view_layer.objects.active
tray_obj.scale = (0.2, 0.5, 0.05)
tray_obj.data.materials.append(materials["BlackMetal"])
tray_obj.parent = gun_pivot

bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.8, location=(0, 0.65, 0))
breech = bpy.context.view_layer.objects.active
breech.rotation_euler[0] = 1.5708
breech.data.materials.append(materials["GunMetal"])
bpy.ops.mesh.primitive_cylinder_add(radius=0.155, depth=0.9, location=(0, 0.65, 0))
hole = bpy.context.view_layer.objects.active
hole.rotation_euler[0] = 1.5708
mod = breech.modifiers.new("Hollow_Breech", "BOOLEAN")
mod.object, mod.operation = hole, "DIFFERENCE"
bpy.context.view_layer.objects.active = breech
bpy.ops.object.modifier_apply(modifier="Hollow_Breech")
bpy.data.objects.remove(hole, do_unlink=True)
breech.parent = gun_pivot
breech.name = "Breech"

bpy.ops.object.camera_add(
    location=(cam_j_x, 1.8 + cam_j_y, 3.4), rotation=(cam_rot_j, cam_rot_j, 0)
)
cam = bpy.context.view_layer.objects.active
cam.data.lens = random.uniform(17, 19)
bpy.context.scene.camera = cam

bpy.ops.object.light_add(
    type="SPOT", location=(-1.5 + random.uniform(-0.5, 0.5), -0.5, 3.2)
)
spot = bpy.context.view_layer.objects.active
spot.rotation_euler = (0.4, 0.4, 0)
spot.data.energy = random.uniform(1000, 2500)
spot.data.spot_size = random.uniform(1.4, 1.8)
spot.data.color = (1.0, random.uniform(0.85, 1.0), random.uniform(0.7, 1.0))
bpy.ops.object.light_add(type="POINT", location=(1.5, 1.0, 2.0))
bpy.context.view_layer.objects.active.data.energy = random.uniform(50, 200)

# --- 5. CREW ---
gunner = spawn_robot_crew("Bot_Gunner", (-1.8, 1.2, 0))
loader = spawn_robot_crew("Bot_Loader", (-0.8, -2.0, 0))
mekhases = spawn_robot_crew("Bot_Mekhases", (1.8, 0.8, 0))

# --- 6. ASSETS ---
m795_dir = os.path.join(base_dir, "M795 155mm shell with M782 fuze - 5428784", "files")
m795_parts = [os.path.join(m795_dir, "shell.stl"), os.path.join(m795_dir, "fuze.stl")]
m107_dir = os.path.join(base_dir, "155mm M107 Howitzer Shell - 4181391", "files")
bag_parts = [os.path.join(m107_dir, "propellant_charge.stl")]

active_shell = import_asset(
    m795_parts,
    "Active_Shell",
    materials[selected_ammo],
    (0.001, 0.001, 0.001),
    YOLO_CLASSES["Shell"],
)
prop_type = "RedBag" if selected_ammo == "M825" else "WhiteBag"
active_prop = import_asset(
    bag_parts,
    "Active_Prop",
    materials[prop_type],
    (0.001, 0.001, 0.001),
    YOLO_CLASSES["Propellant"],
)

fs = import_asset(
    m795_parts, "Floor_Shell", materials[selected_ammo], (0.001, 0.001, 0.001)
)
if fs:
    fs.location, fs.rotation_euler = (-1.8, -1.8, 0.35), (0, 0, 0)

# --- 7. KINEMATICS ---

# Persistent state to capture actual bot positions at phase transitions,
# preventing teleportation caused by discrete frame sampling never landing
# exactly on a phase boundary (e.g. t=0.45 or t=0.90).
_phase_state = {
    "loader_retreat_start": None,
    "mekhases_retreat_start": None,
}


def update_scene(t, frame):
    import mathutils
    import math

    # 1. CONSTANT ANCHORS
    l_home = mathutils.Vector((-0.8, -2.0, 0))
    m_home = mathutils.Vector((1.8, 0.8, 0))
    gunner.location = mathutils.Vector((-1.8, 1.2, 0))

    # 2. DYNAMIC BREECH ANCHORS (Calculated every frame to handle Jitter)
    # The exact entry point of the shell into the metal
    b_entry = gun_pivot.matrix_world @ mathutils.Vector((0, -0.2, 0))
    # The exact deepest point of the ramming
    b_deep = gun_pivot.matrix_world @ mathutils.Vector((0, 0.9, 0))

    # The bot's position when the shell is at the entry/deep points
    l_at_entry = mathutils.Vector((b_entry.x - 0.4, b_entry.y - 0.4, 0))
    l_at_deep  = mathutils.Vector((b_deep.x  - 0.4, b_deep.y  - 0.4, 0))

    m_at_entry = mathutils.Vector((b_entry.x + 0.4, b_entry.y - 0.4, 0))
    m_at_deep  = mathutils.Vector((b_deep.x  + 0.4, b_deep.y  - 0.4, 0))

    # ==========================================
    # LOADER (SHELL) TIMELINE (0.0 to 0.6)
    # ==========================================
    if t < 0.25:
        # APPROACH: Walk from Home to Breech Entry
        f = t / 0.25
        loader.location = l_home.lerp(l_at_entry, f)
        active_shell.location = loader.location + mathutils.Vector((0.4, 0.4, 0.8))
        active_shell.rotation_euler = (1.5708, 0, 0)
        # Reset retreat anchor so it's re-captured fresh this cycle
        _phase_state["loader_retreat_start"] = None

    elif t < 0.45:
        # RAMMING: Coupled movement from Entry to Deep
        f = (t - 0.25) / 0.2
        active_shell.location = b_entry.lerp(b_deep, f)
        active_shell.rotation_euler = (gun_pitch, 0, gun_yaw)
        loader.location = mathutils.Vector((
            active_shell.location.x - 0.4,
            active_shell.location.y - 0.4,
            0.0,
        ))
        # Continuously snapshot so the LAST ramming frame is always captured.
        # This is the fix: we record where the loader actually IS at the end
        # of ramming, rather than recomputing it from b_deep in the retreat
        # phase (which can differ due to frame sampling never hitting t=0.45).
        _phase_state["loader_retreat_start"] = loader.location.copy()

    elif t < 0.60:
        # RETREAT: Shell gone. Walk back to Home.
        active_shell.location.z = -10
        # Use the captured end-of-ramming position as our start point so
        # the first retreat frame continues exactly from where the loader was.
        retreat_start = _phase_state["loader_retreat_start"] or l_at_deep
        f = (t - 0.45) / 0.15
        ease_f = 0.5 - math.cos(f * math.pi) * 0.5
        loader.location = retreat_start.lerp(l_home, ease_f)

    else:
        # IDLE: Stay at home
        active_shell.location.z = -10
        loader.location = l_home

    # ==========================================
    # MEKHASES (PROPELLANT) TIMELINE (0.5 to 1.0)
    # ==========================================
    if t < 0.55:
        active_prop.location.z = -10
        mekhases.location = m_home
        # Reset retreat anchor so it's re-captured fresh this cycle
        _phase_state["mekhases_retreat_start"] = None

    elif t < 0.75:
        # APPROACH: Walk from Home to Breech Entry
        f = (t - 0.55) / 0.2
        mekhases.location = m_home.lerp(m_at_entry, f)
        active_prop.location = mekhases.location + mathutils.Vector((-0.4, 0.4, 0.8))
        active_prop.rotation_euler = (0, 0, 0)
        _phase_state["mekhases_retreat_start"] = None

    elif t < 0.90:
        # RAMMING: Coupled movement from Entry to Deep
        f = (t - 0.75) / 0.15
        active_prop.location = b_entry.lerp(b_deep, f)
        active_prop.rotation_euler = (1.5708 + gun_pitch, 0, gun_yaw)
        mekhases.location = mathutils.Vector((
            active_prop.location.x + 0.4,
            active_prop.location.y - 0.4,
            0.0,
        ))
        # Same fix as loader: snapshot the actual end-of-ramming position.
        _phase_state["mekhases_retreat_start"] = mekhases.location.copy()

    elif t <= 1.0:
        # RETREAT: Propellant gone. Walk back to Home.
        active_prop.location.z = -10
        retreat_start = _phase_state["mekhases_retreat_start"] or m_at_deep
        f = (t - 0.90) / 0.1
        ease_f = 0.5 - math.cos(f * math.pi) * 0.5
        mekhases.location = retreat_start.lerp(m_home, ease_f)


def get_obb(scene, cam_ob, mesh_ob):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    if mesh_ob.location.z < -4.0:
        return None
    mat = mesh_ob.matrix_world
    visible_hits = 0
    total_test_points = 10
    for i in range(total_test_points):
        z_offset = -0.4 + (0.8 * (i / (total_test_points - 1)))
        world_pt = mat @ mathutils.Vector((0, 0, z_offset))
        direction = world_pt - cam_ob.location
        hit, _, _, _, hit_obj, _ = scene.ray_cast(
            depsgraph,
            cam_ob.location,
            direction.normalized(),
            distance=direction.length + 0.05,
        )
        if not hit or hit_obj.name.startswith(mesh_ob.name):
            visible_hits += 1
    if (visible_hits / total_test_points) < 0.2:
        return None
    points_2d = []
    for corner in mesh_ob.bound_box:
        co_ndc = world_to_camera_view(scene, cam_ob, mat @ mathutils.Vector(corner))
        if 0.0 <= co_ndc.x <= 1.0 and 0.0 <= co_ndc.y <= 1.0 and co_ndc.z > 0:
            points_2d.append((co_ndc.x, 1.0 - co_ndc.y))
    if len(points_2d) < 4:
        return None
    min_area = float("inf")
    best_corners = None
    for i in range(0, 90, 5):
        angle = math.radians(i)
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        rx = [p[0] * cos_a - p[1] * sin_a for p in points_2d]
        ry = [p[0] * sin_a + p[1] * cos_a for p in points_2d]
        area = (max(rx) - min(rx)) * (max(ry) - min(ry))
        if area < min_area:
            min_area = area
            best_corners = []
            for cx, cy in [
                (min(rx), min(ry)),
                (max(rx), min(ry)),
                (max(rx), max(ry)),
                (min(rx), max(ry)),
            ]:
                best_corners.extend([cx * cos_a + cy * sin_a, -cx * sin_a + cy * cos_a])
    return [max(0, min(1, c)) for c in best_corners]


def export_labels(filepath, scene, cam):
    lines = []
    for obj in [active_shell, active_prop]:
        obb = get_obb(scene, cam, obj)
        if obb:
            lines.append(f"{obj['yolo_class']} " + " ".join([f"{c:.6f}" for c in obb]))
    with open(filepath, "w") as f:
        f.write("\n".join(lines))


# --- EXECUTION ---
scene = bpy.context.scene
rgb_dir = os.path.join(base_dir, "training_data", "images", "train")
label_dir = os.path.join(base_dir, "training_data", "labels", "train")
os.makedirs(rgb_dir, exist_ok=True)
os.makedirs(label_dir, exist_ok=True)

for f_idx in range(args.frames):
    update_scene(f_idx / (args.frames - 1), f_idx)
    bpy.context.view_layer.update()
    name = f"run_{args.run_id:03d}_{selected_ammo}_f{f_idx:04d}"
    scene.render.filepath = os.path.join(rgb_dir, name + ".png")
    bpy.ops.render.render(write_still=True)
    export_labels(os.path.join(label_dir, name + ".txt"), scene, cam)