import bpy
import bmesh
import sys
import os
import argparse
import math
import random
import mathutils
import json

# Ensure Blender import addons for common mesh formats are enabled. If these fail we want
# Blender to raise so the user can see the problem (per request: don't swallow errors).
bpy.ops.wm.addon_enable(module='io_mesh_stl')
bpy.ops.wm.addon_enable(module='io_mesh_3mf')

# --- 1. PARSE ARGUMENTS ---
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

parser = argparse.ArgumentParser()
parser.add_argument("--render", action="store_true")
parser.add_argument("--demo", action="store_true")
parser.add_argument("--run_id", type=int, default=0)
parser.add_argument("--frames", type=int, default=50)
parser.add_argument("--ammo_type", type=str, default="M795")
args, unknown = parser.parse_known_args(argv)

selected_ammo = args.ammo_type

YOLO_CLASSES = { "Shell": 0, "Propellant": 1 }

# --- CONTROLLED SCENE JITTER (Constant per Run) ---
cam_j_x = random.uniform(-0.08, 0.08)
cam_j_y = random.uniform(-0.08, 0.08)
cam_rot_j = random.uniform(-0.05, 0.05)
place_j_x = random.uniform(-0.04, 0.04)

gun_yaw = random.uniform(-0.5, 0.5)
gun_pitch = random.uniform(0.0, 0.5)

bot_r, bot_g, bot_b = random.uniform(0.05, 0.2), random.uniform(0.2, 0.4), random.uniform(0.05, 0.2)
bot_color = (bot_r, bot_g, bot_b)

# --- 2. CLEAN ENVIRONMENT ---
for obj in bpy.data.objects: bpy.data.objects.remove(obj, do_unlink=True)
for mesh in bpy.data.meshes: bpy.data.meshes.remove(mesh, do_unlink=True)

base_dir = os.path.dirname(os.path.abspath(__file__))

# --- 3. MATERIALS ---
def create_material(name, base_color, emission=0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (base_color[0], base_color[1], base_color[2], 1)
        if emission > 0:
            bsdf.inputs["Emission Color"].default_value = (base_color[0], base_color[1], base_color[2], 1)
            bsdf.inputs["Emission Strength"].default_value = emission
    return mat

def create_textured_wall():
    mat = bpy.data.materials.new("Textured_Wall")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    wall_tint = random.uniform(-0.05, 0.05)
    bsdf.inputs["Base Color"].default_value = (0.45 + wall_tint, 0.45 + wall_tint, 0.40 + wall_tint, 1.0)
    bsdf.inputs["Roughness"].default_value = random.uniform(0.6, 0.9)
    noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = random.uniform(100.0, 200.0)
    bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35
    mat.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    mat.node_tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat

materials = {
    "M795": create_material("M795_Olive", (0.2, 0.3, 0.1)),
    "M825": create_material("M825_Seafoam", (0.3, 0.6, 0.4)),
    "M107": create_material("M107_Olive", (0.15, 0.25, 0.1)),
    "WhiteBag": create_material("White_Cloth", (0.8, 0.8, 0.8)),
    "RedBag": create_material("Red_Cloth", (0.8, 0.1, 0.1)),
    "BotGreen": create_material("Bot_Green", bot_color), # Now randomized per scene
    "BlackHelmet": create_material("Helmet_Black", (0.015, 0.015, 0.015)),
    "HelmetStripe": create_material("Helmet_Stripe", (0.9, 0.9, 0.9)),
    "VisorWhite": create_material("Visor_White", (1.0, 1.0, 1.0), emission=15.0),
    "BlackMetal": create_material("Black_Metal", (0.02, 0.02, 0.02)),
    "GunMetal": create_material("Gun_Metal", (0.05, 0.05, 0.05)),
    "TexturedRoom": create_textured_wall()
}

def spawn_robot_crew(name, location):
    bpy.context.scene.cursor.location = (0,0,0)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.0, location=(0,0,0.5))
    body = bpy.context.view_layer.objects.active; body.data.materials.append(materials["BotGreen"])
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.2, location=(0,0,1.1))
    neck = bpy.context.view_layer.objects.active; neck.data.materials.append(materials["BlackMetal"])
    bpy.ops.mesh.primitive_cube_add(size=0.45, location=(0,0,1.45))
    head = bpy.context.view_layer.objects.active; head.data.materials.append(materials["BotGreen"])
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.05, location=(-0.12, 0.23, 1.45))
    eye_l = bpy.context.view_layer.objects.active; eye_l.rotation_euler[0] = 1.5708; eye_l.data.materials.append(materials["VisorWhite"])
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.05, location=(0.12, 0.23, 1.45))
    eye_r = bpy.context.view_layer.objects.active; eye_r.rotation_euler[0] = 1.5708; eye_r.data.materials.append(materials["VisorWhite"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.38, location=(0,0,1.60))
    helmet = bpy.context.view_layer.objects.active; helmet.scale[2] = 0.6; helmet.data.materials.append(materials["BlackHelmet"])
    bpy.ops.mesh.primitive_cylinder_add(radius=0.39, depth=0.03, location=(0,0,1.50))
    stripe = bpy.context.view_layer.objects.active; stripe.data.materials.append(materials["HelmetStripe"])

    bpy.ops.object.select_all(action='DESELECT')
    for p in [body, neck, head, eye_l, eye_r, helmet, stripe]: p.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    bot = bpy.context.view_layer.objects.active; bot.name = name
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS'); bot.location = location
    return bot

def import_asset(filepaths, name, material, scale=(0.001, 0.001, 0.001), yolo_class=None):
    imported = []
    for path in filepaths:
        if os.path.exists(path):
            before = set(bpy.data.objects)
            # Call the exact import operator for the file extension. Do not swallow errors;
            # let Blender raise if an importer is missing or the file is invalid.
            ext = os.path.splitext(path)[1].lower()
            if ext == '.stl':
                bpy.ops.import_mesh.stl(filepath=path)
            elif ext == '.3mf':
                bpy.ops.import_mesh.threemf(filepath=path)
            else:
                # For any other extension (e.g., .step) invoke a generic import attempt that will fail
                # loudly if no operator exists — this is intentional per project policy.
                bpy.ops.import_scene.autodetect(filepath=path)
            imported.extend(list(set(bpy.data.objects) - before))
    meshes = [o for o in imported if o.type == 'MESH']
    if meshes:
        bpy.ops.object.select_all(action='DESELECT')
        for m in meshes: m.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        if len(meshes) > 1: bpy.ops.object.join()
        final = bpy.context.view_layer.objects.active
        final.name, final.scale = name, scale
        final.data.materials.clear(); final.data.materials.append(material)
        if yolo_class is not None: final["yolo_class"] = yolo_class
        return final
    return None

# --- 4. ENVIRONMENT WITH DYNAMIC GUN ASSEMBLY ---
room = bpy.ops.mesh.primitive_cube_add(size=5, location=(0, 0, 1.75))
room_obj = bpy.context.view_layer.objects.active; room_obj.scale[2] = 3.5 / 5.0
room_obj.data.materials.append(materials["TexturedRoom"])
bm = bmesh.new(); bm.from_mesh(room_obj.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(room_obj.data); bm.free()

LOAD_Z = 1.38
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 1.5, LOAD_Z))
gun_pivot = bpy.context.view_layer.objects.active; gun_pivot.rotation_euler = (gun_pitch, 0, gun_yaw)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.25 - LOAD_Z))
tray_obj = bpy.context.view_layer.objects.active; tray_obj.scale = (0.2, 0.5, 0.05); tray_obj.data.materials.append(materials["BlackMetal"])
tray_obj.parent = gun_pivot

bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.8, location=(0, 2.15 - 1.5, 0))
breech = bpy.context.view_layer.objects.active; breech.rotation_euler[0] = 1.5708; breech.data.materials.append(materials["GunMetal"])
bpy.ops.mesh.primitive_cylinder_add(radius=0.155, depth=0.9, location=(0, 2.15 - 1.5, 0))
hole = bpy.context.view_layer.objects.active; hole.rotation_euler[0] = 1.5708
mod = breech.modifiers.new("Hollow_Breech", 'BOOLEAN'); mod.object, mod.operation = hole, 'DIFFERENCE'
bpy.context.view_layer.objects.active = breech; bpy.ops.object.modifier_apply(modifier="Hollow_Breech")
bpy.data.objects.remove(hole, do_unlink=True); breech.parent = gun_pivot

bpy.ops.object.camera_add(location=(0 + cam_j_x, 1.8 + cam_j_y, 3.4), rotation=(cam_rot_j, cam_rot_j, 0))
sensor = bpy.context.view_layer.objects.active; sensor.data.lens = random.uniform(17, 19); bpy.context.scene.camera = sensor

bpy.ops.object.light_add(type='SPOT', location=(-1.5 + random.uniform(-0.5, 0.5), -0.5, 3.2))
spot = bpy.context.view_layer.objects.active; spot.rotation_euler = (0.4, 0.4, 0); spot.data.energy = random.uniform(1000, 2500)
spot.data.spot_size = random.uniform(1.4, 1.8); spot.data.color = (1.0, random.uniform(0.85, 1.0), random.uniform(0.7, 1.0))
bpy.ops.object.light_add(type='POINT', location=(1.5, 1.0, 2.0))
fill = bpy.context.view_layer.objects.active; fill.data.energy = random.uniform(50, 200)

# --- 5. CREW ---
gunner = spawn_robot_crew("Bot_Gunner", (-1.8, 1.2, 0))
loader = spawn_robot_crew("Bot_Loader", (-0.8, -2.0, 0))
mekhases = spawn_robot_crew("Bot_Mekhases", (1.8, 0.8, 0))

# --- 6. ASSETS & CLUTTER PLACEMENT ---
m795_dir = os.path.join(base_dir, "M795 155mm shell with M782 fuze - 5428784", "files")
m795_parts = [os.path.join(m795_dir, "shell.stl"), os.path.join(m795_dir, "fuze.stl")]
m107_dir = os.path.join(base_dir, "155mm M107 Howitzer Shell - 4181391", "files")
bag_parts = [os.path.join(m107_dir, "propellant_charge.stl")]

shell_pool = [
    {"type": "M795", "parts": m795_parts, "mat": materials["M795"], "scale": (0.001, 0.001, 0.001)},
    {"type": "M825", "parts": m795_parts, "mat": materials["M825"], "scale": (0.00095, 0.00095, 0.0011)},
    {"type": "M107", "parts": m795_parts, "mat": materials["M107"], "scale": (0.00105, 0.00105, 0.0008)}
]

s_data = next(item for item in shell_pool if item["type"] == selected_ammo)
active_shell = import_asset(s_data["parts"], "Active_Shell", s_data["mat"], s_data["scale"], yolo_class=YOLO_CLASSES["Shell"])
prop_type = "RedBag" if selected_ammo == "M825" else "WhiteBag"
active_prop = import_asset(bag_parts, "Active_Prop", materials[prop_type], yolo_class=YOLO_CLASSES["Propellant"])

remaining_shells = [item for item in shell_pool if item["type"] != selected_ammo]
for i, r_s in enumerate(remaining_shells):
    fs = import_asset(r_s["parts"], f"Floor_{r_s['type']}", r_s["mat"], r_s["scale"])
    if fs: fs.location, fs.rotation_euler = (-1.8 - (i * 0.4), -1.8, 0.35), (0, 0, 0)

fb0 = import_asset(bag_parts, "Floor_Bag_White", materials["WhiteBag"])
if fb0:
    fb0.location, fb0.rotation_euler = (2.0, 1.6, 0.25), (0, 0, 0)

fb1 = import_asset(bag_parts, "Floor_Bag_Red", materials["RedBag"])
if fb1:
    fb1.location, fb1.rotation_euler = (2.0, 2.0, 0.25), (0, 0, 0)
# --- 7. KINEMATICS ---
def update_scene(t, frame):
    SHELL_STAND, SHELL_LOAD = 1.5708, 0.0
    PROP_STAND, PROP_LOAD = 0.0, 1.5708
    loader_home, mekhases_home = (-0.8, -2.0), (1.8, 0.8)
    prop_start = (1.8, 1.2)
    tgt_x = 0.0 + place_j_x

    jit = lambda amp: math.sin(frame * 0.5) * amp # Deterministic micro-jitter
    gunner.location.x, gunner.location.y = -1.8 + jit(0.02), 1.2 + jit(0.02)

    active_shell.location, active_shell.rotation_euler[0] = (-1.2 + jit(0.01), -2.0 + jit(0.01), 0.4), SHELL_STAND
    active_prop.location, active_prop.rotation_euler[0] = (prop_start[0] + jit(0.01), prop_start[1] + jit(0.01), 0.3), PROP_STAND
    loader.location.x, loader.location.y, loader.rotation_euler[2] = loader_home[0], loader_home[1], 0
    mekhases.location.x, mekhases.location.y, mekhases.rotation_euler[2] = mekhases_home[0], mekhases_home[1], 1.57

    if t < 0.25:
        f = t / 0.25
        cx, cy = -1.2 + (tgt_x - -1.2)*f, -2.0 + (0.6 - -2.0)*f
        active_shell.location = (cx + jit(0.01), cy + jit(0.01), 0.8)
        loader.location.x, loader.location.y = cx - 0.4, cy - 0.4
    elif t < 0.35:
        f = (t - 0.25) / 0.1
        start_loc = mathutils.Vector((tgt_x, 0.8, 0.8))
        target_loc = gun_pivot.matrix_world @ mathutils.Vector((0, -0.1, 0))
        active_shell.location = start_loc.lerp(target_loc, f)
        active_shell.rotation_euler[0] = SHELL_STAND + (f * (SHELL_LOAD - SHELL_STAND)) + (f * gun_pitch)
        active_shell.rotation_euler[2] = (f * gun_yaw)
        loader.location.x, loader.location.y = active_shell.location.x - 0.4, active_shell.location.y - 0.4
    elif t < 0.45:
        f = (t - 0.35) / 0.1
        local_slide = mathutils.Vector((0, -0.1 + (f * 1.0), 0))
        active_shell.location = gun_pivot.matrix_world @ local_slide
        active_shell.rotation_euler[0] = SHELL_LOAD + gun_pitch; active_shell.rotation_euler[2] = gun_yaw
        loader.location.x, loader.location.y = active_shell.location.x - 0.4, active_shell.location.y - 0.6
    elif t < 0.55:
        active_shell.location.z = -5
        f = (t - 0.45) / 0.10
        loader.location.x, loader.location.y, loader.rotation_euler[2] = -0.4 - 0.4*f, 1.3 - 3.3*f, 3.14
    elif t > 0.6 and t < 0.75:
        active_shell.location.z = -5
        f = (t - 0.6) / 0.15
        cx, cy = prop_start[0] - (prop_start[0] - tgt_x)*f, prop_start[1] - (prop_start[1] - 0.8)*f
        active_prop.location = (cx + jit(0.01), cy + jit(0.01), 0.8)
        mekhases.location.x, mekhases.location.y, mekhases.rotation_euler[2] = cx + 0.4, cy - 0.4, 0
    elif t >= 0.75 and t < 0.85:
        active_shell.location.z = -5
        f = (t - 0.75) / 0.1
        start_loc = mathutils.Vector((tgt_x, 0.8, 0.8))
        target_loc = gun_pivot.matrix_world @ mathutils.Vector((0, -0.1, 0))
        active_prop.location = start_loc.lerp(target_loc, f)
        active_prop.rotation_euler[0] = PROP_STAND + (f * (PROP_LOAD - PROP_STAND)) + (f * gun_pitch)
        active_prop.rotation_euler[2] = (f * gun_yaw)
        mekhases.location.x, mekhases.location.y = active_prop.location.x + 0.4, active_prop.location.y - 0.4
    elif t >= 0.85 and t < 0.95:
        active_shell.location.z = -5
        f = (t - 0.85) / 0.1
        local_slide = mathutils.Vector((0, -0.1 + (f * 1.0), 0))
        active_prop.location = gun_pivot.matrix_world @ local_slide
        active_prop.rotation_euler[0] = PROP_LOAD + gun_pitch; active_prop.rotation_euler[2] = gun_yaw
        mekhases.location.x, mekhases.location.y = active_prop.location.x + 0.4, active_prop.location.y - 0.6
    elif t >= 0.95:
        active_shell.location.z = active_prop.location.z = -5
        f = (t - 0.95) / 0.05
        mekhases.location.x, mekhases.location.y, mekhases.rotation_euler[2] = 0.4 + (mekhases_home[0]-0.4)*f, 1.5 + (mekhases_home[1]-1.5)*f, 3.14

    if args.demo:
        for o in [active_shell, active_prop, loader, mekhases]:
            if o: o.keyframe_insert("location", frame=frame); o.keyframe_insert("rotation_euler", frame=frame)

# --- 8. AUTO-LABELING MATH FOR YOLO ---
from bpy_extras.object_utils import world_to_camera_view
def clamp(x, minimum, maximum): return max(minimum, min(x, maximum))

def get_2d_bounding_box(scene, cam_ob, mesh_ob):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh_eval = mesh_ob.evaluated_get(depsgraph)
    me = mesh_eval.to_mesh()
    mat = mesh_eval.matrix_world
    lx, ly = [], []

    for v in me.vertices:
        co_world = mat @ v.co
        co_ndc = world_to_camera_view(scene, cam_ob, co_world)
        if co_ndc.z > 0.0:
            lx.append(co_ndc.x); ly.append(co_ndc.y)

    mesh_eval.to_mesh_clear()
    if not lx or not ly: return None
    min_x, max_x = clamp(min(lx), 0.0, 1.0), clamp(max(lx), 0.0, 1.0)
    min_y, max_y = clamp(min(ly), 0.0, 1.0), clamp(max(ly), 0.0, 1.0)

    if min_x == max_x or min_y == max_y: return None
    width, height = max_x - min_x, max_y - min_y
    return (min_x + (width / 2.0), 1.0 - (min_y + (height / 2.0)), width, height)

def export_yolo_labels(filepath, scene, cam):
    labels = []
    for obj in scene.objects:
        if "yolo_class" in obj and obj.location.z > -4.0:
            bbox = get_2d_bounding_box(scene, cam, obj)
            if bbox: labels.append(f"{obj['yolo_class']} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}")
    if labels:
        with open(filepath, 'w') as f: f.write('\n'.join(labels))

# --- RUN EXECUTION ---
total_f = 250
scene = bpy.context.scene

if args.demo:
    scene.frame_end = total_f
    for f in range(1, total_f + 1): update_scene(f / total_f, f)
    scene.frame_set(1)
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D': s.shading.type = 'MATERIAL'
else:
    rgb_dir = os.path.join(base_dir, "training_data", "images", "train")
    label_dir = os.path.join(base_dir, "training_data", "labels", "train")
    os.makedirs(rgb_dir, exist_ok=True); os.makedirs(label_dir, exist_ok=True)

    # Save Scene Metadata
    metadata = {
        "run_id": args.run_id,
        "ammo_type": selected_ammo,
        "gun_pitch_rad": gun_pitch,
        "gun_yaw_rad": gun_yaw,
        "bot_color_rgb": bot_color
    }
    with open(os.path.join(label_dir, f"run_{args.run_id:03d}_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    for frame_idx in range(args.frames):
        progress = frame_idx / float(args.frames - 1)
        pseudo_frame = int(progress * total_f)
        update_scene(progress, pseudo_frame)

        # CRITICAL: Force Blender to update geometry positions before capturing bounding box
        bpy.context.view_layer.update()

        output_name = f"run_{args.run_id:03d}_{selected_ammo}_f{frame_idx:04d}"
        scene.render.filepath = os.path.join(rgb_dir, output_name + ".png")
        bpy.ops.render.render(write_still=True)
        export_yolo_labels(os.path.join(label_dir, output_name + ".txt"), scene, scene.camera)