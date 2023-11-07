from pathlib import Path
from importlib import reload
from re import search
from .utils import utils

import subprocess
import hou

reload(utils)

def start(settingsjson, datajson):
    # Parsing settings
    fb_name = settingsjson.get("fb_name")
    frame_padding = search(r"\$F\d+",fb_name)
    if not frame_padding:
        print("No frame padding like '$F4' in 'fb_name' found")
        return 0
    else:
        frame_padding = frame_padding[0]
        frame_padding_int = frame_padding.replace("$F","").zfill(2)

    fb_video_ext = settingsjson.get("fb_video_ext")
    fb_folder = hou.text.expandString(settingsjson.get("fb_folder"))
    data = datajson

    # Parsing data
    file_name = data.get("name")
    file_format = data.get("fileformat")
    file_resolution = tuple((int(data.get("resx")), int(data.get("resy"))))

    frame_start = int(data.get("framestart")) if not data.get(
        "framestart").startswith("$") else hou.hscriptExpression(data.get("framestart"))
    frame_end = int(data.get("frameend")) if not data.get("frameend").startswith(
        "$") else hou.hscriptExpression(data.get("frameend"))

    # Default path to write flipbook
    write_folder = Path(fb_folder.format(name=file_name))
    if write_folder.exists():
        pass
    else:
        write_folder.mkdir(parents=True, exist_ok=True)

    # Get newer folder version of flipbook
    write_folder_vers = [x.name for x in write_folder.iterdir() if x.is_dir()]
    write_folder_vers = write_folder_vers if len(write_folder_vers) > 0 else ['v000']

    # Get last version
    last_ver_str = sorted(write_folder_vers, reverse=True)[0][1:]
    ver_digit = int(last_ver_str)+1
    ver_padding = len(last_ver_str)
    ver_str = f"v{str(ver_digit).zfill(ver_padding)}"

    # Set output filename
    filename = fb_name.format(
        name=file_name, version=ver_str, fileformat=file_format)
    output_filepath = write_folder / ver_str / filename

    # Get Viewport
    viewport = utils.HouViewport()

    # Stash flipbook settings
    flipbook_options = viewport.flipbook_settings()

    # Maximize window to get better quality
    viewport.maximize_viewport()

    # Change background color
    if data.get("blackbg"):
        prev_color_scheme = viewport.colorScheme()
        viewport.colorScheme("dark")

    # Disable background image preview
    if data.get("bgimage"):
        viewport.displayBackgroundImage(False)

    # #Open dir
    if data.get("openfolder"):
        subprocess.Popen(['explorer', write_folder.as_uri()])

    # Correcting resolution for mpeg4 codec
    if data.get("convertvideo"):
        presx = file_resolution[0] if file_resolution[0] % 2 == 0 else file_resolution[0]-1
        presy = file_resolution[1] if file_resolution[1] % 2 == 0 else file_resolution[1]-1
        file_resolution = tuple((presx, presy))

    # #Flipbook Settings
    flipbook_options.output(output_filepath.as_posix())
    flipbook_options.useResolution(True)
    flipbook_options.resolution(file_resolution)
    flipbook_options.frameRange(tuple((frame_start, frame_end)))
    flipbook_options.appendFramesToCurrent(False)
    flipbook_options.beautyPassOnly(False)

    # Start Flipbook
    viewport.startFlipbook(flipbook_options)

    # Return pane size
    viewport.maximize_viewport(False)

    # Return color scheme
    if data.get("blackbg"):
        viewport.colorScheme(prev_color_scheme)

    # Return background image
    if data.get("bgimage"):
        viewport.displayBackgroundImage()
    
    if data.get("convertvideo"):
        fps = int(hou.fps())
        aspect = int(data.get("aspect"))
        resolution = f"{file_resolution[0]}x{file_resolution[1]}"
        start_frame = int(frame_start)

        ffmpeg = utils.FFmpeg(Path(__file__).parent / "ffmpeg.json",
                            Path(__file__).parent / "bin" / "ffmpeg.exe")

        input_files = output_filepath.as_posix().replace(frame_padding, f"%{frame_padding_int}d")
        output_video = (output_filepath.parent /
                        filename).as_posix().replace(f"{frame_padding}.{file_format}", fb_video_ext)

        ffmpeg.convert_to_video(fps=fps,
                                resolution=resolution,
                                aspect=file_resolution[0]/file_resolution[1]*aspect,
                                start_frame=start_frame,
                                input=input_files,
                                output=output_video,
                                delete_input=True)