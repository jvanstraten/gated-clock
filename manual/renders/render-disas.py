import bpy
import sys
fname = sys.argv[-1]
assert fname.startswith('disassembly')
assert fname.endswith('.jpg')
index = int(fname[11:-4])
bpy.context.window.scene = bpy.data.scenes['Disassembly {}'.format(index)]
bpy.context.scene.render.filepath = fname
bpy.ops.render.render(write_still=True)
