"""
Animation Library based on the Asset Browser.
"""

bl_info = {
    "name": "Animation Library",
    "description": "Animation Library based on the Asset Browser and Pose Library.",
    "author": "Martin Grabarski",
    "version": (0, 1),
    "blender": (3, 0, 0),
    "warning": "The Asset browser is subject to change",
    "location": "Asset Browser -> Animations, and 3D Viewport -> Animation panel",
    "category": "Animation",
}

import bpy

def register():
    print("Hello World")

def unregister():
    print("Goodbye World")

if __name__ == "__main__":
    register()
