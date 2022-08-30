# This module to be called from VSE_Render root directory as a script argument with Blender
import os
import sys
import getopt

import bpy

from VSE_Rendering import VSERender_Engine

_back_output_path = None
_actors_output_path = None
_uvs_output_path = None

# Cannot render back or actors if UVs render is True because of the unique resolution required
_render_back = False
_render_actors = False
_render_UVs = False

_render_resolution_x = None
_render_resolution_y = None

_render_sample = 0

def Apply_Settings():

    print("_______________________________________________________________________________________(switches):")
    # Creating the options for commandline switches
    opts, args = getopt.getopt(
        sys.argv[13:],
        "",
        ["back_out=",
            "actors_out=",
            "uvs_out=",
            "render_back=",
            "render_actors=",
            "render_uvs=",
            "render_resolution_x=",
            "render_resolution_y=",
            "render_sample="])

    _expected_options = ["--back_out",
                            "--actors_out",
                            "--uvs_out",
                            "--render_back",
                            "--render_actors",
                            "--render_uvs",
                            "--render_resolution_x",
                            "--render_resolution_y",
                            "--render_sample"]
    _added_options = []
    for opt, arg in opts:
        if opt == "--back_out":
            global _back_output_path
            _back_output_path = arg
            _added_options.append(opt)
            print("back output file path:     " + arg)

        if opt == "--actors_out":
            global _actors_output_path
            _actors_output_path = arg
            _added_options.append(opt)
            print("actors output file path:     " + arg)

        if opt == "--uvs_out":
            global _uvs_output_path
            _uvs_output_path = arg
            _added_options.append(opt)
            print("UVs output file path:     " + arg)

        if opt == "--render_back":
            global _render_back
            if arg == "True":
                _render_back = True
            _added_options.append(opt)
            print("render back:     " + arg)

        if opt == "--render_actors":
            global _render_actors
            if arg == "True":
                _render_actors = True
            _added_options.append(opt)
            print("render actors     " + arg)

        if opt == "--render_uvs":
            global _render_UVs
            if arg == "True":
                _render_UVs = True
            _added_options.append(opt)
            print("render uvs     " + arg)

        if opt == "--render_resolution_x":
            global _render_resolution_x
            _render_resolution_x = int(arg)
            _added_options.append(opt)
            print("render resolution_x     " + arg)

        if opt == "--render_resolution_y":
            global _render_resolution_y
            _render_resolution_y = int(arg)
            _added_options.append(opt)
            print("render resolution_y " + arg)

        if opt == "--render_sample":
            global _render_sample
            _render_sample = int(arg)
            _added_options.append(opt)
            print("render sample " + arg)

    _missing_option = False
    _missing_string = "\nError: Missing switch: "
    for opt in _expected_options:
        if not opt in _added_options:
            _missing_option = True
            _missing_string += opt + ", "

    if(_missing_option):
        print(_missing_string)
        print("_______________________________________________________________________________________\n")
        return False
    else:
        print("\nall inputs recorded")

    return True

def Setup_Scene():

    # Outputs
    bpy.context.scene.node_tree.nodes[
        VSERender_Engine.Rendering_Engine._BLENDER_COMPOSITING_BACK_EXR_OUTPUT_NODE_NAME].base_path = os.path.join(_back_output_path, "Back_####.exr")
    bpy.context.scene.node_tree.nodes[
        VSERender_Engine.Rendering_Engine._BLENDER_COMPOSITING_ACTORS_EXR_OUTPUT_NODE_NAME].base_path = os.path.join(_actors_output_path, "Actors_####.exr")
    bpy.context.scene.node_tree.nodes[
        VSERender_Engine.Rendering_Engine._BLENDER_COMPOSITING_UVS_EXR_OUTPUT_NODE_NAME].base_path = os.path.join(_uvs_output_path, "UV_####.exr")

    # Resolution
    bpy.context.scene.render.resolution_x = _render_resolution_x
    bpy.context.scene.render.resolution_y = _render_resolution_y

    # Samples
    bpy.context.scene.cycles.samples = _render_sample

    # Render selection
    bpy.context.scene.view_layers["Back"].use = _render_back
    bpy.context.scene.view_layers["Actors"].use = _render_actors
    bpy.context.scene.view_layers["UV"].use = _render_UVs



if len(sys.argv) > 1:
    Apply_Settings()
    Setup_Scene()


