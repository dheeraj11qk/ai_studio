import bpy
import math
import os

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 5
scene.render.fps = 24

rig = bpy.data.objects.get("RIG-rain")
if rig is None:
    raise RuntimeError("RIG-rain not found")

# ---------------------------
# SMILE (Smile.L / Smile.R shape keys)
# ---------------------------
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        for key in obj.data.shape_keys.key_blocks:
            if key.name in ("Smile.L", "Smile.R"):
                key.value = 0.9
                key.keyframe_insert(data_path="value", frame=1)
                key.keyframe_insert(data_path="value", frame=5)

# ---------------------------
# HAND + HEAD BONES (correct names)
# ---------------------------
hand_l = rig.pose.bones.get("IK-Hand.L")
hand_r = rig.pose.bones.get("IK-Hand.R")
head   = rig.pose.bones.get("HNG-Head")

print(f"[DEBUG] hand_l={hand_l}, hand_r={hand_r}, head={head}")

# 5 very distinct poses
poses = [
    # frame, hl_x, hl_z, hr_x, hr_z, head_z, mouth
    (1,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0),   # neutral
    (2,  0.4,  0.3, -0.4,  0.3,  0.2,  0.8),   # both hands up, mouth open
    (3, -0.4, -0.2,  0.4, -0.2, -0.2,  0.0),   # hands down, mouth closed
    (4,  0.5,  0.5,  0.1,  0.1,  0.3,  1.0),   # left hand high wave
    (5,  0.0,  0.2,  0.0,  0.2,  0.0,  0.5),   # rest
]

for (frame, hl_x, hl_z, hr_x, hr_z, hd_z, mouth_v) in poses:
    scene.frame_set(frame)

    if hand_l:
        hand_l.location.x = hl_x
        hand_l.location.z = hl_z
        hand_l.keyframe_insert(data_path="location")

    if hand_r:
        hand_r.location.x = hr_x
        hand_r.location.z = hr_z
        hand_r.keyframe_insert(data_path="location")

    if head:
        head.rotation_euler[2] = hd_z
        head.keyframe_insert(data_path="rotation_euler")

    # mouth_open shape key
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            for key in obj.data.shape_keys.key_blocks:
                if key.name == "mouth_open":
                    key.value = mouth_v
                    key.keyframe_insert(data_path="value")

# ---------------------------
# LIGHTING
# ---------------------------
for obj in list(bpy.data.objects):
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)

key_light = bpy.data.lights.new(name="Key", type='AREA')
key_obj   = bpy.data.objects.new("Key", key_light)
bpy.context.collection.objects.link(key_obj)
key_obj.location  = (1.5, -2.2, 2.2)
key_light.energy  = 300
key_light.size    = 4

fill_light = bpy.data.lights.new(name="Fill", type='AREA')
fill_obj   = bpy.data.objects.new("Fill", fill_light)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location  = (-1.5, -2.2, 1.5)
fill_light.energy  = 100
fill_light.size    = 4

world = bpy.data.worlds["World"]
world.use_nodes = True
bg_node = world.node_tree.nodes["Background"]
bg_node.inputs[0].default_value = (0.05, 0.05, 0.05, 1)
bg_node.inputs[1].default_value = 0.5

# ---------------------------
# CAMERA (unchanged)
# ---------------------------
if "Camera" in bpy.data.objects:
    cam = bpy.data.objects["Camera"]
else:
    cam_data = bpy.data.cameras.new(name="Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)

cam.location = (-0.3, -2.4, 1.7)
target    = bpy.data.objects["RIG-rain"]
head_pos  = target.location.copy()
head_pos.z += 1.5
direction = head_pos - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# ---------------------------
# OUTPUT
# ---------------------------
out_dir = "/Users/dheerajgautam/Documents/ai_studio/3d_model_video/output"
os.makedirs(out_dir, exist_ok=True)
scene.render.filepath = f"{out_dir}/frame_"
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

bpy.ops.render.render(animation=True)
