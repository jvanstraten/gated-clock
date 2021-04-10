import bpy
import os

print('Adjusting front sheet thickness...')
bpy.data.objects['FrontThickness'].location.z = -float(os.environ['FRONT_THICKNESS'])

print('Adjusting display sheet thickness...')
bpy.data.objects['DisplayThickness'].location.z = -float(os.environ['DISPLAY_THICKNESS'])

print('Adjusting highlight sheet thickness...')
bpy.data.objects['HighlightThickness'].location.z = -float(os.environ['HIGHLIGHT_THICKNESS'])

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
    bpy.ops.export_mesh.stl(
        filepath='stl/{}/{}.stl'.format(color, name),
        check_existing=False,
        use_selection=True
    )
    ob.select_set(False)
