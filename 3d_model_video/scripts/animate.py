import bpy

scene = bpy.context.scene
scene.frame_set(1)  # only first frame

rig = bpy.data.objects["RIG-rain"]

# ---------------------------
# SMILE (keep only this)
# ---------------------------
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        keys = obj.data.shape_keys.key_blocks

        for key in keys:
            if "smile" in key.name.lower():
                key.value = 0.6


# ---------------------------
# LIGHTING (ADD THIS)
# ---------------------------

# remove old lights
for obj in list(bpy.data.objects):
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)

# main front light
key_data = bpy.data.lights.new(name="KeyLight", type='AREA')
key_light = bpy.data.objects.new(name="KeyLight", object_data=key_data)
bpy.context.collection.objects.link(key_light)

key_light.location = (1.5, -2.2, 2.2)
key_light.data.energy = 400
key_light.data.size = 4

# soft fill light
fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
fill_light = bpy.data.objects.new(name="FillLight", object_data=fill_data)
bpy.context.collection.objects.link(fill_light)

fill_light.location = (-1.5, -2.2, 1.5)
fill_light.data.energy = 120
fill_light.data.size = 4

# world brightness
world = bpy.data.worlds["World"]
world.use_nodes = True

bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.05, 0.05, 0.05, 1)  
bg.inputs[1].default_value = 0.8

# ---------------------------
# CAMERA (same as before)
# ---------------------------
if "Camera" in bpy.data.objects:
    cam = bpy.data.objects["Camera"]
else:
    cam_data = bpy.data.cameras.new(name="Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)

cam.location = (-0.3, -2.4, 1.7)

target = bpy.data.objects["RIG-rain"]
head_pos = target.location.copy()
head_pos.z += 1.5

direction = head_pos - cam.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()

bpy.context.scene.camera = cam


# ---------------------------
# OUTPUT (SINGLE IMAGE)
# ---------------------------
# scene.render.filepath = "/Users/dheerajgautam/3d_model_video/output/preview"
scene.render.filepath = "/Users/dheerajgautam/Documents/ai_studio/3d_model_video/output/preview"

scene.render.image_settings.file_format = 'PNG'


# ---------------------------
# RENDER ONE IMAGE
# ---------------------------
bpy.ops.render.render(write_still=True)