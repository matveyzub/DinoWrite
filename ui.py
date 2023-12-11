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
RESOLUTION_DROPDOWN_LIST =    ["Camera Resolution","1/2","2/3","---"]

COLORS_PALLETE = {
    "white":"#dedede",
    "grey-bright":"#373737",
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
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

from importlib import reload
from pathlib import Path
from re import search as regsearch

from .utils import widgets , utils
from . import flipbook

import hou
import json

reload(flipbook)
reload(widgets)
reload(utils)

Icons = utils.Icons()
Fileparser = utils.FileParser()

class TitleBar(QWidget):
    """
    Custom titlebar with LOGO & TITLE & CLOSE BUTTON
    """

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        ### ICON
        window_icon = widgets.HIcon(Icons.getRandom(type="Path"),size=40) 

        ### TITLE
        TITLE_SIZE=14
        self.title = widgets.Label(WINDOW_TITLE,size=TITLE_SIZE)
        self.title.setMaximumWidth(WINDOW_WIDTH/1.5)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet(f"background-color:{COLORS_PALLETE['grey']};\
                            border-radius: 10px;\
                            color:{COLORS_PALLETE['white']};")
        self.title.setCursor(Qt.OpenHandCursor)

        ### CLOSE BUTTON
        CLOSE_BUTTON_SIZE = 20
        close_button = widgets.PushButton()
        close_button.setFixedSize(CLOSE_BUTTON_SIZE,CLOSE_BUTTON_SIZE)
        close_button.setIcon(Icons.get("close.svg"))
        close_button.setLayoutDirection(Qt.RightToLeft)
        close_button.setStyleSheet(f"QPushButton {{background-color:{COLORS_PALLETE['crimson']};\
                                                    border-radius: 10px;}}\
                                    QPushButton::hover {{background-color:{COLORS_PALLETE['red']};}}")
        close_button.clicked.connect(self.close_window)
        
        layout = widgets.HLayout([window_icon,self.title,close_button],align=None)
        layout.setContentsMargins(15,10,15,3)
        self.setLayout(layout)

        self.start = QPoint(0, 0)
        self.pressing = False

    def mousePressEvent(self, event):
        self.start = self.mapToGlobal(event.pos())
        self.pressing = True
        self.title.setCursor(Qt.ClosedHandCursor)

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
        self.title.setCursor(Qt.OpenHandCursor)

    def close_window(self):
        self.parent.close()

class DinoWriter(QWidget):

    def __init__(self,kwargs):
        '''
        Parent widget to houdini window to make it visible
        '''
        super().__init__(hou.qt.mainWindow())


        '''
        Adding search path to Qt to be able to using "icons:filepath" prefix in stylesheets files
        '''
        QDir.addSearchPath("icons",Path(__file__,"../icons").resolve().as_posix())


        '''
        Setting some flags to widget
        WindowTitle - allows you to track the widget among others and not paint a new widget, in case of a repeat call
        QtWindow and Frameless flags - just for TitleBar
        WA_DeleteOnClose attribute - allows to delete widget in application childrens after widget is closed
        FixedSize - Blocks the user from being able to stretch the widget in different directions
        '''
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedSize(WINDOW_WIDTH,WINDOW_HIGHT)
        self.setStyleSheet(f"background-color:{COLORS_PALLETE['grey-bright']};")


        '''
        Setting round edges on widget
        It seems to me that this option is bad, since the 
        mask is bitwise , which causes ugly aliasing at the edges
        '''
        radius = 15
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), radius, radius)
        mask = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)


        '''
        Settng proper widget position
        I'm believe that in should work on any monitor setup's
        The point is that the window does NOT spawn on the border of the monitors or beyond
        '''
        mouse_pos = QCursor.pos()
        screen = QDesktopWidget().screenNumber(mouse_pos)
        screenGeometry = QDesktopWidget().screenGeometry(screen)
        xpoint = min( max(mouse_pos.x()-WINDOW_WIDTH/2,screenGeometry.x() + WIDTH_OFFSET) , screenGeometry.x() + screenGeometry.width() - WINDOW_WIDTH - WIDTH_OFFSET )
        ypoint = min(mouse_pos.y()-WINDOW_HIGHT/2+HIGHT_OFFSET,screenGeometry.height()-WINDOW_HIGHT-100)
        self.move(QPoint(xpoint,ypoint))


        '''
        Promoting viewport settings and kwargs
        '''
        self.hou_viewport = utils.HouViewport(kwargs)
        self.kwargs = kwargs

        settingsfile = self.load_json(Path(__file__).parent / "settings.json")
        self.paths = settingsfile["paths"]
        self.formats = settingsfile["formats"]
        self.addresolution = settingsfile["custom_resolution"]
        self.addframerange = settingsfile["custom_framerange"]

        self.data = self.load_json(Path(self.get_tmp(), self.paths.get("tmp_data")))
        self.initUI()

    def initUI(self):

        ### INFO LINE
        info_frame = widgets.Frame(background_color=COLORS_PALLETE["grey"])
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        info_layout.setContentsMargins(10,5,10,5)

        self.cameraname = widgets.Label("Camera: {camera}".format(camera=self.hou_viewport.cameraName()))
        self.ramusage =   widgets.Label("RAM Usage: {ramusage}")
        self.seqname = widgets.ColorfulLabel()
        dino_paint = widgets.HIcon(Icons.get("label_dino_paint.svg",type="Path"),size=50)
        
        self.cameraname.setCursor(Qt.IBeamCursor)
        self.cameraname.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.ramusage.setCursor(Qt.IBeamCursor)
        self.ramusage.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.seqname.setCursor(Qt.IBeamCursor)
        self.seqname.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        sequence_layout = widgets.HLayout([self.seqname,dino_paint],align=None)

        info_layout.addWidget(self.cameraname)
        info_layout.addWidget(self.ramusage)
        info_layout.addLayout(sequence_layout)

        ## MAIN SETTINGS
        main_frame = widgets.Frame(background_color=COLORS_PALLETE["grey"])
        grid_layout = QGridLayout(main_frame)

        ### FIRST LINE
        label_filename =   widgets.HBLabel("Name")
        self.filename =    widgets.LineEdit(self.read_data("name", FILENAME_DEFAULT),hint=FILENAME_HINT)
        folders_list = self.flipbooks_menu()
        self.filename.setCompleter(widgets.Completer(folders_list))
        self.filename.installEventFilter(self)
        self.menu_button = widgets.DropDownButton(menu=folders_list, callback=self.setMenuItemFile)

        grid_layout.addWidget(label_filename, 0, 0)
        grid_layout.addWidget(self.filename, 0, 1, 1, 2)
        grid_layout.addWidget(self.menu_button, 0, 3)

        ### SECOND LINE
        label_res = widgets.HBLabel("Resolution")
        self.resx = widgets.LineEdit(self.read_data("resx", RESOLUTION_X_DEFAULT),hint=RESOLUTION_X_HINT)
        self.resx.setValidator(QIntValidator())
        self.resx.setCompleter(widgets.Completer([x.split(" ")[0] for x in self.addresolution]))
        self.resx.installEventFilter(self)

        self.resy = widgets.LineEdit(self.read_data("resy", RESOLUTION_Y_DEFAULT),hint=RESOLUTION_Y_HINT)
        self.resy.setValidator(QIntValidator())
        self.resy.setCompleter(widgets.Completer([x.split(" ")[1] for x in self.addresolution]))
        self.resy.installEventFilter(self)

        self.res_menu = widgets.DropDownButton(
            menu=RESOLUTION_DROPDOWN_LIST + self.addresolution, callback=self.setMenuItemResolution)

        grid_layout.addWidget(label_res, 1, 0)
        grid_layout.addWidget(self.resx, 1, 1)
        grid_layout.addWidget(self.resy, 1, 2)
        grid_layout.addWidget(self.res_menu, 1, 3)

        ### THIRD LINE
        label_range =     widgets.HBLabel("Frame Range")
        self.framestart = widgets.LineEdit(self.read_data("framestart", FRAME_START_DEFAULT),hint=FRAME_START_HINT)
        self.framestart.setCompleter(widgets.Completer(FRAME_RANGES_COMPLETER_LIST))
        self.framestart.installEventFilter(self)

        self.frameend =   widgets.LineEdit(self.read_data("frameend", FRAME_END_DEFAULT),hint=FRAME_END_HINT)
        self.frameend.setCompleter(widgets.Completer(FRAME_RANGES_COMPLETER_LIST))
        self.frameend.installEventFilter(self)

        self.native_ranges = FRAME_RANGES_DROPDOWN_DICT
        self.native_ranges.update(self.addframerange)
        self.frame_menu = widgets.DropDownButton(menu=self.native_ranges.keys(), callback=self.setMenuItemFrameRange)

        grid_layout.addWidget(label_range, 2, 0)
        grid_layout.addWidget(self.framestart, 2, 1)
        grid_layout.addWidget(self.frameend, 2, 2)
        grid_layout.addWidget(self.frame_menu, 2, 3)

        ### FOURTH LINE
        label_fileformat = widgets.HBLabel("File Format")
        self.fileformat =  widgets.ComboBox(self.formats["pic_exts"],item=self.read_data("fileformat", FILE_FORMAT_DEFAULT))

        grid_layout.addWidget(label_fileformat, 3, 0)
        grid_layout.addWidget(self.fileformat, 3, 1,1,3)

        ## CHECKBOXES
        checkbox_frame = widgets.Frame(background_color=COLORS_PALLETE["grey"])
        checkbox_layout = QVBoxLayout(checkbox_frame)

        self.convertvideo =       widgets.CheckBox(
            "Convert to video",self.read_data("convertvideo", CONVERT_VIDEO_DEFAULT))
        convertvideo_icon = widgets.HIcon(Icons.get("clapperboard.svg",type="Path"),size=15)
        self.blackbackground =    widgets.CheckBox(
            "Switch to black background", self.read_data("blackbg", BLACK_BACKGROUND_DEFAULT))
        blackbackground_icon = widgets.HIcon(Icons.get("circle-half-stroke.svg",type="Path"),size=15)
        self.offbackgroundimage = widgets.CheckBox(
            "Off Background Image",self.read_data("bgimage", OFF_BACKGROUND_IMAGE_DEFAULT))
        offbackgroundimage_icon = widgets.HIcon(Icons.get("eye-slash.svg",type="Path"),size=15)
        self.openwritefolder =    widgets.CheckBox(
            "Open write folder",self.read_data("openfolder", OPEN_WRITE_FOLDER_DEFAULT))
        openwritefolder_icon = widgets.HIcon(Icons.get("folder-open.svg",type="Path"),size=15)
        
        self.convertvideo.setToolTip("After the end of recording the flipbook,the entire \nsequence of files will be converted to video via ffmpeg")
        self.blackbackground.setToolTip("When recording a flipbook with white/gray background colors , the final \nimage turns out to be incorrect. \n\nThis checkbox switches the background to black during the recording of the flipbook")
        self.offbackgroundimage.setToolTip("When you use a shot sequence on the background, sometimes \nyou have to turn it off to record pure 3d and put \nthe background on the composition\n\nThis checkbox disable the background for the time of recording the flipbook and then \nreturn it to its original state")
        self.openwritefolder.setToolTip("After finishing recording, the flipbook opens the folder where it was recorded.")

        convertvideo_layout =       widgets.HLayout([self.convertvideo,convertvideo_icon])
        blackbackground_layout =    widgets.HLayout([self.blackbackground,blackbackground_icon])
        offbackgroundimage_layout = widgets.HLayout([self.offbackgroundimage,offbackgroundimage_icon])
        openwritefolder_layout =    widgets.HLayout([self.openwritefolder,openwritefolder_icon])

        checkbox_layout.addLayout(convertvideo_layout)
        checkbox_layout.addLayout(blackbackground_layout)
        checkbox_layout.addLayout(offbackgroundimage_layout)
        checkbox_layout.addLayout(openwritefolder_layout)
        
        ### MAIN BUTTON
        self.writebutton = widgets.PushButton("WRITE ", default=True,size=widgets.MAIN_SIZE+4)
        self.writebutton.setIcon(Icons.get("dino_cam.svg"))
        self.writebutton.setIconSize(QSize(35,35))
        self.writebutton.setLayoutDirection(Qt.RightToLeft)

        # LAYOUTS
        TITLE_LAYOUT = QVBoxLayout() 
        TITLE_LAYOUT.setContentsMargins(0,0,0,0)

        MAIN_LAYOUT = QVBoxLayout()
        MAIN_LAYOUT.setAlignment(Qt.AlignLeft | Qt.AlignTop)
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
        self.resx.editingFinished.connect(self.updateResolutions)
        self.resy.editingFinished.connect(self.updateRamUsage)
        self.resy.editingFinished.connect(self.updateResolutions)
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
        self.updateFileFormat()
        self.updateResolutions()


        '''
        Track if widget opened via search through childrens of Houdini Window
        Search by window title which we set in line 169
        '''
        flipbook_widget = None
        for w in hou.qt.mainWindow().children():
            if w.isWidgetType() and w.windowTitle()==WINDOW_TITLE and w.isVisible():
                    flipbook_widget = w

        if flipbook_widget:
            utils.logger(f"{TITLE} is already open")
            flipbook_widget.activateWindow()
        else:
            self.show()

    def eventFilter(self, source , event) -> bool:
        if  event.type() == QEvent.FocusIn or \
            event.type() == QEvent.KeyRelease and \
            event.key() not in [Qt.Key_Return,Qt.Key_Enter]:
            self.writebutton.setDefault(False)

        elif event.type() == QEvent.KeyRelease and \
            event.key() in [Qt.Key_Return,Qt.Key_Enter]:
            if self.writebutton.isDefault():
                self.writebutton.animateClick()
            self.writebutton.setDefault(True)

        if event.type() == QEvent.FocusOut and \
            source in [self.resx,self.resy]:
            self.updateResolutions()

        return super().eventFilter(source, event)
    
    def updateResolutions(self):
        self.resx.setText( str( max( int( self.resx.text() ),MIN_RESOLUTION_X) ) )
        self.resy.setText( str( max( int( self.resy.text() ),MIN_RESOLUTION_Y) ) )

    def updateFileFormat(self):
        state = self.convertvideo.isChecked()
        if state:
            self.fileformat.setCurrentText("exr")
            self.fileformat.setDisabled(True)
        else:
            self.fileformat.setDisabled(False)

    def updateColorfulLabel(self):

        label =     ["Sequence name: ",COLORS_PALLETE["white"]]
        separator = [".",COLORS_PALLETE["white"]]
        final_list = label

        fb_name = self.paths.get("fb_name")
        for name in fb_name.split("."):
            part = name.format(name=self.filename.text(),
                                version=Fileparser.getVersion(self.filename.text()),
                                fileformat=self.fileformat.currentText())
            
            if name == "{name}":
                final_list.append(part)
                final_list.append(COLORS_PALLETE["orange"])
            elif regsearch(r"\$F\d+",name):
                final_list.append(part)
                final_list.append(COLORS_PALLETE["green"])
            elif name == "{version}":
                final_list.append(part)
                final_list.append(COLORS_PALLETE["yellow"])
            elif name == "{fileformat}":
                final_list.append(part)
                final_list.append(COLORS_PALLETE["blue"])
            else:
                final_list.append(name)
                final_list.append(COLORS_PALLETE["white"])
            final_list+=separator
        self.seqname.update(final_list)

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
        elif item.find("/")!=-1:
            divisible,divider = item.split("/")
            ratio = int(divisible) / int(divider)
            resx = self.resx.text()
            resy = self.resy.text()
            newresx = max(round(int(resx)*ratio), MIN_RESOLUTION_X)
            newresy = max(round(int(resy)*ratio), MIN_RESOLUTION_Y)
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
        fb_folder_raw = hou.text.expandString(self.paths.get("fb_folder")).format(name=self.data.get("name"))
        pfolder = Path(fb_folder_raw).resolve().parent

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