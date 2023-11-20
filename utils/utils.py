import hou
import json
from pathlib import Path
import subprocess
from os import environ as osenviron

def logger(message,len=40):
    print(" Flipbook Writer ".center(len,"-"))
    print(message)
    print(f"{'-'*len}")

class StyleSheet:
    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def get(self, element: str) -> str:
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
    def __init__(self, config_path: str, bin: str,cmd: dict) -> None:
        
        self.config_path = config_path
        self.cmdvar = cmd

        if not config_path and not cmd:
            logger("No config path or cmd set")
            return 0

        path = osenviron["PATH"]
        osenviron["PATH"] = f"{bin};{path}"

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
            subprocess.run(ffmpeg_cmd, check=True, shell=True)
        except subprocess.CalledProcessError as e:
            logger(f"Error occured during subprocces run ffmpeg command\n\nErrorLog:\n{e}")
            return 0

        if len(files) != 0 and delete_input:
            for file in files:
                file.unlink()

class HouViewport:
    def __init__(self,kwargs) -> None:
        self.viewport_panetab = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)

        if hou.ui.paneTabOfType(hou.paneTabType.SceneViewer,1):
            self.viewport_panetab = kwargs.get("pane")

        self.viewport_pane = self.viewport_panetab.pane()
        self.settings = self.viewport_panetab.curViewport().settings()

    def startFlipbook(self,options):
        self.viewport_panetab.flipbook(self.viewport_panetab.curViewport(), options)

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
        viewport = self.viewport_panetab.curViewport()
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
        viewport = self.viewport_panetab.curViewport()
        camera = viewport.camera()
        if camera:
            aspect = camera.evalParm("aspect")
        else:
            logger("No Camera Found in viewport\nReturning aspect 1")
            aspect = 1
        return aspect

    def flipbook_settings(self):
        return self.viewport_panetab.flipbookSettings().stash()