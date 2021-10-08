import logging
import io

import adsk.core, adsk.fusion, traceback
from adsk.core import Application

from ..util import identifier

app = Application.get()
ui = app.userInterface

handlers = []
logger = logging.getLogger("addCurveHandler")

class AddCurveCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):

    def __init__(self):
        super().__init__()

    def notify(self, args):

        try:

            logger.debug("addCurveHandler init")

            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            cmd.setDialogInitialSize(1000, 1000)

            # Get the CommandInputs collection to create new command inputs.            
            inputs = cmd.commandInputs

            # Connect to the execute event.
            onExecute = AddCurveCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            logger.debug("addCurveHandler created")


        except Exception as e:
            ui.messagebox("adding curve failed: {}".format(traceback.format_exc()))


class AddCurveCommandExecuteHandler(adsk.core.CommandEventHandler):

    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface
            # Get all components in the active design.
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
            title = 'Import Line csv'
            if not design:
                ui.messageBox('No active Fusion design', title)
                return
            
            dlg = ui.createFileDialog()
            dlg.title = 'Open CSV File'
            dlg.filter = 'Comma Separated Values (*.csv);;All Files (*.*)'
            if dlg.showOpen() != adsk.core.DialogResults.DialogOK :
                return
            
            filename = dlg.filename
            with io.open(filename, 'r', encoding='utf-8-sig') as f:
                points = adsk.core.ObjectCollection.create()
                line = f.readline()
                data = []
                while line:
                    pntStrArr = line.split(',')
                    for pntStr in pntStrArr:
                        try:
                            data.append(float(pntStr) / 10.0 ) # default unit is assumed to be centimeters
                        except:
                            break
                
                    if len(data) >= 3 :
                        point = adsk.core.Point3D.create(data[0], data[1], data[2])
                        points.add(point)
                    line = f.readline()
                    data.clear()            
            if points.count:
                root = design.rootComponent
                sketch = root.sketches.add(root.xYConstructionPlane)

                lines = []

                for i in range(0, len(points)):  

                    if i == 0:
                        start = points[0]
                        end = points[1]
                    elif i == len(points)-1:
                        start = lines[-1].endSketchPoint
                        end = lines[0].startSketchPoint
                    else:
                        start = lines[-1].endSketchPoint
                        end = points[i+1]

                    lines.append(sketch.sketchCurves.sketchLines.addByTwoPoints(start, end))

                # sketch.sketchCurves.sketchFittedSplines.add(points)
                # ui.messageBox("points: {}".format(points.count), title)    
            else:
                ui.messageBox('No valid points', title)          
                
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
