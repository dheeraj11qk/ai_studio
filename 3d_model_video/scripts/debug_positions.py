import bpy

rig = bpy.data.objects.get("RIG-rain")
if rig:
    for name in ["IK-Hand.L", "IK-Hand.R", "HNG-Head", "FK-Neck", "root", "Root"]:
        bone = rig.pose.bones.get(name)
        if bone:
            print(f"[POS] {name}: loc={bone.location}, head={bone.head}")

print("[POS] RIG-rain world location:", rig.location if rig else "NOT FOUND")
