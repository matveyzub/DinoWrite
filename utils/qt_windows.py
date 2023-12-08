import typing
from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from pathlib import Path
from importlib import reload

import PySide2.QtCore
import PySide2.QtWidgets

from . import utils
reload(utils)

styles = utils.StyleSheet((Path(__file__).parent / "stylesheets.json").as_posix())
Icons = utils.Icons()

#CONSTANT's
MAIN_FONT =   styles.get("main").get('font')
MAIN_SIZE =   max(styles.get("main").get('fontsize'),3)
TEXT_WEIGHT = {"normal": QtGui.QFont.Medium,"bold": QtGui.QFont.Bold}
COLORFUL_LABEL_COLORS = {"name":"#fa7960",
                        "version":"#f19e18",
                        "frame":"#04e762",
                        "extension":"#008bf8"}

if MAIN_FONT=="_custom_":
    id = QtGui.QFontDatabase.addApplicationFont((Path(__file__).parents[1] / "misc" / "font.ttf").as_posix())
    if id < 0:
        utils.logger("No font found in 'misc/font.ttf'")
        MAIN_FONT = "Arial"
    else:
        MAIN_FONT = QtGui.QFontDatabase.applicationFontFamilies(id)[0]

class Frame(QtWidgets.QFrame):
    """
    Stylized Frame
    """
    def __init__(self,background_color:str="#2d2d2d",border_radius:int=5,margins:int=1,parent=None) -> QtWidgets.QFrame:
        super().__init__(parent)

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setContentsMargins(margins,margins,margins,margins)
        self.setStyleSheet(f"background-color:{background_color};\
                            border-radius: {border_radius}px;")

class Label(QtWidgets.QLabel):
    """
    Simple Label with font,size and weight settings
    """
    def __init__(self,label:str="",font:str=MAIN_FONT,size:int=MAIN_SIZE-2,weight:str="normal",parent=None) -> QtWidgets.QLabel:
        super().__init__(parent)

        self.setText(label)
        self.setFont(QtGui.QFont(font,size,weight=TEXT_WEIGHT[weight]))
        self.setStyleSheet(styles.get("label"))

class HBLabel(Label):
    """
    Houdini bold , right-align style label for lineedits
    """
    def __init__(self,label:str="",font:str=MAIN_FONT,size:int=MAIN_SIZE,weight:str="bold",parent=None) -> QtWidgets.QLabel:
        super().__init__(label=label,font=font,size=size-1,weight=weight,parent=parent)
        self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

class ColorfulLabel(Label):
    """Colorful label for indicating user inputs

    Args:
        Args should be in %2 to match type like {label} - {color}

    Returns:
        Label widget with colored strings
    """
    def __init__(self,labels_list:list=["label1","#ff0033"," - ","#00ff3c","label2","#0073ff"],font=MAIN_FONT,size=MAIN_SIZE,parent=None) -> QtWidgets.QLabel:
        super().__init__(font=font,size=size,parent=parent)
        self.update(labels_list)

    def update(self,labels_list):
        template_string = "<font color='{color}')>{label}</font>"
        
        if len(labels_list)%2!=0:
            print("bad args")
            return 0
        
        string_to_set = ""
        labels = labels_list[0::2]
        colors = labels_list[1::2]
        for i in range(len(labels)):
            string_to_set+=template_string.format(label=labels[i],color=colors[i])

        self.setText(string_to_set)

class LineEdit(QtWidgets.QLineEdit):
    """
    Simple LineEdit with func of making bold like Houdini
    """
    def __init__(self,spawntext:str="",hint:str=None,font:str=MAIN_FONT,size:int=MAIN_SIZE,parent=None) -> QtWidgets.QLineEdit:
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
    def __init__(self,icon:str=None,title:str="",menu:list=[],callback:list=None,font:str=MAIN_FONT,size:int=MAIN_SIZE,parent=None) -> QtWidgets.QPushButton:
        super().__init__(parent)

        self.setText(title if not icon else "")
        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("button"))
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        buttonsize = 25
        self.setFixedSize(QtCore.QSize(buttonsize,buttonsize))

        self.setCheckable(True)
        self.setChecked(False)

        if icon:
            self.setIcon(QtGui.QIcon((Path(__file__).parent / "icons" / icon).as_posix()))

        self.menu = QtWidgets.QMenu()
        self.menu.setFont(QtGui.QFont(font,size))
        self.menu.setStyleSheet(styles.get("menu"))
        self.menu.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.setMenu(self.menu)

        if len(menu)==0:
            menu.append("No folders found")

        for action_name in menu:
            if action_name=="---":
                self.menu.addSeparator()
            elif action_name=="50%": # bad coding :) but i'm lazy
                pixmap = Icons.get("dino_knife_cut.svg",type="Path")
                iconpixmap = QtGui.QPixmap(pixmap)
                iconpixmap = iconpixmap.scaled(25, 25, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                icon = QtGui.QIcon(iconpixmap)

                action = QtWidgets.QAction(icon,action_name,self)

                if action_name!="No folders found":
                    action.triggered.connect(callback)
                else:
                    pass
                
                self.menu.addAction(action)
            else:
                action = QtWidgets.QAction(action_name,self)

                if action_name!="No folders found":
                    action.triggered.connect(callback)
                else:
                    pass
                
                self.menu.addAction(action)

class CheckBox(QtWidgets.QCheckBox):
    """
    Simple CheckBox
    """
    def __init__(self,label:str="",default:bool=False,font:str=MAIN_FONT,size:int=MAIN_SIZE,parent=None) -> QtWidgets.QCheckBox:
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
    def __init__(self,items:list=[],item:str=None,font:str=MAIN_FONT,size:int=MAIN_SIZE,parent=None) -> QtWidgets.QComboBox:
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
    def __init__(self,label:str="",font:str=MAIN_FONT,size:int=MAIN_SIZE,default:bool=False,parent=None) -> QtWidgets.QPushButton:
        super().__init__(parent)

        self.setText(label)
        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("mainbutton"))
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setDefault(default)

class HIcon(QtWidgets.QLabel):

    def __init__(self,iconpath:str="photo.svg",size:int=30,parent=None) -> QtWidgets.QLabel:
        super().__init__(parent)

        iconpixmap = QtGui.QPixmap(iconpath)
        iconpixmap = iconpixmap.scaled(size, size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.setPixmap(iconpixmap)
        self.setFixedWidth(size)

class HSeparator(QtWidgets.QFrame):
    """
    Horizontal Separator (line)
    """
    def __init__(self,parent=None) -> QtWidgets.QFrame:
        super().__init__(parent)

        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setLineWidth(1)

class HWidget(QtWidgets.QHBoxLayout):
    """
    Procedural layout which align all input widgets to the left
    """

    def __init__(self, widgets:list=[],parent=None) -> QtWidgets.QHBoxLayout:
        super().__init__(parent)

        self.setAlignment(QtCore.Qt.AlignLeft)
        
        for w in widgets:
            self.addWidget(w)