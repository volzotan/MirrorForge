import adsk.core      

def get_filename(ui):    
    fileDialog = ui.createFileDialog()
    fileDialog.isMultiSelectEnabled = False
    fileDialog.title = "Specify result filename"
    fileDialog.filter = "JSON files (*.json)"
    fileDialog.filterIndex = 0
    dialogResult = fileDialog.showSave()
    if dialogResult == adsk.core.DialogResults.DialogOK:
        return fileDialog.filename
    else:
        return