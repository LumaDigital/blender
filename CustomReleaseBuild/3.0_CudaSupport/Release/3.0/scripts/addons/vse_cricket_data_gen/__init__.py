import bpy
from . import data_generation_tool

bl_info = {
    "name": "Luma Cricket Game data file generation",
    "author": "Martin Grabarski @ Luma Interactive",
    "version": (1, 0, 0),
    "blender":  (3, 0, 1),
    "location": "Video Sequence Editor > Properties > Cricket Data Generation",
    "description": "Tool for generating Cricket data files for events and sounds in .csv format",
    "category": "Video Sequence Editor (VSE)",
}

### REGISTER ###
def register():
    data_generation_tool.register()

def unregister():
    data_generation_tool.unregister()
