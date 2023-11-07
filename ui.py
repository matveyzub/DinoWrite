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

class flipbook_menu(QtWidgets.QDialog):

    def __init__(self):
        super().__init__(hou.qt.mainWindow())

        self.setWindowTitle("Write flipbook")
        self.setGeometry(300, 300, 400, 300)
        self.setMaximumSize(QtCore.QSize(400, 350))

        self.settings = self.load_json(Path(__file__).parent / "settings.json")
        self.data = self.load_json(
            Path(self.get_tmp(), self.settings.get("tmp_data")))
        self.hou_viewport = utils.HouViewport()

        self.initUI()

    def initUI(self):
        # WIDGETS
        label_filename =   qt_windows.MainLabel("Name")
        self.filename =    qt_windows.LineEdit(self.read_data("name", "flipbook"))
        self.menu_button = qt_windows.DropDownButton(
            menu=self.flipbooks_menu(), callback=self.setMenuItemFile)
        
        self.filename.installEventFilter(self)

        label_res = qt_windows.MainLabel("Resolution")
        self.resx = qt_windows.LineEdit(self.read_data("resx", "1920"))
        self.resy = qt_windows.LineEdit(self.read_data("resy", "1080"))
        self.res_menu = qt_windows.DropDownButton(
            menu=["Camera Resolution", "50%", "---", "3840 2160", "1920 1080", "1280 720"], callback=self.setMenuItemResolution)
        
        self.resx.installEventFilter(self)
        self.resy.installEventFilter(self)

        self.resx.setValidator(QtGui.QIntValidator())
        self.resy.setValidator(QtGui.QIntValidator())

        label_range = qt_windows.MainLabel("Frame Range")
        self.framestart = qt_windows.LineEdit(
            self.read_data("framestart", "$FSTART"))
        self.frameend = qt_windows.LineEdit(
            self.read_data("frameend", "$FEND"))
        self.frame_menu = qt_windows.DropDownButton(
            menu=["Global Frame Range", "Playbar Frame Range"], callback=self.setMenuItemFrameRange)
        
        self.framestart.installEventFilter(self)
        self.frameend.installEventFilter(self)

        formats_dict = {0: "exr", 1: "jpg", 2: "png"}
        label_fileformat = qt_windows.MainLabel("File Format")
        self.fileformat =  qt_windows.ComboBox(formats_dict.values(),item=self.read_data("fileformat", "exr"))

        self.convertvideo = qt_windows.CheckBox(
            "Convert to video",          self.read_data("convertvideo", False))
        self.blackbackground = qt_windows.CheckBox(
            "Switch to black background", self.read_data("blackbg", True))
        self.offbackgroundimage = qt_windows.CheckBox(
            "Off Background Image",      self.read_data("bgimage", True))
        self.openwritefolder = qt_windows.CheckBox(
            "Open write folder",         self.read_data("openfolder", True))

        self.writebutton = qt_windows.PushButton("Write", default=True, size=14)

        # LAYOUTS
        grid = QtWidgets.QGridLayout()
        boxv1 = QtWidgets.QVBoxLayout()

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

        boxv1.addLayout(grid)

        boxv1.addWidget(qt_windows.QHLine())
        boxv1.addWidget(self.convertvideo)
        boxv1.addWidget(self.blackbackground)
        boxv1.addWidget(self.offbackgroundimage)
        boxv1.addWidget(self.openwritefolder)
        boxv1.addWidget(qt_windows.QHLine())
        boxv1.addWidget(self.writebutton)

        self.setLayout(boxv1)

        # SIGNALS
        self.writebutton.clicked.connect(lambda: self.dump_json(self.settings))
        # self.writebutton.clicked.connect(lambda: self.close())

        # SCRIPTS
        flipbook_widget = None
        for w in hou.qt.mainWindow().children():
            if w.isWidgetType():
                if w.windowTitle()=="Write flipbook" and w.isVisible():
                    flipbook_widget = w

        if flipbook_widget:
            print("\nFlipbook Writer is already open\n")
            flipbook_widget.activateWindow()
        else:
            self.show()



    def eventFilter(self, source , event) -> bool:
        
        if event.type() == QtCore.QEvent.FocusIn:
            self.writebutton.setDefault(False)
        
        elif event.type() == QtCore.QEvent.KeyRelease and event.key() in [QtCore.Qt.Key_Return,QtCore.Qt.Key_Enter]:
            self.writebutton.setDefault(True)

        return super().eventFilter(source, event)

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

            newresx = max(round(int(resx)/2), 128)
            newresy = max(round(int(resy)/2), 128)

            self.resx.setText(str(newresx))
            self.resy.setText(str(newresy))
        else:
            x, y = item.split(" ")
            self.resx.setText(str(x))
            self.resy.setText(str(y))

    def setMenuItemFrameRange(self):
        item = self.sender().text()

        if item == "Global Frame Range":
            self.framestart.setText("$FSTART")
            self.frameend.setText("$FEND")
        elif item == "Playbar Frame Range":
            self.framestart.setText("$RFSTART")
            self.frameend.setText("$RFEND")

    def flipbooks_menu(self):
        names = self.flipbookNames(Path(hou.text.expandString(
            self.settings.get("fb_folder")).format(name=self.data.get("name"))))
        return names

    def get_tmp(self):
        hou_temp = Path(hou.text.expandString(self.settings.get("tmp_folder")))

        if hou_temp.exists():
            pass
        else:
            hou_temp.mkdir(parents=True, exist_ok=True)

        return hou_temp.as_posix()

    def dump_json(self, settingsjson):
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

        data_file = Path(hou_temp, self.settings.get("tmp_data")).as_posix()

        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.close()
        flipbook.start(settingsjson, data)

    def load_json(self, file):
        try:
            with open(file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def read_data(self, key, value):
        return self.data.get(key) if self.data.get(key) != None else value

    def flipbookNames(self,pfolder):
        folder = pfolder.parent
        files = [x.name for x in folder.iterdir() if x.is_dir()]
        return files
