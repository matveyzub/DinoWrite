from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from pathlib import Path
from importlib import reload

from . import utils
reload(utils)

styles = utils.StyleSheet((Path(__file__).parent / "stylesheets.json").as_posix())
Icons = utils.Icons()

#CONSTANTs
MAIN_FONT =   styles.get("main").get('font')
MAIN_SIZE =   max(styles.get("main").get('fontsize'),3)
TEXT_WEIGHT = {"normal": QFont.Medium,"bold": QFont.Bold}

if MAIN_FONT=="_custom_":
    id = QFontDatabase.addApplicationFont((Path(__file__).parents[1] / "misc" / "font.ttf").as_posix())
    if id < 0:
        utils.logger("No font found in 'misc/font.ttf'")
        MAIN_FONT = "Arial"
    else:
        MAIN_FONT = QFontDatabase.applicationFontFamilies(id)[0]

def Completer(array:list) -> QCompleter: 
    completer = QCompleter(array)
    completer.setCaseSensitivity(Qt.CaseInsensitive)
    completer.setCompletionMode(QCompleter.InlineCompletion)
    return completer

class Frame(QFrame):
    """
    Stylized Frame
    """
    def __init__(self,
                background_color:str="#2d2d2d",
                border_radius:int=5,
                margins:int=1,
                parent=None) -> QFrame:
        
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setContentsMargins(margins,margins,margins,margins)
        self.setStyleSheet(f"background-color:{background_color};\
                            border-radius: {border_radius}px;")

class Label(QLabel):
    """
    Simple Label with font,size and weight settings
    """
    def __init__(self,
                label:str="",
                font:str=MAIN_FONT,
                size:int=MAIN_SIZE-2,
                weight:str="normal",
                parent=None) -> QLabel:
        
        super().__init__(parent)
        self.setText(label)
        self.setFont(QFont(font,size,weight=TEXT_WEIGHT[weight]))
        self.setStyleSheet(styles.get("label"))

class HBLabel(Label):
    """
    Houdini bold , right-align style label for lineedits
    """
    def __init__(self,
                label:str="",
                font:str=MAIN_FONT,
                size:int=MAIN_SIZE,
                weight:str="bold",
                parent=None) -> QLabel:

        super().__init__(label=label,font=font,size=size-1,weight=weight,parent=parent)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

class ColorfulLabel(Label):
    """Colorful label for indicating user inputs

    Args:
        Args should be in %2 to match type like {label} - {color}

    Returns:
        Label widget with colored strings
    """
    def __init__(self,
                labels_list:list=["label1","#ff0033"," - ","#00ff3c","label2","#0073ff"],
                font=MAIN_FONT,
                size=MAIN_SIZE,
                parent=None) -> QLabel:
        
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

class LineEdit(QLineEdit):
    """
    Simple LineEdit with func of making bold like Houdini
    """
    def __init__(self,
                spawntext:str="",
                hint:str=None,
                font:str=MAIN_FONT,
                size:int=MAIN_SIZE,
                parent=None) -> QLineEdit:
        
        super().__init__(parent)
        self.setText(spawntext)
        self.setFont(QFont(font,size,))
        self.setStyleSheet(styles.get("lineedit"))

        if hint:
            self.setPlaceholderText(hint)

        self.editingFinished.connect(lambda: self.makeBold(spawntext,font,size))

    def makeBold(self,spawntext,font,size):
        if spawntext!=self.text():
            self.setFont(QFont(font,size-1,weight=TEXT_WEIGHT["bold"]))
        else:
            self.setFont(QFont(font,size,weight=TEXT_WEIGHT["normal"]))

class DropDownButton(QPushButton):
    """
    Button which dropdown context menu with a bunch of actions
    """
    def __init__(self,icon:str=None,
                title:str="",
                menu:list=[],
                callback:list=None,
                font:str=MAIN_FONT,
                size:int=MAIN_SIZE,
                parent=None) -> QPushButton:

        super().__init__(parent)

        self.setText(title if not icon else "")
        self.setFont(QFont(font,size))
        self.setStyleSheet(styles.get("button"))
        self.setFocusPolicy(Qt.ClickFocus)
        buttonsize = 25
        self.setFixedSize(QSize(buttonsize,buttonsize))

        self.setCheckable(True)
        self.setChecked(False)

        if icon:
            self.setIcon(QIcon((Path(__file__).parent / "icons" / icon).as_posix()))

        self.menu = QMenu()
        self.menu.setFont(QFont(font,size))
        self.menu.setStyleSheet(styles.get("menu"))
        self.menu.setLayoutDirection(Qt.RightToLeft)
        self.menu.setCursor(Qt.PointingHandCursor)
        self.setMenu(self.menu)

        if len(menu)==0:
            menu.append("No folders found")

        for action_name in menu:
            if action_name=="---":
                self.menu.addSeparator()
            elif action_name=="1/2": # bad coding :) but i'm lazy
                pixmap = Icons.get("dino_knife_cut.svg",type="Path")
                iconpixmap = QPixmap(pixmap)
                iconpixmap = iconpixmap.scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon = QIcon(iconpixmap)

                action = QAction(icon,action_name,self)

                if action_name!="No folders found":
                    action.triggered.connect(callback)
                else:
                    pass
                
                self.menu.addAction(action)
            else:
                action = QAction(action_name,self)

                if action_name!="No folders found":
                    action.triggered.connect(callback)
                else:
                    pass
                
                self.menu.addAction(action)

class CheckBox(QCheckBox):
    """
    Simple CheckBox
    """
    def __init__(self,
                label:str="",
                default:bool=False,
                font:str=MAIN_FONT,
                size:int=MAIN_SIZE,
                parent=None) -> QCheckBox:
        
        super().__init__(parent)
        
        self.setText(label)
        self.setFont(QFont(font,size))
        self.setStyleSheet(styles.get("checkbox"))
        self.setChecked(default)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setCursor(Qt.PointingHandCursor)

        self.clicked.connect(lambda: self.makeBold(default,font,size))

    def makeBold(self,state,font,size):
        if state!=self.isChecked():
            self.setFont(QFont(font,size,weight=TEXT_WEIGHT["bold"]))
        else:
            self.setFont(QFont(font,size,weight=TEXT_WEIGHT["normal"]))

class ComboBox(QComboBox):
    """
    Simple ComboBox
    """
    def __init__(self,
                items:list=[],
                item:str=None,
                font:str=MAIN_FONT,
                size:int=MAIN_SIZE,
                parent=None) -> QComboBox:
        
        super().__init__(parent)

        self.setFont(QFont(font,size))
        self.setStyleSheet(styles.get("combobox"))
        self.setFocusPolicy(Qt.ClickFocus)
        self.insertItems(0,items)

        if item:
            self.setCurrentText(item)
        state = self.currentIndex()

        self.currentIndexChanged.connect(lambda: self.makeBold(state,font,size))

    def makeBold(self,state,font,size):
        if state!=self.currentIndex():
            self.setFont(QFont(font,size,weight=TEXT_WEIGHT["bold"]))
        else:
            self.setFont(QFont(font,size,weight=TEXT_WEIGHT["normal"]))

class PushButton(QPushButton):
    """
    Button
    """
    def __init__(self,
                label:str="",
                font:str=MAIN_FONT,
                size:int=MAIN_SIZE,
                default:bool=False,
                parent=None) -> QPushButton:
        
        super().__init__(parent)

        self.setText(label)
        self.setFont(QFont(font,size))
        self.setStyleSheet(styles.get("mainbutton"))
        self.setFocusPolicy(Qt.ClickFocus)
        self.setDefault(default)

class HIcon(QLabel):

    def __init__(self,iconpath:str="photo.svg",size:int=30,parent=None) -> QLabel:
        super().__init__(parent)

        iconpixmap = QPixmap(iconpath)
        iconpixmap = iconpixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(iconpixmap)
        self.setFixedWidth(size)

class HSeparator(QFrame):
    """
    Horizontal Separator (line)
    """
    def __init__(self,parent=None) -> QFrame:
        super().__init__(parent)

        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)

class HLayout(QHBoxLayout):
    """
    Procedural layout which align all input widgets to the left
    """

    def __init__(self, widgets:list=[],align=Qt.AlignLeft,parent=None) -> QHBoxLayout:
        super().__init__(parent)

        if align:
            self.setAlignment(align)
        
        for w in widgets:
            self.addWidget(w)