3D models for parts
===================

This folder contains 3D models for all the parts.

`template.blend` may be used as a template for them; it doesn't have the usual
light and camera and stuff and has the coordinate system scaling properly set
up. `materials.blend` is used as a library for all the materials that the parts
use, so they can be tweaked easily; thus, all part blend files link to this
file. Other than that, however, there's nothing special about these blend
files; their main collection is simply instanced whenever a part is used
somewhere.
