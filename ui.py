'''
DinoWrite UI File
Python Tool for Houdini to easily write flipbooks
'''

# CONSTANTs
TITLE = "DinoWrite"
VERSION = "1.2.0"
BRANCH = "dev"
WINDOW_TITLE = f"{TITLE} - {VERSION} - {BRANCH}"

WINDOW_WIDTH = 400
WINDOW_HIGHT = 380
WIDTH_OFFSET = 20
HIGHT_OFFSET = 90

MIN_RESOLUTION_X = 128
MIN_RESOLUTION_Y = 128

FILENAME_DEFAULT = "flipbook"
FILENAME_HINT = "Flipbook name"

RESOLUTION_X_DEFAULT = "1920"
RESOLUTION_X_HINT = "Width"

RESOLUTION_Y_DEFAULT = "1080"
RESOLUTION_Y_HINT = "Height"

FRAME_START_DEFAULT = "$FSTART"
FRAME_START_HINT = "Start frame"

FRAME_END_DEFAULT = "$FEND"
FRAME_END_HINT = "End frame"

FILE_FORMAT_DEFAULT = "exr"

CONVERT_VIDEO_DEFAULT = False
BLACK_BACKGROUND_DEFAULT = True
OFF_BACKGROUND_IMAGE_DEFAULT = True
OPEN_WRITE_FOLDER_DEFAULT = True

FRAME_RANGES_DROPDOWN_DICT =  { "Global Frame Range":"$FSTART $FEND",
                                "Playbar Frame Range":"$RFSTART $RFEND",
                                "---":""}
FRAME_RANGES_COMPLETER_LIST = ['$F','$FSTART','$FEND','$RFSTART','$RFEND']
RESOLUTION_DROPDOWN_LIST =    ["Camera Resolution", "50%", "---"]

BYTES_TOLERANCE = 1024

# IMPORTs
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from importlib import reload
from pathlib import Path

from .utils import qt_windows , utils
from . import flipbook

import hou
import json

reload(flipbook)
reload(qt_windows)
reload(utils)

# if BRANCH=="main":
#     WINDOW_TITLE = f"{TITLE} - {{version}}"

# Functions
def qtCompleter(array:list) -> QtWidgets.QCompleter: 
    completer = QtWidgets.QCompleter(array)
    completer.setCaseSensitivity(QtGui.Qt.CaseInsensitive)
    completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
    return completer

# Main Class
class flipbook_menu(QtWidgets.QWidget):

    def __init__(self,kwargs):
        super().__init__(hou.qt.mainWindow())

        self.Icons = utils.Icons()
        self.hou_viewport = utils.HouViewport(kwargs)
        self.kwargs = kwargs

        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setFixedWidth(WINDOW_WIDTH)
        self.setFixedHeight(WINDOW_HIGHT)
        self.setWindowIcon(self.Icons.getRandom())

        # Set proper window pos
        mouse_pos = QtGui.QCursor.pos()
        screen = QtWidgets.QDesktopWidget().screenNumber(mouse_pos)
        screenGeometry = QtWidgets.QDesktopWidget().screenGeometry(screen)
        xpoint = min( max(mouse_pos.x()-WINDOW_WIDTH/2,screenGeometry.x() + WIDTH_OFFSET) , screenGeometry.x() + screenGeometry.width() - WINDOW_WIDTH - WIDTH_OFFSET )
        ypoint = min(mouse_pos.y()-WINDOW_HIGHT/2+HIGHT_OFFSET,screenGeometry.height()-WINDOW_HIGHT-100)
        self.move(QtCore.QPoint(xpoint,ypoint))

        settingsfile = self.load_json(Path(__file__).parent / "settings.json")
        self.paths = settingsfile["paths"]
        self.formats = settingsfile["formats"]
        self.addresolution = settingsfile["custom_resolution"]
        self.addframerange = settingsfile["custom_framerange"]

        self.data = self.load_json(Path(self.get_tmp(), self.paths.get("tmp_data")))

        self.fileparser = utils.FileParser()

        self.initUI()

    def initUI(self):
        # WIDGETS

        ### INFO LINE
        self.cameraname = qt_windows.Label("Camera: {camera}".format(camera=self.hou_viewport.cameraName()))
        self.ramusage = qt_windows.Label("")

        ### FIRST LINE
        label_filename =   qt_windows.HBLabel("Name")
        self.filename =    qt_windows.LineEdit(self.read_data("name", FILENAME_DEFAULT),hint=FILENAME_HINT)
        self.filename.setCompleter(qtCompleter(self.flipbooks_menu()))
        self.filename.installEventFilter(self)

        self.menu_button = qt_windows.DropDownButton(
            menu=self.flipbooks_menu(), callback=self.setMenuItemFile)

        ### SECOND LINE
        label_res = qt_windows.HBLabel("Resolution")
        self.resx = qt_windows.LineEdit(self.read_data("resx", RESOLUTION_X_DEFAULT),hint=RESOLUTION_X_HINT)
        self.resx.setValidator(QtGui.QIntValidator())
        self.resx.setCompleter(qtCompleter([x.split(" ")[0] for x in self.addresolution]))
        self.resx.installEventFilter(self)

        self.resy = qt_windows.LineEdit(self.read_data("resy", RESOLUTION_Y_DEFAULT),hint=RESOLUTION_Y_HINT)
        self.resy.setValidator(QtGui.QIntValidator())
        self.resy.setCompleter(qtCompleter([x.split(" ")[1] for x in self.addresolution]))
        self.resy.installEventFilter(self)

        self.res_menu = qt_windows.DropDownButton(
            menu=RESOLUTION_DROPDOWN_LIST + self.addresolution, callback=self.setMenuItemResolution)

        ### THIRD LINE
        label_range =     qt_windows.HBLabel("Frame Range")
        self.framestart = qt_windows.LineEdit(self.read_data("framestart", FRAME_START_DEFAULT),hint=FRAME_START_HINT)
        self.framestart.setCompleter(qtCompleter(FRAME_RANGES_COMPLETER_LIST))
        self.framestart.installEventFilter(self)

        self.frameend =   qt_windows.LineEdit(self.read_data("frameend", FRAME_END_DEFAULT),hint=FRAME_END_HINT)
        self.frameend.setCompleter(qtCompleter(FRAME_RANGES_COMPLETER_LIST))
        self.frameend.installEventFilter(self)

        self.native_ranges = FRAME_RANGES_DROPDOWN_DICT
        self.native_ranges.update(self.addframerange)
        self.frame_menu = qt_windows.DropDownButton(menu=self.native_ranges.keys(), callback=self.setMenuItemFrameRange)

        self.updateRamUsage()

        ### FOURTH LINE
        label_fileformat = qt_windows.HBLabel("File Format")
        self.fileformat =  qt_windows.ComboBox(self.formats["pic_exts"],item=self.read_data("fileformat", FILE_FORMAT_DEFAULT))

        ### CHECKBOXES
        self.convertvideo =       qt_windows.CheckBox(
            "Convert to video",self.read_data("convertvideo", CONVERT_VIDEO_DEFAULT))
        self.blackbackground =    qt_windows.CheckBox(
            "Switch to black background", self.read_data("blackbg", BLACK_BACKGROUND_DEFAULT))
        self.offbackgroundimage = qt_windows.CheckBox(
            "Off Background Image",self.read_data("bgimage", OFF_BACKGROUND_IMAGE_DEFAULT))
        self.openwritefolder =    qt_windows.CheckBox(
            "Open write folder",self.read_data("openfolder", OPEN_WRITE_FOLDER_DEFAULT))
        
        ### MAIN BUTTON
        self.writebutton = qt_windows.PushButton("WRITE", default=True,size=qt_windows.MAIN_SIZE+4)

        ### COLOR FILENAME
        self.label_name = qt_windows.ColorfulLabel(self.filename.text(),
                                                self.fileparser.getVersion(self.filename.text()),
                                                "$F4",
                                                self.fileformat.currentText())

        # LAYOUTS
        grid =  QtWidgets.QGridLayout()
        MAIN_LAYOUT = QtWidgets.QVBoxLayout()

        grid.addWidget(label_filename, 0, 0)
        grid.addWidget(self.filename, 0, 1, 1, 2)
        grid.addWidget(self.menu_button, 0, 3)

        grid.addWidget(label_res, 1, 0)
        grid.addWidget(self.resx, 1, 1)
        grid.addWidget(self.resy, 1, 2)
        grid.addWidget(self.res_menu, 1, 3)

        grid.addWidget(label_range, 2, 0)
        grid.addWidget(self.framestart, 2, 1)
        grid.addWidget(self.frameend, 2, 2)
        grid.addWidget(self.frame_menu, 2, 3)

        grid.addWidget(label_fileformat, 3, 0)
        grid.addWidget(self.fileformat, 3, 1, 1, 3)

        MAIN_LAYOUT.addWidget(self.cameraname)
        MAIN_LAYOUT.addWidget(self.ramusage)
        MAIN_LAYOUT.addSpacing(10)
        MAIN_LAYOUT.addWidget(qt_windows.HSeparator())
        MAIN_LAYOUT.addLayout(grid)
        MAIN_LAYOUT.addWidget(qt_windows.HSeparator())
        MAIN_LAYOUT.addWidget(self.convertvideo)
        MAIN_LAYOUT.addWidget(self.blackbackground)
        MAIN_LAYOUT.addWidget(self.offbackgroundimage)
        MAIN_LAYOUT.addWidget(self.openwritefolder)
        MAIN_LAYOUT.addWidget(qt_windows.HSeparator())
        MAIN_LAYOUT.addWidget(self.writebutton)
        MAIN_LAYOUT.addWidget(self.label_name)

        self.setLayout(MAIN_LAYOUT)

        # SIGNALS
        self.filename.editingFinished.connect(self.updateColorfulLabel)
        self.menu_button.menu.triggered.connect(self.updateColorfulLabel)
        self.fileformat.currentIndexChanged.connect(self.updateColorfulLabel)
        self.resx.editingFinished.connect(self.updateRamUsage)
        self.resy.editingFinished.connect(self.updateRamUsage)
        self.res_menu.menu.triggered.connect(self.updateRamUsage)
        self.res_menu.menu.triggered.connect(self.updateCameraLabel)
        self.framestart.editingFinished.connect(self.updateRamUsage)
        self.frameend.editingFinished.connect(self.updateRamUsage)
        self.frame_menu.menu.triggered.connect(self.updateRamUsage)
        self.writebutton.clicked.connect(self.main)

        # SCRIPTS
        flipbook_widget = None
        for w in hou.qt.mainWindow().children():
            if w.isWidgetType():
                if w.windowTitle()==WINDOW_TITLE and w.isVisible():
                    flipbook_widget = w

        if flipbook_widget:
            utils.logger(f"{TITLE} is already open")
            flipbook_widget.activateWindow()
        else:
            self.show()

    def eventFilter(self, source , event) -> bool:
        if  event.type() == QtCore.QEvent.FocusIn or \
            event.type() == QtCore.QEvent.KeyRelease and \
            event.key() not in [QtCore.Qt.Key_Return,QtCore.Qt.Key_Enter]:
            self.writebutton.setDefault(False)

        elif event.type() == QtCore.QEvent.KeyRelease and \
            event.key() in [QtCore.Qt.Key_Return,QtCore.Qt.Key_Enter]:
            if self.writebutton.isDefault():
                self.writebutton.animateClick()
            self.writebutton.setDefault(True)

        # if source==self.convertvideo and event.type()==QtCore.QEvent.MouseButtonRelease:
        #     if self.convertvideo.isChecked():
        #         self.fileformat.clear()
        #         self.fileformat.addItems(self.formats["pic_exts"])
        #     else:
        #         self.fileformat.clear()
        #         self.fileformat.addItems(self.formats["video_exts"])

        return super().eventFilter(source, event)

    def updateColorfulLabel(self):
        self.label_name.update(name=self.filename.text(),
                                version=self.fileparser.getVersion(self.filename.text()),
                                extension=self.fileformat.currentText())

    def updateCameraLabel(self):
        self.cameraname.setText(f"Camera: {self.hou_viewport.cameraName()}")

    def setMenuItemFile(self):
        item = self.sender().text()
        self.filename.setText(item)

    def setMenuItemResolution(self):
        item = self.sender().text()

        if item == "Camera Resolution":
            camera_res = self.hou_viewport.cameraResolution()
            self.resx.setText(str(camera_res[0]))
            self.resy.setText(str(camera_res[1]))
        elif item == "50%":
            resx = self.resx.text()
            resy = self.resy.text()
            newresx = max(round(int(resx)/2), MIN_RESOLUTION_X)
            newresy = max(round(int(resy)/2), MIN_RESOLUTION_Y)
            self.resx.setText(str(newresx))
            self.resy.setText(str(newresy))
        else:
            x, y = item.split(" ")
            self.resx.setText(str(x))
            self.resy.setText(str(y))

    def setMenuItemFrameRange(self):
        item = self.sender().text()
        start,end = self.native_ranges[item].split()

        self.framestart.setText(start)
        self.frameend.setText(end)

    def ramUsage(self):
        pixels_count = int(self.resx.text()) * int(self.resy.text())
        image_in_bytes = pixels_count * 4
        image_in_mbytes = image_in_bytes / BYTES_TOLERANCE / BYTES_TOLERANCE
        frame_range = max(int(hou.text.expandString(self.frameend.text())) - int(hou.text.expandString(self.framestart.text())) + 1,1)
        mbytes = image_in_mbytes * frame_range
        return mbytes
    
    def updateRamUsage(self):
        ram = self.ramUsage()
        if ram<=BYTES_TOLERANCE:
            ramtext = f"RAM Usage: {ram:.2f} MB"
        else:
            ramtext = f"RAM Usage: {ram/BYTES_TOLERANCE :.2f} GB"
        self.ramusage.setText(ramtext)

    def flipbooks_menu(self):
        pfolder = Path(hou.text.expandString(self.paths.get("fb_folder")).format(name=self.data.get("name"))).resolve().parent

        if not pfolder.exists():
            if not hou.ui.displayMessage(f"{self.paths.get('fb_folder')}\nNo folder found\nWanna create it?",buttons=("Yes","No")):
                pfolder.mkdir(parents=True, exist_ok=True)
            else:
                utils.logger("No folder to write in flipbooks\nChange path or create folder")
                return []

        folders = [x.name for x in pfolder.iterdir() if x.is_dir()]
        return folders

    def get_tmp(self):
        hou_temp = Path(hou.text.expandString(self.paths.get("tmp_folder")))

        if not hou_temp.exists():
            hou_temp.mkdir(parents=True, exist_ok=True)

        return hou_temp.as_posix()

    def main(self):

        # Check lineedits validness
        check_lines = [self.filename,self.resx,self.resy,self.framestart,self.frameend]
        empty_array = []
        string_of_empty = ""
        for line in check_lines:
            if len(line.text())==0:
                empty_array.append(line.placeholderText())
        if len(empty_array)>0:
            for i,element in enumerate(empty_array):
                string_of_empty += f"{str(i+1)}.{element}\n"
            utils.hmsg(f"Empty line detected!\nPlease check values in:\n{string_of_empty}")
            return 0

        # Create data to store
        hou_temp = self.get_tmp()
        data = {
            "name": self.filename.text(),
            "resx": self.resx.text(),
            "resy": self.resy.text(),
            "aspect": self.hou_viewport.cameraPixelAspect(),
            "framestart": self.framestart.text(),
            "frameend": self.frameend.text(),
            "fileformat": self.fileformat.currentText(),
            "convertvideo": self.convertvideo.isChecked(),
            "blackbg": self.blackbackground.isChecked(),
            "bgimage": self.offbackgroundimage.isChecked(),
            "openfolder": self.openwritefolder.isChecked()
        }
        data_file = Path(hou_temp, self.paths.get("tmp_data")).as_posix()
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # Proceed hip and start flipbook script
        self.close()
        hou.hipFile.saveAndBackup()
        flipbook.start(data,self.kwargs)

    def load_json(self, file):
        try:
            with open(file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def read_data(self, key, value):
        return self.data.get(key) if self.data.get(key) != None else value