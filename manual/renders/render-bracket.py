import bpy
bpy.context.scene.render.filepath = 'bracket.png'
bpy.ops.render.render(write_still=True)
