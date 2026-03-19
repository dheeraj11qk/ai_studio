import bpy

print("\n=== OBJECTS IN SCENE ===")
for obj in bpy.data.objects:
    print(f"  [{obj.type}] {obj.name}")

print("\n=== ARMATURES / BONES ===")
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        print(f"\n  Armature: {obj.name}")
        for bone in obj.pose.bones:
            print(f"    bone: {bone.name}")

print("\n=== SHAPE KEYS ===")
for obj in bpy.data.objects:
    if obj.type == 'MESH' and obj.data.shape_keys:
        print(f"\n  Mesh: {obj.name}")
        for key in obj.data.shape_keys.key_blocks:
            print(f"    key: {key.name}")
