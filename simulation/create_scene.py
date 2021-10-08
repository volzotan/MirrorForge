import bpy
from bpy_extras import image_utils

import argparse
import sys
import os
import json
import math


# Octree depth of blenders remesh modifier
# Higher depth = longer processing time
CONFIG_REMESH_OCTREE_DEPTH  = 8

# Put blender in render mode when started
CONFIG_RENDER_PREVIEW       = False

USE_REMESH_MODIFIER         = False
USE_SMOOTH_SHADING          = False

UNITS                       = "METRIC"
# UNITS                       = "IMPERIAL"

SAVE_FILE                   = False

# ----------------------------------------------------------------------------------------------------

# src: https://blender.stackexchange.com/a/134596/118415
class ArgumentParserForBlender(argparse.ArgumentParser):

    def _get_argv_after_doubledash(self):
        try:
            idx = sys.argv.index("--")
            return sys.argv[idx+1:] # the list after '--'
        except ValueError as e: # '--' not in the list:
            return []

    # overrides superclass
    def parse_args(self):
        return super().parse_args(args=self._get_argv_after_doubledash())


def showMessageBox(message, title="Message Box", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def importStl(filename):

    # scaling: 
    # STL input is in default fusion unit: cm
    # blender interprets this as cm->m: *10
    # scene should be rendered in cm->m->mm: *10 *0.1 *0.01
        
    bpy.ops.import_mesh.stl(files=[{"name":filename}], global_scale=0.001)

    object_names = []
    sel = bpy.context.selected_objects
    for obj in sel:
        object_names.append(obj.name)

    if not len(object_names) == 1:
        raise Exception("unexpected object names during import: {}".format(object_names))
    name = object_names[0]

    print("imported: {}".format(name))

    return bpy.data.objects[name]


# src: http://forums.luxcorerender.org/viewtopic.php?t=2183
def assignMaterial(obj):

    mat = bpy.data.materials.new(name="Material")
    tree_name = "Nodes_" + mat.name
    node_tree = bpy.data.node_groups.new(name=tree_name, type="luxcore_material_nodes")
    mat.luxcore.node_tree = node_tree

    # User counting does not work reliably with Python PointerProperty.
    # Sometimes, the material this tree is linked to is not counted as user.
    node_tree.use_fake_user = True

    nodes = node_tree.nodes

    output = nodes.new("LuxCoreNodeMatOutput")
    output.location = 300, 200
    output.select = False

    matmirror = nodes.new("LuxCoreNodeMatMirror")
    matmirror.location = 50, 200

    node_tree.links.new(matmirror.outputs[0], output.inputs[0])

    if obj.material_slots:
        obj.material_slots[obj.active_material_index].material = mat
    else:
        obj.data.materials.append(mat)

    # For viewport render, we have to update the luxcore object
    # because the newly created material is not yet assigned there
    obj.update_tag()


# blender unit conversion 
# from Fusion360 cm to blender m
def convert_unit(val):
    return val * 0.01


def orientation_to_rot(origin, direction):
    vec = [0, 0, 0]
        
    for i in range(0, 3):
        vec[i] = origin[i] - direction[i]
    x, y, z = vec

    # l = math.sqrt( x**2 + y**2 + z**2 )
    # x = x/l
    # y = y/l
    # z = z/l

    return (
        math.atan2(z, math.sqrt(x**2 + y**2)) + math.pi/2,
        0,
        math.atan2(x, y) * -1,
    )



# ----------------------------------------------------------------------------------------------------

parser = ArgumentParserForBlender()

parser.add_argument("-i", "--input",
                    type=str,
                    default="example.json",
                    help="JSON scene description file (output of mirrorforge Fusion360 plugin)")

args = parser.parse_args()

# ----------------------------------------------------------------------------------------------------

# preflight checks

passed_checks = True

if "BlendLuxCore" not in bpy.context.preferences.addons:
# if True:
    showMessageBox("BlendLuxCore plugin not found. Please install the plugin and reload. See luxcorerender.org/download/")
    passed_checks = False

if passed_checks:

    # General scene settings

    bpy.context.scene.render.engine             = "LUXCORE"
    bpy.context.scene.unit_settings.system      = UNITS
    bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"
    bpy.context.scene.luxcore.config.engine     = "BIDIR"

    # put blender in render preview mode

    if CONFIG_RENDER_PREVIEW:
        for area in bpy.context.workspace.screens[0].areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'

    # parse JSON

    basepath = os.path.dirname(args.input)

    data = None
    with open(args.input) as json_file:
        data = json.load(json_file)

    # remove default scene objects
 
        # bpy.ops.object.select_all(action='DESELECT')
        for o in bpy.context.scene.objects:
            o.select_set(True)
        bpy.ops.object.delete() 

    # import STLs

    for body in data["bodies"]:
        filename = os.path.join(basepath, body)
        print("import: {}".format(filename))

        if not os.path.exists(filename):
            print("import failed! file missing.")
        else:
            _ = importStl(filename)

    # create mirrors

    if "mirrors" in data:
        for body in data["mirrors"]:
            filename = os.path.join(basepath, body)
            obj = importStl(filename)

            # remesh modifier: 
            # add a modifier to the object without applying it
            # will remesh the mirror to improve reflection quality
            # requires an octree depth of at least 8 for reliable results
            if USE_REMESH_MODIFIER:
                bpy.ops.object.modifier_add(type="REMESH")
                obj.modifiers["Remesh"].mode = "SMOOTH"
                obj.modifiers["Remesh"].octree_depth = CONFIG_REMESH_OCTREE_DEPTH
                obj.modifiers["Remesh"].scale = 0.99

            # smooth shading:
            # surface smoothing prior to raytracing
            if USE_SMOOTH_SHADING:
                mesh = obj.data
                for f in mesh.polygons:
                    f.use_smooth = True

            assignMaterial(obj)

    # create cameras

    if "cameras" in data:
        for camera_info in data["cameras"]:

            valid = True

            fields = ["origin", "direction", "fov"]
            for field in fields:
                if field not in camera_info:
                    print("field {} missing in camera info. Not creating camera.".format(field))
                    valid = False
                    break

            if not valid:
                continue

            camera_data = bpy.data.cameras.new(name='Camera')
            camera_object = bpy.data.objects.new('Camera', camera_data)     
            bpy.context.scene.collection.objects.link(camera_object)

            rotX, rotY, rotZ = orientation_to_rot(camera_info["direction"], camera_info["origin"])
            
            print("camera rotation: X {:6.2f} / Y {:6.2f} / Z {:6.2f}".format(math.degrees(rotX), math.degrees(rotY), math.degrees(rotZ)))

            camera_object.rotation_euler = (rotX, rotY, rotZ)
            camera_object.location = [convert_unit(c) for c in camera_info["origin"]]
            camera_object.scale = (.01, .01, .01)

            camera_object.data.clip_start = 0.01 # TODO: does it work?

            # print(camera_object.data)
            # print(dir(camera_object.data))

            # for key in dir(camera_object.data):
            #     print("{} -- {}".format(key, getattr(camera_object.data, key)))

            # exit()

            camera_object.data.lens_unit = "MILLIMETERS"
            camera_object.data.lens = camera_info["fov"] 
            # TODO: set mode to FOV instead of focal length

            # TODO: create camera in correct collection

            # TODO: add light to scene

    # create projectors

    projectors = []
    if "projectors" in data:
        for projector_info in data["projectors"]:

            valid = True

            fields = ["origin", "direction", "fov", "image"]
            for field in fields:
                if field not in projector_info:
                    print("field {} missing in projector info. Not creating projector.".format(field))
                    valid = False
                    break

            if projector_info["image"] is None or len(projector_info["image"]) == 0:
                print("no projector image specified, creating projector without image.")
            elif not os.path.isfile(projector_info["image"]):
                print("could not find projector image \"{}\". Creating projector without image.".format(projector_info["image"]))
                # valid = False

            if not valid:
                continue

            light_data = bpy.data.lights.new(name="projector", type="SPOT")
            light_data.energy = 1000
            light_data.show_cone = True
            light_data.spot_blend = 0

            # field of view: angle of the spotlight beam, float in [0.0174533, 3.14159]
            light_data.spot_size = projector_info["fov"]

            light_object = bpy.data.objects.new(name="projector", object_data=light_data)
            bpy.context.collection.objects.link(light_object)
            bpy.context.view_layer.objects.active = light_object

            rotX, rotY, rotZ = orientation_to_rot(projector_info["direction"], projector_info["origin"])

            print("projector rotation: X {:6.2f} / Y {:6.2f} / Z {:6.2f}".format(math.degrees(rotX), math.degrees(rotY), math.degrees(rotZ)))

            light_object.rotation_euler = (rotX, rotY, rotZ)
            light_object.location = [convert_unit(c) for c in projector_info["origin"]]

            img = image_utils.load_image(projector_info["image"])
            bpy.data.lights.get("projector").luxcore.image = img

            dg = bpy.context.evaluated_depsgraph_get() 
            dg.update()

    # if there is no projector, add some global lights for the camera
    if len(projectors) == 0:

        light_data = bpy.data.lights.new(name="light", type="AREA")     
        light_data.energy = 1000

        light_object = bpy.data.objects.new(name="light", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object

        light_object.location = [0, 0, 1]

    # create planes

    bpy.ops.mesh.primitive_plane_add(location=(0, 0, -.001))
    plane = bpy.context.active_object
    plane.scale = (1, 1, .01)

    # save file

    if SAVE_FILE:
        bpy.ops.wm.save_as_mainfile(filepath="output.blend")