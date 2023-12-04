from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from pathlib import Path
from importlib import reload

from . import utils
reload(utils)

styles = utils.StyleSheet((Path(__file__).parent / "stylesheets.json").as_posix())

#CONSTANT's
MAIN_FONT =   styles.get("main").get('font')
MAIN_SIZE =   max(styles.get("main").get('fontsize'),3)
TEXT_WEIGHT = {"normal": QtGui.QFont.Medium,"bold": QtGui.QFont.Bold}
COLORFUL_LABEL_COLORS = {"name":"#74e796",
                        "version":"#e3e774",
                        "frame":"#74c4e7",
                        "extension":"#e77a74"}

if MAIN_FONT=="_custom_":
    id = QtGui.QFontDatabase.addApplicationFont((Path(__file__).parents[1] / "misc" / "font.ttf").as_posix())
    if id < 0:
        utils.logger("No font found in 'misc/font.ttf'")
        MAIN_FONT = "Arial"
    else:
        MAIN_FONT = QtGui.QFontDatabase.applicationFontFamilies(id)[0]

class Label(QtWidgets.QLabel):
    """
    Simple Label with font,size and weight settings
    """
    def __init__(self,label="",font=MAIN_FONT,size=MAIN_SIZE-2,weight="normal",parent=None) -> QtWidgets.QLabel:
        super().__init__(parent)

        self.setText(label)
        self.setFont(QtGui.QFont(font,size,weight=TEXT_WEIGHT[weight]))
        self.setStyleSheet(styles.get("label"))

class HBLabel(QtWidgets.QLabel):
    """
    Houdini bold , right-align style label for lineedits
    """
    def __init__(self,label="",font=MAIN_FONT,size=MAIN_SIZE,weight="bold",parent=None) -> QtWidgets.QLabel:
        super().__init__(parent)

        self.setText(label)
        self.setFont(QtGui.QFont(font,size,weight=TEXT_WEIGHT[weight]))
        self.setStyleSheet(styles.get("label"))
        self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

class ColorfulLabel(QtWidgets.QWidget):
    """
    Colorful label for indicating user inputs
    """
    def __init__(self,name:str,version:str,frame:str,extension:str,font=MAIN_FONT,size=MAIN_SIZE,parent=None) -> QtWidgets.QWidget:
        super().__init__(parent)

        self.filename = Label('',font=font,size=size,weight="normal")
        self.separator = " -"
        self.filename.setText(f"{self.colorText(item=name,color='name')}{self.separator} \
                                {self.colorText(item=version,color='version')}{self.separator} \
                                {self.colorText(item=frame,color='frame')}{self.separator} \
                                {self.colorText(item=extension,color='extension')}")
        self.name = name
        self.version = version
        self.frame = frame
        self.extension = extension

        boxh = QtWidgets.QHBoxLayout()
        boxh.addWidget(self.filename)
        boxh.setAlignment(QtCore.Qt.AlignCenter)
        boxh.setContentsMargins(0,0,0,0)
        self.setLayout(boxh)

    def colorText(self,item:str,color:str):
        color = COLORFUL_LABEL_COLORS.get(color)
        return f"<font color='{color}')>{item}</font>"

    def update(self,name=None,version=None,frame=None,extension=None):
        self.filename.setText(f"{self.colorText(item=name if name else self.name,color='name')}{self.separator}\
                                {self.colorText(item=version if version else self.version,color='version')}{self.separator}\
                                {self.colorText(item=frame if frame else self.frame,color='frame')}{self.separator}\
                                {self.colorText(item=extension if extension else self.extension,color='extension')}")

class LineEdit(QtWidgets.QLineEdit):
    """
    Simple LineEdit with func of making bold like Houdini
    """
    def __init__(self,spawntext="",hint=None,font=MAIN_FONT,size=MAIN_SIZE,parent=None) -> QtWidgets.QLineEdit:
        super().__init__(parent)

        self.setText(spawntext)
        self.setFont(QtGui.QFont(font,size,))
        self.setStyleSheet(styles.get("lineedit"))

        if hint:
            self.setPlaceholderText(hint)

        self.editingFinished.connect(lambda: self.makeBold(spawntext,font,size))

    def makeBold(self,spawntext,font,size):
        if spawntext!=self.text():
            self.setFont(QtGui.QFont(font,size-1,weight=TEXT_WEIGHT["bold"]))
        else:
            self.setFont(QtGui.QFont(font,size,weight=TEXT_WEIGHT["normal"]))

class DropDownButton(QtWidgets.QPushButton):
    """
    Button which dropdown context menu with a bunch of actions
    """
    def __init__(self,icon=None,title="",menu=[],callback=None,font=MAIN_FONT,size=MAIN_SIZE,parent=None) -> QtWidgets.QPushButton:
        super().__init__(parent)

        self.setText(title if not icon else "")
        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("button"))
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.setCheckable(True)
        self.setChecked(False)

        if icon:
            self.setIcon(QtGui.QIcon((Path(__file__).parent / "icons" / icon).as_posix()))

        self.menu = QtWidgets.QMenu()
        self.menu.setFont(QtGui.QFont(font,size))
        self.menu.setStyleSheet(styles.get("menu"))

        self.setMenu(self.menu)
        self.setFixedSize(QtCore.QSize(28,25))

        if len(menu)==0:
            menu.append("No folders found")

        for action_name in menu:
            if action_name!="---":
                action = QtWidgets.QAction(action_name,self)

                if action_name!="No folders found":
                    action.triggered.connect(callback)
                else:
                    pass
                
                self.menu.addAction(action)
            else:
                self.menu.addSeparator()

class CheckBox(QtWidgets.QCheckBox):
    """
    Simple CheckBox
    """
    def __init__(self,label="",default=False,font=MAIN_FONT,size=MAIN_SIZE,parent=None) -> QtWidgets.QCheckBox:
        super().__init__(parent)
        
        self.setText(label)
        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("checkbox"))
        self.setChecked(default)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.clicked.connect(lambda: self.makeBold(default,font,size))

    def makeBold(self,state,font,size):
        if state!=self.isChecked():
            self.setFont(QtGui.QFont(font,size,weight=TEXT_WEIGHT["bold"]))
        else:
            self.setFont(QtGui.QFont(font,size,weight=TEXT_WEIGHT["normal"]))

class ComboBox(QtWidgets.QComboBox):
    """
    Simple ComboBox
    """
    def __init__(self,items=[],item=None,font=MAIN_FONT,size=MAIN_SIZE,parent=None) -> QtWidgets.QComboBox:
        super().__init__(parent)

        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("combobox"))
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.insertItems(0,items)

        if item:
            self.setCurrentText(item)
        state = self.currentIndex()

        self.currentIndexChanged.connect(lambda: self.makeBold(state,font,size))

    def makeBold(self,state,font,size):
        if state!=self.currentIndex():
            self.setFont(QtGui.QFont(font,size,weight=TEXT_WEIGHT["bold"]))
        else:
            self.setFont(QtGui.QFont(font,size,weight=TEXT_WEIGHT["normal"]))

class PushButton(QtWidgets.QPushButton):
    """
    Button
    """
    def __init__(self,label="",font=MAIN_FONT,size=MAIN_SIZE,default=False,parent=None) -> QtWidgets.QPushButton:
        super().__init__(parent)

        self.setText(label)
        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("button"))
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setDefault(default)

class HSeparator(QtWidgets.QFrame):
    """
    Horizontal Separator (line)
    """
    def __init__(self,parent=None) -> QtWidgets.QFrame:
        super().__init__(parent)

        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)