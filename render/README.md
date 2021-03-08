Renderings and mechanical integration
=====================================

The stuff in this folder is used to get a "3D CAD" overview of the entire
assembly, and of course to make nice renders of it. The file you're looking for
is `top.blend`, but make sure to run the makefile in the root first, or you'll
get errors about missing links.

The various Python scripts and template files are used to build blend files for
the PCBs, acrylic plates, and their part instances. This is all managed by the
makefile in the root directory. All output products land in the `output`
directory.
