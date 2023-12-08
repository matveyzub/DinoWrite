'''
DinoWrite UI File
Python Tool for Houdini to easily write flipbooks
'''

# CONSTANTs
TITLE = "DinoWrite"
VERSION = "1.2.4"
BRANCH = "main"
WINDOW_TITLE = f"{TITLE} - {VERSION} - {BRANCH}"

if BRANCH=="main":
    WINDOW_TITLE = TITLE

WINDOW_WIDTH = 430
WINDOW_HIGHT = 470
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

COLORS_PALLETE = {
    "white":"#dedede",
    "grey":"#2d2d2d",
    "red":"#ec3c48",
    "crimson":"#ff6570",
    "orange":"#fa7960",
    "yellow":"#f1d018",
    "green":"#04e762",
    "blue":"#00b6f8"
}

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

Icons = utils.Icons()
Fileparser = utils.FileParser()

# Functions
def qtCompleter(array:list) -> QtWidgets.QCompleter: 
    completer = QtWidgets.QCompleter(array)
    completer.setCaseSensitivity(QtGui.Qt.CaseInsensitive)
    completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
    return completer

class TitleBar(QtWidgets.QWidget):
    """
    Custom titlebar with LOGO & TITLE & CLOSE BUTTON
    """

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        ### ICON
        window_icon = qt_windows.HIcon(Icons.getRandom(type="Path"),size=40) 

        ### TITLE
        TITLE_SIZE=14
        title = qt_windows.Label(WINDOW_TITLE,size=TITLE_SIZE)
        title.setMaximumWidth(WINDOW_WIDTH/1.5)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet(f"background-color:{COLORS_PALLETE['grey']};\
                            border-radius: 10px;\
                            color:{COLORS_PALLETE['white']};")

        ### CLOSE BUTTON
        CLOSE_BUTTON_SIZE = 20
        close_button = qt_windows.PushButton()
        close_button.setFixedSize(CLOSE_BUTTON_SIZE,CLOSE_BUTTON_SIZE)
        close_button.setIcon(Icons.get("xmark.svg"))
        close_button.setLayoutDirection(QtCore.Qt.RightToLeft)
        close_button.setStyleSheet(f"QPushButton {{background-color:{COLORS_PALLETE['crimson']};\
                                                    border-radius: 10px;}}\
                                    QPushButton::hover {{background-color:{COLORS_PALLETE['red']};}}")
        close_button.clicked.connect(self.close_window)
        
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(15,10,15,3)
        layout.addWidget(window_icon)
        layout.addWidget(title)
        layout.addWidget(close_button)
        self.setLayout(layout)

        self.start = QtCore.QPoint(0, 0)
        self.pressing = False

    def mousePressEvent(self, event):
        self.start = self.mapToGlobal(event.pos())
        self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing:
            self.end = self.mapToGlobal(event.pos())
            self.movement = self.end-self.start
            self.parent.setGeometry(self.mapToGlobal(self.movement).x(),
                                self.mapToGlobal(self.movement).y(),
                                self.parent.width(),
                                self.parent.height())
            self.start = self.end

    def mouseReleaseEvent(self, QMouseEvent):
        self.pressing = False

    def close_window(self):
        self.parent.close()

class DinoWriter(QtWidgets.QWidget):

    def __init__(self,kwargs):
        super().__init__(hou.qt.mainWindow())
        
        QtCore.QDir.addSearchPath("icons",Path(__file__,"../icons").resolve().as_posix())

        self.hou_viewport = utils.HouViewport(kwargs)
        self.kwargs = kwargs

        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setFixedWidth(WINDOW_WIDTH)
        self.setFixedHeight(WINDOW_HIGHT)

        # Round edges on widget
        radius = 15
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), radius, radius)
        mask = QtGui.QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)

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
        self.initUI()

    def initUI(self):

        ### INFO LINE
        info_frame = qt_windows.Frame(background_color=COLORS_PALLETE["grey"])
        info_layout = QtWidgets.QVBoxLayout(info_frame)
        info_layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        info_layout.setContentsMargins(10,5,10,5)

        self.cameraname = qt_windows.Label("Camera: {camera}".format(camera=self.hou_viewport.cameraName()))
        self.ramusage =   qt_windows.Label("RAM Usage: {ramusage}")
        self.seqname = qt_windows.ColorfulLabel()
        self.cameraname.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.ramusage.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.seqname.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        
        dino_paint = qt_windows.HIcon(Icons.get("label_dino_paint.svg",type="Path"),size=50)

        sequence_layout = QtWidgets.QHBoxLayout()
        sequence_layout.addWidget(self.seqname)
        sequence_layout.addWidget(dino_paint)

        info_layout.addWidget(self.cameraname)
        info_layout.addWidget(self.ramusage)
        info_layout.addLayout(sequence_layout)

        ## MAIN SETTINGS
        main_frame = qt_windows.Frame(background_color=COLORS_PALLETE["grey"])
        grid_layout = QtWidgets.QGridLayout(main_frame)

        ### FIRST LINE
        label_filename =   qt_windows.HBLabel("Name")
        self.filename =    qt_windows.LineEdit(self.read_data("name", FILENAME_DEFAULT),hint=FILENAME_HINT)
        folders_list = self.flipbooks_menu()
        self.filename.setCompleter(qtCompleter(folders_list))
        self.filename.installEventFilter(self)
        self.menu_button = qt_windows.DropDownButton(menu=folders_list, callback=self.setMenuItemFile)

        grid_layout.addWidget(label_filename, 0, 0)
        grid_layout.addWidget(self.filename, 0, 1, 1, 2)
        grid_layout.addWidget(self.menu_button, 0, 3)

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

        grid_layout.addWidget(label_res, 1, 0)
        grid_layout.addWidget(self.resx, 1, 1)
        grid_layout.addWidget(self.resy, 1, 2)
        grid_layout.addWidget(self.res_menu, 1, 3)

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

        grid_layout.addWidget(label_range, 2, 0)
        grid_layout.addWidget(self.framestart, 2, 1)
        grid_layout.addWidget(self.frameend, 2, 2)
        grid_layout.addWidget(self.frame_menu, 2, 3)

        ### FOURTH LINE
        label_fileformat = qt_windows.HBLabel("File Format")
        self.fileformat =  qt_windows.ComboBox(self.formats["pic_exts"],item=self.read_data("fileformat", FILE_FORMAT_DEFAULT))

        grid_layout.addWidget(label_fileformat, 3, 0)
        grid_layout.addWidget(self.fileformat, 3, 1,1,3)

        ## CHECKBOXES
        checkbox_frame = qt_windows.Frame(background_color=COLORS_PALLETE["grey"])
        checkbox_layout = QtWidgets.QVBoxLayout(checkbox_frame)

        self.convertvideo =       qt_windows.CheckBox(
            "Convert to video",self.read_data("convertvideo", CONVERT_VIDEO_DEFAULT))
        convertvideo_icon = qt_windows.HIcon(Icons.get("clapperboard.svg",type="Path"),size=15)
        self.blackbackground =    qt_windows.CheckBox(
            "Switch to black background", self.read_data("blackbg", BLACK_BACKGROUND_DEFAULT))
        blackbackground_icon = qt_windows.HIcon(Icons.get("circle-half-stroke.svg",type="Path"),size=15)
        self.offbackgroundimage = qt_windows.CheckBox(
            "Off Background Image",self.read_data("bgimage", OFF_BACKGROUND_IMAGE_DEFAULT))
        offbackgroundimage_icon = qt_windows.HIcon(Icons.get("eye-slash.svg",type="Path"),size=15)
        self.openwritefolder =    qt_windows.CheckBox(
            "Open write folder",self.read_data("openfolder", OPEN_WRITE_FOLDER_DEFAULT))
        openwritefolder_icon = qt_windows.HIcon(Icons.get("folder-open.svg",type="Path"),size=15)
        
        self.convertvideo.setToolTip("After the end of recording the flipbook,the entire \nsequence of files will be converted to video via ffmpeg")
        self.blackbackground.setToolTip("When recording a flipbook with white/gray background colors , the final \nimage turns out to be incorrect. \n\nThis checkbox switches the background to black during the recording of the flipbook")
        self.offbackgroundimage.setToolTip("When you use a shot sequence on the background, sometimes \nyou have to turn it off to record pure 3d and put \nthe background on the composition\n\nThis checkbox disable the background for the time of recording the flipbook and then \nreturn it to its original state")
        self.openwritefolder.setToolTip("After finishing recording, the flipbook opens the folder where it was recorded.")

        convertvideo_layout =       qt_windows.HWidget([self.convertvideo,convertvideo_icon])
        blackbackground_layout =    qt_windows.HWidget([self.blackbackground,blackbackground_icon])
        offbackgroundimage_layout = qt_windows.HWidget([self.offbackgroundimage,offbackgroundimage_icon])
        openwritefolder_layout =    qt_windows.HWidget([self.openwritefolder,openwritefolder_icon])

        checkbox_layout.addLayout(convertvideo_layout)
        checkbox_layout.addLayout(blackbackground_layout)
        checkbox_layout.addLayout(offbackgroundimage_layout)
        checkbox_layout.addLayout(openwritefolder_layout)
        
        ### MAIN BUTTON
        self.writebutton = qt_windows.PushButton("WRITE ", default=True,size=qt_windows.MAIN_SIZE+4)
        self.writebutton.setIcon(Icons.get("dino_cam.svg"))
        self.writebutton.setIconSize(QtCore.QSize(35,35))
        self.writebutton.setLayoutDirection(QtCore.Qt.RightToLeft)

        # LAYOUTS
        TITLE_LAYOUT = QtWidgets.QVBoxLayout() 
        TITLE_LAYOUT.setContentsMargins(0,0,0,0)

        MAIN_LAYOUT = QtWidgets.QVBoxLayout()
        MAIN_LAYOUT.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        MAIN_LAYOUT.setContentsMargins(10,10,10,10)

        MAIN_LAYOUT.addWidget(info_frame)
        MAIN_LAYOUT.addWidget(main_frame)
        MAIN_LAYOUT.addWidget(checkbox_frame)
        MAIN_LAYOUT.addWidget(self.writebutton)

        TITLE_LAYOUT.addWidget(TitleBar(self))
        TITLE_LAYOUT.addLayout(MAIN_LAYOUT)

        self.setLayout(TITLE_LAYOUT)

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
        self.convertvideo.stateChanged.connect(self.updateFileFormat)
        self.writebutton.clicked.connect(self.main)

        # SCRIPTS
        self.updateRamUsage()
        self.updateColorfulLabel()

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

        return super().eventFilter(source, event)

    def updateFileFormat(self):
        state = self.convertvideo.isChecked()
        if state:
            self.fileformat.setCurrentText("exr")
            self.fileformat.setDisabled(True)
        else:
            self.fileformat.setDisabled(False)

    def updateColorfulLabel(self):
        self.seqname.update(["Sequence name: ",COLORS_PALLETE["white"],
                            self.filename.text(),COLORS_PALLETE["orange"],
                            ".",COLORS_PALLETE["white"],
                            Fileparser.getVersion(self.filename.text()),COLORS_PALLETE["yellow"],
                            ".",COLORS_PALLETE["white"],
                            "$F4",COLORS_PALLETE["green"],
                            ".",COLORS_PALLETE["white"],
                            self.fileformat.currentText(),COLORS_PALLETE["blue"]])

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
                self.close()
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