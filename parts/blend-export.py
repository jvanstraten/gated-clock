import bpy
import math
import struct

def read_lines(ob, f):
    assert round(ob.location[0], 3) == 0 and round(ob.location[1], 3) == 0 and round(ob.location[2], 3) == 0
    assert round(ob.rotation_euler[0], 3) == 0 and round(ob.rotation_euler[1], 3) == 0 and round(ob.rotation_euler[2], 3) == 0
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
    print(' with {} line segment(s)'.format(n))

def read_label(ob, f):
    assert ob.location[2] == 0
    f.write('label {} {} {} {} {}\n'.format(ob.data.body.replace(' ', '~'), ob.location[0], ob.location[1], ob.rotation_euler[2], ob.scale[0]))
    print(' {}'.format(ob.data.body))

with open('.'.join(bpy.data.filepath.split('.')[:-1]) + '.txt', 'w') as f:
    for ob in bpy.data.objects:
        print('parsing object {}: '.format(ob.name), end='')
        if ob.type == 'MESH':
            print('line object', end='')
            read_lines(ob, f)
            continue
        elif ob.type == 'FONT':
            print('label', end='')
            read_label(ob, f)
            continue
        else:
            print('UNKNOWN, treating as comment')

print('DONE')
