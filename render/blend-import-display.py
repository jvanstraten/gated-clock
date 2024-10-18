import bpy

bpy.ops.wm.open_mainfile(filepath='acrylic.template.blend')

bpy.data.objects.remove(bpy.data.objects['Acrylic'])
bpy.data.objects.remove(bpy.data.objects['Surface'])

bpy.ops.wm.obj_import(
    filepath='../output/mainboard.Display.obj',
    use_split_groups=True,
    forward_axis='Y', up_axis='Z'
)

for obj in bpy.data.objects:
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()

    for slot in obj.material_slots:
        if slot.material.name_full.startswith('substrate'):
            slot.material = bpy.data.materials.get('Display')
        else:
            print(slot.material.name_full)
            assert False

bpy.data.collections['Collection'].name = 'Display'

bpy.ops.wm.save_as_mainfile(filepath='../output/mainboard.Display.blend')
