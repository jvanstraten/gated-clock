import bpy
import math
import struct

def read_lines(layer, ob, f, thickness):
    assert round(ob.location[0], 3) == 0 and round(ob.location[1], 3) == 0 and round(ob.location[2], 3) == 0
    assert round(ob.rotation_euler[0], 3) == 0 and round(ob.rotation_euler[1], 3) == 0 and round(ob.rotation_euler[2], 3) == 0
    f.write('layer {}\nmode C{}\n'.format(layer, thickness))
    d = ob.data
    n = 0
    verts = set()
    for e in d.edges:
        c1 = d.vertices[e.vertices[0]].co
        c2 = d.vertices[e.vertices[1]].co
        if c1[2] != 0.0 or c2[2] != 0.0:
            continue
        f.write('line {} {} {} {}\n'.format(c1[0], c1[1], c2[0], c2[1]))
        verts.add(e.vertices[0])
        verts.add(e.vertices[1])
        n += 1
    print(' with {} line segment(s)'.format(n), end='')
    n = 0
    for i, v in enumerate(d.vertices):
        c = v.co
        if i in verts or c[2] != 0:
            continue
        f.write('vert {} {}\n'.format(c[0], c[1]))
        n += 1
    print(' and {} flash(es)'.format(n))

def read_regions(layer, ob, f):
    assert round(ob.location[0], 3) == 0 and round(ob.location[1], 3) == 0 and round(ob.location[2], 3) == 0
    assert round(ob.rotation_euler[0], 3) == 0 and round(ob.rotation_euler[1], 3) == 0 and round(ob.rotation_euler[2], 3) == 0
    n = 0
    for p in ob.data.polygons:
        f.write('layer {}\nmode region\n'.format(layer))
        for v in p.vertices:
            c = ob.data.vertices[v].co
            assert c[2] == 0.0
            f.write('vert {} {}\n'.format(c[0], c[1]))
            n += 1
    print(' with {} vertex/vertices'.format(n))

def read_label(layer, ob, f):
    assert ob.location[2] == 0
    f.write('layer {}\nlabel {} {} {} {}\n'.format(layer, ob.data.body, ob.location[0], ob.location[1], ob.rotation_euler[2]))
    print(' {}'.format(ob.data.body))

def read_via(ob, f):
    assert ob.location[2] == 0
    ds = []
    for p in ob.data.polygons:
        da = 0
        dn = 0
        for v in p.vertices:
            c = ob.data.vertices[v].co
            assert c[2] == 0.0
            da += math.sqrt(c[0]**2 + c[1]**2) * 2
            dn += 1
        ds.append(da / dn)
    ds.sort()
    if len(ds) == 1:
        print(', non-plated {:.2f}'.format(ds[0]))
        f.write('hole {} {} {}\n'.format(ob.location[0], ob.location[1], ds[0]))
    elif len(ds) == 2:
        print(', plated {:.2f}x{:.2f}'.format(ds[1], ds[0]))
        f.write('via {} {} {} {}\n'.format(ob.location[0], ob.location[1], ds[0], ds[1]))
    else:
        assert False

known_layers = {'Ctop', 'GTO', 'GTS', 'GTL', 'G1', 'G2', 'GBL', 'GBS', 'GBO', 'Cbottom', 'Mill', 'Drill'}

with open(bpy.data.filepath + '.txt', 'w') as f:
    for ob in bpy.data.objects:
        for c in ob.users_collection:
            print('parsing object {} on layer {}: '.format(ob.name, c.name), end='')
            if c.name in known_layers:
                if ob.type == 'MESH' and c.name not in ('Ctop', 'Cbottom'):
                    if c.name == 'Drill':
                        print('hole/via object', end='')
                        read_via(ob, f)
                        continue
                    elif 'Solidify' in ob.modifiers:
                        thickness = round(ob.modifiers['Solidify'].thickness, 2)
                        print('line object with thickness = {}'.format(thickness), end='')
                        read_lines(c.name, ob, f, thickness)
                        continue
                    elif c.name != 'Mill':
                        print('region object', end='')
                        read_regions(c.name, ob, f)
                        continue
                elif ob.type == 'FONT':
                    print('label', end='')
                    read_label(c.name, ob, f)
                    continue
            elif c.name.startswith('Acrylic.'):
                _, name, mode = c.name.split('.')
                assert mode in ('Cut', 'Engrave')
                if ob.type == 'MESH':
                    if 'Solidify' in ob.modifiers:
                        thickness = round(ob.modifiers['Solidify'].thickness, 2)
                        print('line object with thickness = {}'.format(thickness), end='')
                        read_lines(c.name, ob, f, thickness)
                        continue
                    elif mode != 'Cut':
                        print('region object', end='')
                        read_regions(c.name, ob, f)
                        continue
            print('UNKNOWN, treating as comment')

print('DONE')
