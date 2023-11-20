
Write flipbooks to disk easily

This is a fully Python tool that allows you to write flipbooks in Houdini

## Features
---
 - Open source with comprehensive explanations
 - A lot of customization available for the UI and settings
 - Keeping track of previous settings
 - Folders are automatically versioned
 - Enlarge the viewport window to improve quality
 - Support multiple viewports
 - Displaying existing flipbooks (can grab their name)
 - Grabs resolution from camera or divides it in half
 - Convert the sequence to video using FFmpeg
 - Opening the writing folder before flipbook is done 
 - A bunch of tips and tricks that I used in my workflow
 - Custom metadata
## Tips
---
There are a bunch of little tips that I use in my daily workflow to make it easier and more readable.

1. Off background image used when working with film footage and dealing with shot timing. So later, you can easily merge your flipbooks with shot source footage.  
2. Turning on the black background provides a little improvement when merging with the source.  
3. Using version namespace in the file name allows you to see your flipbook version easily in Nuke without going inside the read node. Just select your read node and press the alt+up/down arrow to switch versions.

### Attentions
---
- By default, the script deletes your sequence if it doesn't cover the full length of the frame range (you can disable it in the `settings.json` file)  
- By default, after converting sequence to video, script delete sequence files (which can also be disabled in `settings.json`)  
- By default, sequences are written in native pixel aspect, but Houdini flipbooks cannot handle that with the original resolution. It can be fixed in Nuke via the reformat node. But ffmpeg conversion handles pixel aspect and gives you the correct image (which can also be modified in `settings.json`)

### Dependencies
---
- ffmpeg installed and be in your system envs
## Installation 
---
1. Download source files 
2. Copy them to your 

| os | location |
|---|---|
| win | %USERNAME%/Documents/houdini%.% |
| linux | $HOME/houdini%.% |
| mac | /Users/%USERNAME%/Library/Preferences/houdini%.% |

#### Tested
---

| Version     | win | linux | mac |
| ----------- | ----------- |----------- | ----------- | 
| 19.5.403 - 3.9py     |+|
| Paragraph   | Text        | 

#### Credits 
---
- 

#### Attributions 
---
- 
