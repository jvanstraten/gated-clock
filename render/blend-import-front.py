import bpy

bpy.ops.wm.open_mainfile(filepath='acrylic.template.blend')

bpy.data.objects.remove(bpy.data.objects['Acrylic'])
bpy.data.objects.remove(bpy.data.objects['Surface'])

bpy.ops.import_scene.obj(
    filepath='../output/mainboard.Front.obj',
    use_split_groups=True,
    use_image_search=False,
    axis_forward='Y', axis_up='Z'
)

for obj in bpy.data.objects:
    if obj.name.endswith('GBS'):
        bpy.data.objects.remove(obj)
        continue

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()

    for slot in obj.material_slots:
        if slot.material.name_full.startswith('silkscreen'):
            slot.material = bpy.data.materials.get('FrontEngraving')
        elif slot.material.name_full.startswith('substrate'):
            slot.material = bpy.data.materials.get('Front')
        else:
            print(slot.material.name_full)
            assert False

bpy.data.collections['Collection'].name = 'Front'

bpy.ops.wm.save_as_mainfile(filepath='../output/mainboard.Front.blend')

