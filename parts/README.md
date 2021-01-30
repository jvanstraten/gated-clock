Part database
=============

Database with metadata for all the parts needed to build the clock. All parts
have a `<name>.meta.txt` file with some ordering information in them. For most
of the parts this is the only thing, but some parts, like the PCBs and the
lasercut acrylic sheets need manufacturing files as well. These also live here.
Note that some (notably the PCBs) are generated.

Most parts also have a 3D model. These models live in the `models` directory
however, as some parts (like different-valued resistors) reuse the same model.
They are linked via the `model` key in `.meta.txt`.
