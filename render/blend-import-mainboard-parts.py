import bpy
import math

instances = {}

with open('../output/mainboard.parts.txt', 'r') as f:
    for line in f.read().split('\n'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        _, model, layer, x, y, rot = line.split()
        if model == '*':
            continue
        if layer == 'Ctop':
            layer = True
        elif layer == 'Cbottom':
            layer = False
        else:
            print(layer)
            assert False
        if model not in instances:
            instances[model] = []
        instances[model].append((layer, float(x), float(y), float(rot)))

bpy.ops.wm.open_mainfile(filepath='parts.template.blend')

for name, insts in instances.items():

    with bpy.data.libraries.load('../models/{0}/{0}.blend'.format(name), link=True) as (data_from, data_to):
        data_to.collections = data_from.collections

    assert len(data_to.collections) == 1
    src = data_to.collections[0]

    print('{} instances of {}...'.format(len(insts), name))

    for idx, (layer, x, y, rot) in enumerate(insts):
        instance = bpy.data.objects.new('{}.{:03d}'.format(src.name, idx), None)
        instance.instance_type = 'COLLECTION'
        instance.instance_collection = src
        instance.location[0] = x
        instance.location[1] = y
        instance.location[2] = 1.6 if layer else 0
        instance.rotation_euler[0] = 0 if layer else math.pi
        instance.rotation_euler[2] = rot / 180 * math.pi
        if not layer:
            instance.rotation_euler[2] += math.pi
        bpy.data.collections[0].objects.link(instance)


bpy.ops.wm.save_as_mainfile(filepath='../output/mainboard.Parts.blend')
