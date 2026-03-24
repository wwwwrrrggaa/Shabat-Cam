import bpy
import bmesh
import sys
import os
import argparse
import math
import random

# --- 1. PARSE ARGUMENTS ---
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

parser = argparse.ArgumentParser()
parser.add_argument("--render", action="store_true")
parser.add_argument("--demo", action="store_true")
parser.add_argument("--progress", type=float, default=0.0)
parser.add_argument("--output", type=str, default="test_render")
# New argument to randomize ammo type per run
parser.add_argument("--ammo_type", type=str, default="M795")
args, unknown = parser.parse_known_args(argv)

# --- 2. CLEAN ENVIRONMENT ---
for obj in bpy.data.objects:
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in bpy.data.meshes:
    bpy.data.meshes.remove(mesh, do_unlink=True)
for ng in bpy.data.node_groups:
    bpy.data.node_groups.remove(ng)

base_dir = os.path.dirname(os.path.abspath(__file__))

# --- 3. MATERIALS ---
def create_material(name, color, emission=0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        if emission > 0:
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = emission
    mat.diffuse_color = color
    return mat

materials = {
    "M795": create_material("M795_Olive", (0.2, 0.3, 0.1, 1)),
    "M825": create_material("M825_Seafoam", (0.4, 0.7, 0.5, 1)),
    "M107": create_material("M107_Olive", (0.15, 0.25, 0.1, 1)),
    "WhiteBag": create_material("White_Cloth", (0.8, 0.8, 0.8, 1)),
    "RedBag": create_material("Red_Cloth", (0.8, 0.1, 0.1, 1)),
    "BotGreen": create_material("Bot_Green", (0.05, 0.2, 0.05, 1)),
    "BlackHelmet": create_material("Helmet_Black", (0.02, 0.02, 0.02, 1)),
    "Visor": create_material("Visor_Glow", (0, 0.8, 1, 1), emission=10.0),
    "BlackMetal": create_material("Black_Metal", (0.01, 0.01, 0.01, 1)),
    "WhiteRoom": create_material("Tan_Interior", (0.5, 0.45, 0.35, 1))
}

def spawn_robot_crew(name, location):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.2, location=(0,0,0.6))
    body = bpy.context.view_layer.objects.active
    body.data.materials.append(materials["BotGreen"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0,0,1.2))
    head = bpy.context.view_layer.objects.active
    head.data.materials.append(materials["BotGreen"])
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0.25, 1.25))
    visor = bpy.context.view_layer.objects.active
    visor.scale = (4.0, 0.5, 1.2); visor.data.materials.append(materials["Visor"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.33, location=(0,0,1.22))
    helmet = bpy.context.view_layer.objects.active
    helmet.scale[2] = 0.85; helmet.data.materials.append(materials["BlackHelmet"])
    bpy.ops.object.select_all(action='DESELECT')
    for p in [body, head, visor, helmet]: p.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    bot = bpy.context.view_layer.objects.active
    bot.name = name
    bpy.context.scene.cursor.location = (0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='BOUNDS')
    bot.location = location
    return bot

# --- 4. ENVIRONMENT ---
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes.get("Background")
if bg: bg.inputs[0].default_value = (0, 0, 0, 1)

room = bpy.ops.mesh.primitive_cube_add(size=5, location=(0, 0, 1.75))
room_obj = bpy.context.view_layer.objects.active
room_obj.scale[2] = 3.5 / 5.0
room_obj.data.materials.append(materials["WhiteRoom"])
bm = bmesh.new(); bm.from_mesh(room_obj.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(room_obj.data); bm.free()

tray = bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 1.8, 1.25))
tray_obj = bpy.context.view_layer.objects.active
tray_obj.scale = (0.2, 0.4, 0.05); tray_obj.data.materials.append(materials["BlackMetal"])

bpy.ops.object.light_add(type='SPOT', location=(0, 0.0, 3.4))
spot = bpy.context.view_layer.objects.active
spot.data.energy = 3000

# --- CAMERA/LIDAR POSITION (Directly Above Turret) ---
bpy.ops.object.camera_add(location=(0, 0, 3.4), rotation=(0, 0, 0))
cam = bpy.context.view_layer.objects.active
cam.data.lens = 15 # Ultra-Wide God's Eye View
bpy.context.scene.camera = cam

# --- 5. CREW ---
gunner = spawn_robot_crew("Bot_Gunner", (-1.8, 1.0, 0))
loader = spawn_robot_crew("Bot_Loader", (-0.8, -1.8, 0))
mekhases = spawn_robot_crew("Bot_Mekhases", (1.5, 0.5, 0))

# --- 6. RANDOMIZED AMMO ---
def spawn_ammo(name, a_type):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.6)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.data.materials.append(materials.get(a_type, materials["M795"]))
    return obj

# Pick ammo for this run
shell = spawn_ammo("Shell", args.ammo_type)
bag_type = "RedBag" if args.ammo_type == "M825" else "WhiteBag"
propellant = spawn_ammo("Propellant", bag_type)

# --- 7. ANIMATION ---
def update_scene(t, frame):
    STANDING, FLAT = 1.5708, 0.0
    shell.location, shell.rotation_euler[0] = (-1.2, -2.0, 0.4), STANDING
    propellant.location, propellant.rotation_euler[0] = (1.5, 0.5, 0.3), FLAT
    loader.location, mekhases.location = (-0.8, -1.8, 0), (1.5, 0.5, 0)

    if t < 0.35: # Shell Transport
        f = t / 0.35
        shell.location = (-1.2 + 1.2*f, -2.0 + 3.4*f, 0.7)
        loader.location.x, loader.location.y = shell.location.x - 0.4, shell.location.y - 0.4
    elif t < 0.45: # Shell Tilt/Load
        f = (t-0.35)/0.1
        shell.location = (0, 1.4 + 0.6*f, 0.7 + 0.55*f)
        shell.rotation_euler[0] = STANDING - (f * STANDING)
    elif t > 0.6 and t < 0.9: # Bag Load
        shell.location.z = -5
        f = (t-0.6)/0.3
        propellant.location = (1.5 - 1.5*f, 0.5 + 1.3*f, 0.7 + 0.55*f)
        propellant.rotation_euler[0] = FLAT + (f * STANDING)
        mekhases.location.x, mekhases.location.y = propellant.location.x + 0.4, propellant.location.y - 0.4
    elif t >= 0.9:
        shell.location.z = propellant.location.z = -5

    if args.demo:
        for o in [shell, propellant, loader, mekhases]:
            o.keyframe_insert("location", frame=frame); o.keyframe_insert("rotation_euler", frame=frame)

total_f = 250
if args.demo:
    bpy.context.scene.frame_end = total_f
    for f in range(1, total_f + 1): update_scene(f/total_f, f)
else:
    update_scene(args.progress, 1)

# --- 8. COMPOSITOR ---
scene = bpy.context.scene
bpy.context.view_layer.use_pass_z = True
group = bpy.data.node_groups.new(name="Comp", type="CompositorNodeTree")
scene.compositing_node_group = group
rlayers = group.nodes.new('CompositorNodeRLayers')
output = group.nodes.new('CompositorNodeOutputFile')
output.format.file_format = 'OPEN_EXR_MULTILAYER'
output.directory = os.path.join(base_dir, "training_data", "depth")
os.makedirs(output.directory, exist_ok=True)
output.file_output_items.new('RGBA', args.output + "_")
z_sock = next((s for s in rlayers.outputs if s.name in ["Depth", "Z"]), None)
if z_sock: group.links.new(z_sock, output.inputs[0])

if args.render:
    rgb_dir = os.path.join(base_dir, "training_data", "rgb")
    os.makedirs(rgb_dir, exist_ok=True)
    scene.render.filepath = os.path.join(rgb_dir, args.output + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.quit_blender()