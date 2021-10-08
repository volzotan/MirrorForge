import logging
import os
import json

import adsk.core
import traceback

from ..util import identifier
from ..util import functions

app = adsk.core.Application.get()
ui = app.userInterface

handlers = []
logger = logging.getLogger("exportHandler")

# TODO: change
DEFAULT_FILENAME = "/Users/volzotan/Documents/PRINTER/data.json"

class ExportCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):

    def __init__(self):
        super().__init__()

    def notify(self, args):

        try:

            logger.debug("exportHandler init")

            # document = app.activeDocument
            # if document.isSaved is not True:
            #     ui.messageBox('Please save your document before continuing.')

            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            cmd.setDialogInitialSize(1000, 1000)

            # Get the CommandInputs collection to create new command inputs.            
            inputs = cmd.commandInputs

            selectionBodyAll = inputs.addSelectionInput(
                identifier.WIDGET_ID_ALLBODIES, 
                'Components/Bodies for export', 
                'Tooltip')
            selectionBodyAll.addSelectionFilter(adsk.core.SelectionCommandInput.SolidBodies)
            selectionBodyAll.addSelectionFilter(adsk.core.SelectionCommandInput.RootComponents)
            selectionBodyAll.addSelectionFilter(adsk.core.SelectionCommandInput.Occurrences)
            selectionBodyAll.setSelectionLimits(0)

            selectionBodyMirror = inputs.addSelectionInput(
                identifier.WIDGET_ID_MIRRORS, 
                'Mirrors', 
                'Tooltip')
            selectionBodyMirror.addSelectionFilter(adsk.core.SelectionCommandInput.SolidBodies)
            selectionBodyMirror.addSelectionFilter(adsk.core.SelectionCommandInput.RootComponents)
            selectionBodyMirror.addSelectionFilter(adsk.core.SelectionCommandInput.Occurrences)
            selectionBodyMirror.setSelectionLimits(0)
            
            # --- cameras

            groupCameraInputCmd = inputs.addGroupCommandInput('groupCamera', 'Camera')
            groupCameraInputCmd.isExpanded = True
            groupCameraInputCmd.isEnabledCheckBoxDisplayed = True
            groupCameraInputs = groupCameraInputCmd.children

            selectionCameraOrigin = groupCameraInputs.addSelectionInput(
                identifier.WIDGET_ID_CAMERA_ORIGIN, 
                'Camera origin', 
                'Select a (sketch-)point for camera placement')
            selectionCameraOrigin.addSelectionFilter(adsk.core.SelectionCommandInput.SketchPoints)            
            selectionCameraOrigin.addSelectionFilter(adsk.core.SelectionCommandInput.Vertices)
            selectionCameraOrigin.setSelectionLimits(0)

            selectionCameraDirection = groupCameraInputs.addSelectionInput(
                identifier.WIDGET_ID_CAMERA_DIRECTION, 
                'Camera direction', 
                'Select a (sketch-)point to define the cameras direction')
            selectionCameraDirection.addSelectionFilter(adsk.core.SelectionCommandInput.SketchPoints)            
            selectionCameraDirection.addSelectionFilter(adsk.core.SelectionCommandInput.Vertices)
            selectionCameraDirection.setSelectionLimits(0)

            #inputs.addValueInput(identifier.WIDGET_ID_CAMERA_FOV, "Field of View (horizontal)", 'deg', adsk.core.ValueInput.createByReal(0.0))
            fovValueInput = groupCameraInputs.addAngleValueCommandInput(
                identifier.WIDGET_ID_CAMERA_FOV, 
                "Field of View (horizontal)", 
                adsk.core.ValueInput.createByString('30 degree'))
            # fovValueInput.setManipulator(adsk.core.Point3D.create(0, 0, 0), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 0, 1))
            fovValueInput.hasMinimumValue = False
            fovValueInput.hasMaximumValue = False

            # --- projectors

            groupProjectorInputCmd = inputs.addGroupCommandInput('groupProjector', 'Projector')
            groupProjectorInputCmd.isExpanded = True
            groupProjectorInputCmd.isEnabledCheckBoxDisplayed = True
            groupProjectorInputs = groupProjectorInputCmd.children

            selectionProjectorOrigin = groupProjectorInputs.addSelectionInput(
                identifier.WIDGET_ID_PROJECTOR_ORIGIN, 
                'Projector origin', 
                'Select a (sketch-)point for projector placement')
            selectionProjectorOrigin.addSelectionFilter(adsk.core.SelectionCommandInput.SketchPoints)            
            selectionProjectorOrigin.addSelectionFilter(adsk.core.SelectionCommandInput.Vertices)
            selectionProjectorOrigin.setSelectionLimits(0)

            selectionProjectorDirection = groupProjectorInputs.addSelectionInput(
                identifier.WIDGET_ID_PROJECTOR_DIRECTION, 
                'Projector direction', 
                'Select a (sketch-)point to define the projectors direction')
            selectionProjectorDirection.addSelectionFilter(adsk.core.SelectionCommandInput.SketchPoints)            
            selectionProjectorDirection.addSelectionFilter(adsk.core.SelectionCommandInput.Vertices)
            selectionProjectorDirection.setSelectionLimits(0)

            #inputs.addValueInput(identifier.WIDGET_ID_PROJECTOR_FOV, "Field of View (horizontal)", 'deg', adsk.core.ValueInput.createByReal(0.0))
            fovValueInput = groupProjectorInputs.addAngleValueCommandInput(
                identifier.WIDGET_ID_PROJECTOR_FOV, 
                "Field of View (horizontal)", 
                adsk.core.ValueInput.createByString('30 degree'))
            # fovValueInput.setManipulator(adsk.core.Point3D.create(0, 0, 0), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 0, 1))
            fovValueInput.hasMinimumValue = False
            fovValueInput.hasMaximumValue = False

            strProjectorImage = groupProjectorInputs.addStringValueInput(identifier.WIDGET_ID_PROJECTOR_IMAGE, 'Image path (e.g. testpattern.png)', 'Test pattern for the projector')

            # Connect to the inputChanged event.
            onInputChanged = ExportCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)

            # Connect to the execute event.
            onExecute = ExportCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            logger.debug("exportHandler created")

        except Exception as e:
            msg = "Export failed: {}".format(traceback.format_exc())
            logger.error(msg)
            ui.messagebox(msg)


# Event handler for the inputChanged event.
class ExportCommandInputChangedHandler(adsk.core.InputChangedEventHandler):

    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.InputChangedEventArgs.cast(args)
        
        logger.debug("exportHandler inputChanged")

        # Check the value of the check box.
        # changedInput = eventArgs.input
        # if changedInput.id == 'equilateral':
        #     inputs = eventArgs.firingEvent.sender.commandInputs
        #     scaleInput = inputs.itemById('heightScale')
			
        #     # Change the visibility of the scale value input.
        #     if changedInput.value == True:
        #         scaleInput.isVisible = False
        #     else:
        #         scaleInput.isVisible = True


# Event handler for the validateInputs event.
class ExportCommandValidateInputsHandler(adsk.core.ValidateInputsEventHandler):

    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.ValidateInputsEventArgs.cast(args)
        inputs = eventArgs.firingEvent.sender.commandInputs

        eventArgs.isValid = True

        # Check to see if the check box is checked or not.
        # checkBox = inputs.itemById('equilateral')
        # if checkBox.value == True:
        #     eventArgs.isValid = True
        # else:
        #     # Verify that the scale is greater than 0.1.
        #     scaleInput = inputs.itemById('heightScale')
        #     if scaleInput.value < 0.1:
        #         eventArgs.areInputsValid = False
        #     else:
        #         eventArgs.areInputsValid = True


def _get_all_bodies_from_selection(selectionInput):
    
    all_bodies = {}

    for i in range(0, selectionInput.selectionCount):
        selectedEntity = selectionInput.selection(i).entity

        if _check_if_visible(selectedEntity) is False:
            continue

        if selectedEntity.objectType == adsk.fusion.BRepBody.classType():
            all_bodies[selectedEntity.name] = selectedEntity
        elif selectedEntity.objectType == adsk.fusion.Component.classType():
       
            for occ in selectedEntity.allOccurrences:
                logger.debug("found occurence. name: {}".format(occ.name))

                if _check_if_visible(occ) is False:
                    continue

                suffix = ""
                if occ.name.rindex(":") > 0:
                    suffix = occ.name[occ.name.rindex(":")+1:]
               
                for body in occ.component.bRepBodies:

                    if _check_if_visible(body) is False:
                        continue

                    body_name = body.name

                    if suffix != "1":
                        body_name = "{}_{}".format(body.name, suffix)

                    all_bodies[body_name] = body
                    logger.debug("body name: {}".format(body_name))

            # logger.debug("Component was selected (contains {} bodies)".format(len(bodies_in_component)))

        else:
            msg = "unknown entity selected: {}".format(selectedEntity.objectType)
            logger.debug(msg)

    return all_bodies


def get_points_from_selection(selectionInput):

    points = []

    for i in range(0, selectionInput.selectionCount):
        selectedEntity = selectionInput.selection(i).entity

        if selectedEntity.objectType == adsk.fusion.SketchPoint.classType():
            points.append(selectedEntity)
        else:
            msg = "unknown entity selected: {}".format(selectedEntity.objectType)
            logger.debug(msg)

    return points


def set_visible(obj, on_off):
    if isinstance(obj, adsk.fusion.Component):
        obj.isBodiesFolderLightBulbOn = on_off
    else:
        obj.isLightBulbOn = on_off


def _check_if_visible(obj):

    # TODO: parent / occurence hidden?

    if isinstance(obj, adsk.fusion.Component):
        if not obj.isBodiesFolderLightBulbOn:
            return False

    if isinstance(obj, adsk.fusion.BRepBody):

        if obj.parentComponent is not None and not _check_if_visible(obj.parentComponent):
            return False
            
        if obj.isValid:
            return obj.isVisible

    return True


def _is_body_equal(design, body1, body2):

    # comparing bodies is apparently a bit tricky in Fusion360
    # return design.findEntityByToken(body1.entityToken) == design.findEntityByToken(body2.entityToken)
    # return body1 == body2
    return body1.name == body2.name # TODO: dirty fix


def _export_STL(obj, filename):

    logger.debug("preparing export: {}".format(filename))

    if obj.objectType != adsk.fusion.BRepBody.classType():
        raise Exception("export failed. Not a BRepBody: {}".format(obj))
    
    des = app.activeProduct
    root = des.rootComponent

    # when exporting single STLs Fusion will always export the STL relative to it's own
    # coordinate system, not the global one. When an component/body is placed somewhere by
    # the move command or by joints, the global coordinate system is required.
    # We can trick Fusion into using this by exporting the rootComponent instead of the 
    # single BRepBody and while setting all other bodies/components to invisible.
    # Afterwards we need to restore the original visibility settings.

    # Keep original visibility info:

    visibleList = []

    if root.isBodiesFolderLightBulbOn:
        visibleList = [root]

    for occ in root.allOccurrences:
        if occ.isLightBulbOn:
            for body in occ.component.bRepBodies:
                if body.isLightBulbOn:
                    visibleList.append(body)

    # make all invisible

    for item in visibleList:
        set_visible(item, False)      

    exportMgr = des.exportManager
    meshHigh = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    for item in visibleList:

        # out of all bodies, only proceed when we are iterating on the selected body
        if item.objectType == adsk.fusion.BRepBody.classType():
            if _is_body_equal(des, item, obj):
                pass
                # logger.debug("body found")
            else:
                # logger.debug("body not found. comparing {} | {}".format(item, obj))
                continue
        # elif isinstance(item, adsk.fusion.Occurence):
        #     for body in occ.component.bRepBodies:
        #         all_bodies.append(body)
        else:
            continue

        set_visible(item, True)
            
        # TODO: issue: same bodies in different occurences are visible at the same time
                
        stlExportOptions = exportMgr.createSTLExportOptions(root, filename)
        stlExportOptions.meshRefinement = meshHigh
        stlExportOptions.sendToPrintUtility = False
        exportMgr.execute(stlExportOptions)

        logger.debug("exported: {}".format(filename))

        set_visible(item, False)
        
    for item in visibleList:
        set_visible(item, True)

def _export_new(selectionInput):
    
    logger.debug("items in selection: {}".format(selectionInput.selectionCount))

    des = app.activeProduct
    root = des.rootComponent

    folder = "/tmp"

    filenames = []

    for i in range(0, selectionInput.selectionCount):
        selectedEntity = selectionInput.selection(i).entity

        for body in _get_all_bodies(selectedEntity):
            _export_STL(body)

    return filenames


class ExportCommandExecuteHandler(adsk.core.CommandEventHandler):

    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
        
        logger.debug("exportHandler execute")

        try:
            
            data = {}
            data["bodies"] = []
            data["mirrors"] = []
            data["projectors"] = []
            data["cameras"] = []

            regular_bodies = []
            mirror_bodies = []

            cmd = eventArgs.command
            inputs = cmd.commandInputs
            design = adsk.fusion.Design.cast(app.activeProduct)

            data_filename = None
            data_filename = functions.get_filename(ui)

            if data_filename is not None:
                logger.debug("user supplied filename: {}".format(str(data_filename)))
            else:
                logger.debug("no filename specified")
                data_filename = DEFAULT_FILENAME

            folder = os.path.split(data_filename)[0]

            regular_bodies = _get_all_bodies_from_selection(inputs.itemById(identifier.WIDGET_ID_ALLBODIES))
            logger.debug("regular_bodies: {}".format(len(regular_bodies)))

            mirror_bodies = _get_all_bodies_from_selection(inputs.itemById(identifier.WIDGET_ID_MIRRORS))
            logger.debug("mirror_bodies: {}".format(len(mirror_bodies)))

            # remove mirrors from regular bodies. (convencience feature necessary when the top component is selected for export)
            for key in mirror_bodies.keys():
                if key in regular_bodies:
                    del regular_bodies[key]

            for name, body in regular_bodies.items():
                filename = os.path.join(folder, "{}.stl".format(name))
                _export_STL(body, filename)
                data["bodies"].append(os.path.basename(filename))

            for name, body in mirror_bodies.items():
                filename = os.path.join(folder, "{}.stl".format(name))
                _export_STL(body, filename)
                data["mirrors"].append(os.path.basename(filename))

            # camera

            camera_data = {}

            # get origin
            points = get_points_from_selection(inputs.itemById(identifier.WIDGET_ID_CAMERA_ORIGIN))
            if len(points) > 0:
                camera_data["origin"] = [points[0].worldGeometry.x, points[0].worldGeometry.y, points[0].worldGeometry.z]
  
            # get orientation
            points = get_points_from_selection(inputs.itemById(identifier.WIDGET_ID_CAMERA_DIRECTION))
            if len(points) > 0:
                camera_data["direction"] = [points[0].worldGeometry.x, points[0].worldGeometry.y, points[0].worldGeometry.z]

            camera_data["fov"] = inputs.itemById(identifier.WIDGET_ID_CAMERA_FOV).value
            data["cameras"].append(camera_data)
            
            # projector

            projector_data = {}

            # get origin
            points = get_points_from_selection(inputs.itemById(identifier.WIDGET_ID_PROJECTOR_ORIGIN))
            if len(points) > 0:
                projector_data["origin"] = [points[0].worldGeometry.x, points[0].worldGeometry.y, points[0].worldGeometry.z]
  
            # get orientation
            points = get_points_from_selection(inputs.itemById(identifier.WIDGET_ID_PROJECTOR_DIRECTION))
            if len(points) > 0:
                projector_data["direction"] = [points[0].worldGeometry.x, points[0].worldGeometry.y, points[0].worldGeometry.z]

            projector_data["fov"] = inputs.itemById(identifier.WIDGET_ID_PROJECTOR_FOV).value
            projector_data["image"] = inputs.itemById(identifier.WIDGET_ID_PROJECTOR_IMAGE).value
            data["projectors"].append(projector_data)

            with open(data_filename, "w") as write_file:
                json.dump(data, write_file)

        except Exception as e:
            msg = "Export failed: {}".format(traceback.format_exc())
            logger.debug(msg)
            ui.messagebox(msg)
