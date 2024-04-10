import hou
import json
from pathlib import Path
import subprocess
from os import environ as osenviron
import random
import shutil
from pxr import Sdf,Usd

from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

def logger(message:str,length=70) -> None:
    """Simple console logger

    Args:
        message (str): Message to print in console
        length (str, optional): Length of stroke. Defaults to "auto" leads to set length to a length of message.
    """
    if length=="auto":
        length = len(message)
        print(" DinoWriter ".center(length,"-"))
        print(message)
        print(f"{'-'*length}")
    else:
        print(" DinoWriter ".center(length,"-"))
        print(message)
        print(f"{'-'*length}")

def hmsg(message:str,buttons=("Sorry,Dino!",),level="message") -> None:
    """Houdini message window 

    Args:
        message (str): Message to display
        buttons (tuple, optional): Buttons to provide to user. Defaults to ("Sorry,Dino!",).
        level (str, optional): Importance level of message. Defaults to "message" , available "warning" and "error".
    """
    levels = {
        "message": hou.severityType.Message,
        "warning": hou.severityType.Warning,
        "error": hou.severityType.Error
    }

    if message:
        hou.ui.displayMessage(message,buttons=buttons,severity=levels[level],title="DinoWrite say")
    else:
        logger("No message set in hsmg function")

class StyleSheet:
    """Parsing info from stylesheet json file
    """
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def get(self, element: str) -> str:
        """Get element from stylesheet file

        Args:
            element (str): Name of the element

        Returns:
            str: Stylesheet style string
        """
        data = {}
        with open(self.config_path) as theme:
            data = json.load(theme)

        if element != "main":
            label_style = data[element]
            style = ""
            for i in label_style:
                data = label_style[i]
                settings = ""
                for j in data:
                    settings += j
                style += f"{i}{ {settings} }".replace("'", "")
            return style
        else:
            return data[element]

class FFmpeg:
    """Wrapper around ffmpeg
    """
    def __init__(self, config_path: str, bin: str,cmd: dict) -> None:
        
        self.config_path = config_path
        self.cmdvar = cmd
        system_os = hou.getenv("OS")

        if not config_path and not cmd:
            logger("No config path or cmd set")

        # Check for ffmpeg availability in system envs on different os (i believe)
        if system_os=="Windows_NT":
            if Path(bin).exists():
                path = osenviron["PATH"]
                osenviron["PATH"] = f"{bin};{path}"
            elif shutil.which("ffmpeg"):
                pass
            else:
                hmsg(f"No ffmpeg found in system PATH env or in {bin}")
        elif shutil.which("ffmpeg"):
            pass
        else:
            hmsg(f"No ffmpeg found in system PATH env")

    def cmd(self, fps=24, resolution="1920x1080", aspect=1, start_frame=1001, input="", output="") -> list:

        if input == "" or output == "":
            logger("No input or output set")
            return 0

        commands = []
        if not self.cmdvar:
            data = {}
            with open(self.config_path) as cmd:
                data = json.load(cmd)

            for key in data['cmd']:
                nkey = key.format(fps=fps, resolution=resolution, aspect=aspect,
                                start_frame=start_frame, input=input, output=output)
                commands += nkey.split(" ")
        else:
            for key in self.cmdvar:
                nkey = key.format(fps=fps, resolution=resolution, aspect=aspect,
                                start_frame=start_frame, input=input, output=output)
                commands += nkey.split(" ")

        return commands

    def convert_to_video(self, fps=24, resolution="1920x1080", aspect=1, start_frame=1001, input="", output="", delete_input=False):
        ffmpeg_cmd = self.cmd(fps=fps, resolution=resolution, aspect=aspect,
                            start_frame=start_frame, input=input, output=output)
        
        folder = Path(input).parent
        if folder.exists():
            files = [x for x in folder.iterdir()]
        else:
            files = []

        try:
            # subprocess.run(ffmpeg_cmd, check=True, shell=True)
            subprocess.run(ffmpeg_cmd, check=True)
        except subprocess.CalledProcessError as e:
            logger(f"Error occured during subprocces run ffmpeg command\n\nErrorLog:\n{e}")
            return 0

        if len(files) != 0 and delete_input:
            for file in files:
                file.unlink()

class HouViewport:
    def __init__(self,kwargs) -> None:
        self.viewport_panetab = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)

        if not self.viewport_panetab.isCurrentTab():
            logger("Starting the tool from a shelf leads to the recording of a flipbook from the first SceneViewer that comes across")
            self.viewport_panetab.setIsCurrentTab()

        if hou.ui.paneTabOfType(hou.paneTabType.SceneViewer,1):
            paneTab = kwargs.get("pane")
            if paneTab and paneTab.type() == hou.paneTabType.SceneViewer:
                self.viewport_panetab = paneTab
            else:
                logger("Multiple viewers detected!\nYou can select a viewer by executing the tool from the desired")

        self.viewport_pane = self.viewport_panetab.pane()
        self.settings = self.viewport_panetab.curViewport().settings()

    def startFlipbook(self,options):
        float_fullscreen=False
        float_panetab = ""
        if self.viewport_panetab.isFloating():
            float_panetab = self.viewport_panetab.floatingPanel()
            float_fullscreen = float_panetab.isFullscreen()
            float_panetab.setIsFullscreen(True)

        self.viewport_panetab.flipbook(self.viewport_panetab.curViewport(), options)

        if self.viewport_panetab.isFloating():
            float_panetab.setIsFullscreen(float_fullscreen)

    def getPaneTab(self):
        return self.viewport_panetab

    def maximize_viewport(self,type=True):
        self.viewport_pane.setIsMaximized(type)

    def colorScheme(self,color=None):

        scheme = {  "dark":hou.viewportColorScheme.Dark,
                    "grey":hou.viewportColorScheme.Grey,
                    "light":hou.viewportColorScheme.Light}

        if not color:
            return [i for i in scheme if scheme[i]==self.settings.colorScheme()][0]
        else:
            self.settings.setColorScheme(scheme[color])

    def displayBackgroundImage(self,type=True):
        self.settings.setDisplayBackgroundImage(type)

    def cameraResolution(self):
        network = self.viewport_panetab.pwd().childTypeCategory().name()
        viewport = self.viewport_panetab.curViewport()

        if network=="Lop":

            stage = self.viewport_panetab.stage()
            render_prims = [p for p in stage.Traverse() if p.GetTypeName()=="RenderSettings"]
            if len(render_prims)==0:
                size = viewport.size()
                resx = size[2]
                resy = size[3]
                
            elif len(render_prims)>0:
                if len(render_prims)>1:
                    logger("Multiple rendersettings prims detected!\nResolution will be taken from the first alphabetically ordered prim")
                render_prim = render_prims[0]
                resolution = render_prim.GetProperty("resolution").Get()
                resx = resolution[0]
                resy = resolution[1]
        
        else: #proccess obj and sops
            
            camera = viewport.camera()
            if camera:
                resx = camera.evalParm("resx")
                resy = camera.evalParm("resy")
            else:
                logger("No Camera Found in viewport\nReturning resolution from viewport size")
                size = viewport.size()
                resx = size[2]
                resy = size[3]
                
            
        return tuple((resx, resy))
    
    def cameraPixelAspect(self):
        network = self.viewport_panetab.pwd().childTypeCategory().name()
        viewport = self.viewport_panetab.curViewport()

        if network=="Lop":

            stage = self.viewport_panetab.stage()
            render_prims = [p for p in stage.Traverse() if p.GetTypeName()=="RenderSettings"]
            if len(render_prims)==0:
                aspect = 1
            elif len(render_prims)>0:
                render_prim = render_prims[0]
                aspect = render_prim.GetProperty("pixelAspectRatio").Get()
        
        else: #procces obj and sops

            camera = viewport.camera()
            if camera:
                aspect = camera.evalParm("aspect")
            else:
                # logger("No Camera Found in viewport\nReturning aspect 1")
                aspect = 1
        
        
        return aspect

    def cameraName(self):
        viewport = self.viewport_panetab.curViewport()
        camera_path = viewport.cameraPath()
        if camera_path=="":        
            return "Viewport Default Camera"
        else:
            return camera_path.split("/")[-1]
    
    def flipbook_settings(self):
        return self.viewport_panetab.flipbookSettings().stash()

class FileParser:
    def __init__(self) -> None:
        settings_file = (Path(__file__).parents[1] / "settings.json").as_posix()
        data = {}
        with open(settings_file) as f:
            data = json.load(f)
        self.paths = data.get("paths")

    def getVersion(self,flipbook_name:str) -> str:
        fb_folder = Path(hou.text.expandString(self.paths.get("fb_folder")).format(name=flipbook_name)).resolve()
        if fb_folder.exists() and len(flipbook_name)!=0:
            write_folder_vers = [x.name for x in fb_folder.iterdir() if x.is_dir()]
            write_folder_vers = write_folder_vers if len(write_folder_vers) > 0 else ['v000']
            last_ver_str = sorted(write_folder_vers)[-1][1:]
            ver_digit = int(last_ver_str)+1
            ver_padding = len(last_ver_str)
            ver_str = f"v{str(ver_digit).zfill(ver_padding)}"
        else:
            ver_str = "v001"
        return ver_str

class Icons:
    def __init__(self) -> None:
        self.iconfolder = Path(__file__).parents[1] / "icons"

    def get(self,name:str,type:str="Icon") -> QIcon:
        iconpath = Path(self.iconfolder) / name
        if not iconpath.exists():
            logger(f"No icon found:\n{iconpath.as_posix()}")
        else:
            if type=="Icon":
                return QIcon(iconpath.as_posix())
            elif type=="Path":
                return iconpath.as_posix()

    def getRandom(self,prefix="app",type="Icon"):
        iconpath = Path(self.iconfolder)
        icons = [x for x in iconpath.iterdir() if x.stem.startswith(prefix)]
        
        if len(icons)==0:
            logger(f"No files found with current prefix: {prefix}")
            return QIcon()
        else:
            icon = (random.choice(icons)).as_posix()
            if type=="Icon":
                return QIcon(icon)
            elif type=="Path":
                return icon