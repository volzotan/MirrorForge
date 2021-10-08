#!/bin/sh

# OSX users:
# If you need to see output of python scripts executed by blender you
# need to run the blender app package from the command line:

# Blender will ignore all parameters after '-- ' (hyphen hyphen space)
# these are then available to python scripts via argv

# /Applications/Blender.app/Contents/MacOS/Blender --background --python create_scene.py -- -i example.json
# /Applications/Blender.app/Contents/MacOS/Blender --python stub_script.py

# /Applications/Blender.app/Contents/MacOS/Blender --python create_scene.py -- -i ../applicationexamples/camera/wedge.json
/Applications/Blender.app/Contents/MacOS/Blender --python create_scene.py -- -i ../applicationexamples/projector/halopro.json