# This module to be called from VSE_Render root directory as a script argument with Blender

import sys
import getopt

import bpy

from VSE_Rendering import VSERender_Engine

_blend_file_path = None
_exr_output_path = None
_png_output_path = None
_vision_video_output_path = None

_frame_start = 1
_frame_end = 300
_frame_rate = 30
_max_render_samples = 128

_render_exrs = False
_composite_pngs = False
_generate_vv = False

def Assign_Variables():

    print("_______________________________________________________________________________________(switches):")
    # Creating the options for commandline switches
    opts, args = getopt.getopt(
        sys.argv[4:],
        "",
        ["blendfilepath=",
            "exroutput=",
            "pngoutput=",
            "visionoutput=",
            "framestart=",
            "frameend=",
            "framerate=",
            "rendersamples=",
            "renderexr=",
            "compositepng=",
            "generatevv="])

    _expected_options = ["--blendfilepath",
                            "--exroutput",
                            "--pngoutput",
                            "--visionoutput",
                            "--framestart",
                            "--frameend",
                            "--framerate",
                            "--rendersamples",
                            "--renderexr",
                            "--compositepng",
                            "--generatevv"]
    _added_options = []
    for opt, arg in opts:
        if opt == "--blendfilepath":
            global _blend_file_path
            _blend_file_path = arg
            _added_options.append(opt)
            print("blend file path:     " + arg)

        if opt == "--exroutput":
            global _exr_output_path
            _exr_output_path = arg
            _added_options.append(opt)
            print("exr output path:     " + arg)

        if opt == "--pngoutput":
            global _png_output_path
            _png_output_path = arg
            _added_options.append(opt)
            print("png output path:     " + arg)

        if opt == "--visionoutput":
            global _vision_video_output_path
            _vision_video_output_path = arg
            _added_options.append(opt)
            print("vision video output path:     " + arg)

        if opt == "--framestart":
            global _frame_start
            _frame_start = arg
            _added_options.append(opt)
            print("frame start:     " + arg)

        if opt == "--frameend":
            global _frame_end
            _frame_end = arg
            _added_options.append(opt)
            print("frame end:     " + arg)

        if opt == "--framerate":
            global _frame_rate
            _frame_rate = arg
            _added_options.append(opt)
            print("frame rate:     " + arg)

        if opt == "--rendersamples":
            global _max_render_samples
            _max_render_samples = arg
            _added_options.append(opt)
            print("Render Samples: " + arg)

        if opt == "--renderexr":
            global _render_exrs
            if arg == "True":
                _render_exrs = True
            _added_options.append(opt)
            print("Render EXRs: " + arg)

        if opt == "--compositepng":
            global _composite_pngs
            if arg == "True":
                _composite_pngs = True
            _added_options.append(opt)
            print("Composite PNGs: " + arg)

        if opt == "--generatevv":
            global _generate_vv
            if arg == "True":
                _generate_vv = True
            _added_options.append(opt)
            print("Generate VV File: " + arg)


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

def render_and_composite():

    bpy.ops.wm.open_mainfile(filepath=_blend_file_path)

    _rendering_engine = VSERender_Engine.Rendering_Engine(_exr_output_path,
                                                            _png_output_path,
                                                            _vision_video_output_path,
                                                            int(_frame_start),
                                                            int(_frame_end),
                                                            int(_frame_rate),
                                                            int(_max_render_samples),
                                                            _render_exrs,  
                                                            _render_exrs,
                                                            _render_exrs,
                                                            _render_exrs,
                                                            _composite_pngs,
                                                            _generate_vv)

    _rendering_engine.render_and_composite()

if len(sys.argv) > 1:
    if (Assign_Variables()):
        render_and_composite()
        sys.exit(0)
    else:
        print("VSE Commandline Rendering FAILED: Missing switches")
        print("Ensure all options have been passed\nBelow is a list of the required options")
        print("______________________________________\n")
        print("--blendfilepath = Blend scene file path")
        print("--exroutput = EXR renders output path")
        print("--pngoutput = PNG composites output path")
        print("--visionoutput = Vision Video output path")
        print("--framestart = Beginning frame for render")
        print("--frameend = End frame for render")
        print("--framerate = Frame rate for rendered video")
        print("--rendersamples = Render samples for Back and Actors EXR renders")
        print("--renderexr = Toggle for rendering EXRS (uses --blendfilepath)")
        print("--compositepng = Toggle for compositing PNGs (uses --exroutput)")
        print("--generatevv = Toggle for generating VV file (uses --pngoutput)")
        print("______________________________________\n")
