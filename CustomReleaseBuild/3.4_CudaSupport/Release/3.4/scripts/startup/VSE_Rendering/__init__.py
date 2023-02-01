
bl_info = {
    "name": "VSE Rendering",
    "author": "Luma/VSE",
    "version": (1, 0, 0),
    "blender": (3, 0, 1),
    "location": "3D View > Properties> VSE Render",
    "description": "VSE automated render tool. Allows the iniatializing, modification, and commandline sequencing for all VV compatible renders: EXR (Blender), PNGS (CompVV), .VV (MakeVV)",
    "category": "Rendering",
    }

from VSE_Rendering import VSERender_Tool

def register():
    VSERender_Tool.register()

def unregister():
    VSERender_Tool.unregister()

if __name__ == "__main__":
    register()
