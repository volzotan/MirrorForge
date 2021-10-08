# Author-
# Description-

import adsk.core
import adsk.fusion
import traceback

import logging

from .config import Configuration
from .util import identifier, functions
from .handlers import exportHandler
from .handlers import addCurveHandler

# The following two lines must be uncommented
# for logging to work correctly while running
# within Fusion 360
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=Configuration.LOG_FILE, level=Configuration.LOG_LEVEL)
logger = logging.getLogger("MirrorForge")

handlers = []

def run(context):

    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Add panel

        # workspace = ui.workspaces.itemById('FusionSolidEnvironment')
        # panels = workspace.toolbarPanels

        allDesignTabs = ui.toolbarTabsByProductType('DesignProductType')
        toolsTab = allDesignTabs.itemById('SolidTab') 
        panels = toolsTab.toolbarPanels

        logger.debug("Creating MirrorForge Panel")
        
        mfPanel = panels.itemById(identifier.MIRRORFORGE_PANEL_ID)
        if mfPanel:
            mfPanel.deleteMe()
        mfPanel = panels.add(identifier.MIRRORFORGE_PANEL_ID, "MirrorForge", "SelectPanel", False)
        
        # Add commands

        cmdDef = ui.commandDefinitions.itemById(identifier.COMMAND_ID_EXPORT)
        if cmdDef:
            cmdDef.deleteMe()
        cmdDef = ui.commandDefinitions.addButtonDefinition(identifier.COMMAND_ID_EXPORT, 
            "Export to Blender", 
            "Export a component for rendering in blender", 
            ".//Resources//Export")

        exportCommandCreated = exportHandler.ExportCommandCreatedEventHandler()
        cmdDef.commandCreated.add(exportCommandCreated)
        handlers.append(exportCommandCreated)
        mfPanel.controls.addCommand(cmdDef)

        cmdDef = ui.commandDefinitions.itemById(identifier.COMMAND_ID_ADD_CURVE)
        if cmdDef:
            cmdDef.deleteMe()
        cmdDef = ui.commandDefinitions.addButtonDefinition(identifier.COMMAND_ID_ADD_CURVE, 
            "Import curve", 
            "Import a curve specified as CSV data", 
            ".//Resources//Curve")

        addCurveCommandCreated = addCurveHandler.AddCurveCommandCreatedEventHandler()
        cmdDef.commandCreated.add(addCurveCommandCreated)
        handlers.append(addCurveCommandCreated)
        mfPanel.controls.addCommand(cmdDef)

        # If the command is being manually started let the user know it's done
        if context['IsApplicationStartup'] is False:
            ui.messageBox('The AddIn has been loaded and added\nto the CREATE panel of the MODEL workspace.')

        # TODO: remove
        ui.messageBox("init")

    except:
        msg = 'Failed:\n{}'.format(traceback.format_exc())
        logger.error(msg)
        if ui:
            ui.messageBox(msg)

        exit()

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        allDesignTabs = ui.toolbarTabsByProductType("DesignProductType")
        toolsTab = allDesignTabs.itemById("SolidTab") 
        panels = toolsTab.toolbarPanels

        allCommandIdentifier = [
            identifier.COMMAND_ID_ADD_CURVE,
            identifier.COMMAND_ID_EXPORT,
        ]

        for commandIntentifier in allCommandIdentifier:
            cmdDef = ui.commandDefinitions.itemById(commandIntentifier)
            if cmdDef:
                cmdDef.deleteMe()

        mfPanel = panels.itemById(identifier.MIRRORFORGE_PANEL_ID)
        if mfPanel:
            mfPanel.deleteMe()

        logger.debug("Mirrorforge AddIn stopped")

    except:
        msg = "Mirrorforge AddIn stop failed: {}".format(traceback.format_exc())
        logger.debug(msg)
        if ui:
            ui.messageBox(msg)