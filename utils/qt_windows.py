from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore
from pathlib import Path
from importlib import reload

from . import utils
reload(utils)

styles = utils.StyleSheet((Path(__file__).parents[1] / "stylesheets.json").as_posix())
main_font =     styles.get("main")['font']
main_fontsize = styles.get("main")['fontsize']

class MainLabel(QtWidgets.QLabel):
    """
    Label
    """
    def __init__(self,label="",font=main_font,size=main_fontsize,parent=None) -> QtWidgets.QWidget:
        super().__init__(parent)

        self.setText(label)
        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("label"))

class LineEdit(QtWidgets.QLineEdit):
    """
    qlineedit
    """
    def __init__(self,spawntext="",hint="",font=main_font,size=main_fontsize,parent=None) -> QtWidgets.QWidget:
        super().__init__(parent)

        self.setText(spawntext)
        self.setFont(QtGui.QFont(font,size,))
        self.setStyleSheet(styles.get("lineedit"))

        self.textChanged.connect(lambda: self.makeBold(spawntext,font,size))

    def makeBold(self,spawntext,font,size):
        if spawntext!=self.text():
            self.setFont(QtGui.QFont(font,max(size-1,1),weight=QtGui.QFont.Bold))
        else:
            self.setFont(QtGui.QFont(font,size,weight=QtGui.QFont.Normal))

class DropDownButton(QtWidgets.QPushButton):
    """
    Button which dropdown context menu with a bunch of actions

    Args:
        QtWidgets (_type_): _description_
    """
    def __init__(self,icon=None,title="",menu=[],callback=None,font=main_font,size=main_fontsize,parent=None) -> QtWidgets.QWidget:
        super().__init__(parent)

        self.setText(title if not icon else "")
        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("button"))
        self.setCheckable(True)
        self.setChecked(False)

        if icon:
            self.setIcon(QtGui.QIcon((Path(__file__).parent / "icons" / icon).as_posix()))

        self.menu = QtWidgets.QMenu()
        self.menu.setFont(QtGui.QFont(font,size))
        self.menu.setStyleSheet(styles.get("menu"))
        
        self.setMenu(self.menu)
        self.setFixedSize(QtCore.QSize(28,25))

        for action_name in menu:
            if action_name!="---":
                action = QtWidgets.QAction(action_name,self)
                action.triggered.connect(callback)
                self.menu.addAction(action)
            else:
                self.menu.addSeparator()

class CheckBox(QtWidgets.QCheckBox):
    """
    CheckBox
    """
    def __init__(self,label="",default=False,font=main_font,size=main_fontsize,parent=None) -> QtWidgets.QWidget:
        super().__init__(parent)
        
        self.setText(label)
        self.setFont(QtGui.QFont(font,size))
        # self.setStyleSheet(styles.get("checkbox"))

        self.setChecked(default)

        self.clicked.connect(lambda: self.makeBold(default,font,size))

    def makeBold(self,state,font,size):
        if state!=self.isChecked():
            self.setFont(QtGui.QFont(font,size,weight=QtGui.QFont.Bold))
        else:
            self.setFont(QtGui.QFont(font,size,weight=QtGui.QFont.Normal))

class ComboBox(QtWidgets.QComboBox):
    """
    ComboBox
    """
    def __init__(self,items=[],item=None,font=main_font,size=main_fontsize,parent=None) -> QtWidgets.QWidget:
        super().__init__(parent)

        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("combobox"))

        self.insertItems(0,items)
        
        if item:
            self.setCurrentText(item)

        state = self.currentIndex()

        self.currentIndexChanged.connect(lambda: self.makeBold(state,font,size))

    def makeBold(self,state,font,size):
        if state!=self.currentIndex():
            self.setFont(QtGui.QFont(font,size,weight=QtGui.QFont.Bold))
        else:
            self.setFont(QtGui.QFont(font,size,weight=QtGui.QFont.Normal))

class PushButton(QtWidgets.QPushButton):
    """
    Button
    """
    def __init__(self,label="",font=main_font,size=main_fontsize,default=False,parent=None) -> QtWidgets.QWidget:
        super().__init__(parent)

        self.setText(label)
        self.setFont(QtGui.QFont(font,size))
        self.setStyleSheet(styles.get("button"))

        self.setDefault(default)


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()

        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)