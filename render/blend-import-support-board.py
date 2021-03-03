import bpy

bpy.ops.wm.open_mainfile(filepath='support_board.template.blend')

bpy.data.objects.remove(bpy.data.objects['PCB'])
bpy.data.objects.remove(bpy.data.objects['Surface'])
bpy.data.objects.remove(bpy.data.objects['Light'])

bpy.ops.import_scene.obj(
    filepath='../output/support_board.PCB.obj',
    use_split_groups=True,
    use_image_search=False,
    axis_forward='Y', axis_up='Z'
)

for obj in bpy.data.objects:

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()

    for slot in obj.material_slots:
        if slot.material.name_full.startswith('silkscreen'):
            slot.material = bpy.data.materials.get('Silkscreen')
        elif slot.material.name_full.startswith('substrate'):
            slot.material = bpy.data.materials.get('Substrate')
        elif slot.material.name_full.startswith('copper'):
            slot.material = bpy.data.materials.get('Copper')
        elif slot.material.name_full.startswith('soldermask'):
            slot.material = bpy.data.materials.get('Mask')
        else:
            print(slot.material.name_full)
            assert False

bpy.data.collections['Collection'].name = 'Mainboard'

bpy.ops.wm.save_as_mainfile(filepath='../output/support_board.PCB.blend')
