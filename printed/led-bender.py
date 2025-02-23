import bpy

for ob in bpy.data.objects:
    ob.select_set(False)

for ob in bpy.data.objects:
    if ob.name.startswith('PrintedBlack-'):
        color = 'black'
    elif ob.name.startswith('PrintedWhite-'):
        color = 'white'
    elif ob.name.startswith('Printed-'):
        color = 'any'
    else:
        continue
    name = ob.name.split('-', maxsplit=1)[1]

    print('Exporting {}...'.format(name))
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    try:
        # old API
        bpy.ops.export_mesh.stl(
            filepath='stl/{}/{}.stl'.format(color, name),
            check_existing=False,
            use_selection=True
        )
    except AttributeError:
        # new API
        bpy.ops.wm.stl_export(
            filepath='stl/{}/{}.stl'.format(color, name),
            check_existing=False,
            export_selected_objects=True
        )
    ob.select_set(False)
