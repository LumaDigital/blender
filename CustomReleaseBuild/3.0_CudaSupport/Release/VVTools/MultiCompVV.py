import sys
import time
import os
import logging
import subprocess
import getopt
import glob

class MultiCompVV(object):

    _from_frame = 0
    _to_frame = 0
    _frame_count = 0
    _input_path = None
    _png_output_path = None
    _compvv_exe_path = None

    def main(self):
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        logging.info("\nMulti CompVV Tool:\n Composites all EXRS from a directory\n")

        if len(sys.argv) > 1:
            if (self.Assign_Variables()):
                if (self.Do_Work()):
                    logging.info("\nMultiCompVV successfully composited PNGS to\n" + self._png_output_path + "\n")
            else:
                logging.info("\nMultiCompVV Failed, re-enter this tool to see a list of inputs required\n")

        else:
            # Prints structured in a way that's neat and readable for the dev
            logging.info("Ensure all options have been passed\nBelow is a list of the required options")
            logging.info("______________________________________\n")
            logging.info("-i = input path (directory of EXRs)")
            logging.info("-o = output path (png folder)")
            logging.info("-f = frame range (eg. 90-90 || 90 || 90-100)")
            logging.info("-c = compvv.exe path (executable path on network)")
            logging.info("______________________________________\n")
            return False;

        return True;

    def Do_Work(self):

        logging.info("\nStarting Composites in " + self._input_path + " :\n");

        _base_main_path = os.path.join(self._png_output_path, 'main.');
        _base_light_path = os.path.join(self._png_output_path, 'light.');
        _base_stencil_path = os.path.join(self._png_output_path, 'stencil.');
        _base_map_path = os.path.join(self._png_output_path, 'map.');
        _base_uv_path = os.path.join(self._png_output_path, 'uv.');

        for _frame in range(self._frame_count):

            _current_frame = self._from_frame + _frame;

            if _current_frame == '0':
                 _current_frame = str(_current_frame + 1).zfill(4);
            else:
                _current_frame = str(_current_frame).zfill(4);

            _Back_EXR_Path = os.path.join(self._input_path, "Back");
            _Back_EXR_Path = _Back_EXR_Path + '_' + _current_frame + '.exr';

            _Actors_EXR_Path = os.path.join(self._input_path, "Actors");
            _Actors_EXR_Path = _Actors_EXR_Path + '_' + _current_frame + '.exr';

            _UV_EXR_Path = os.path.join(self._input_path, "UV");
            _UV_EXR_Path = _UV_EXR_Path + '_' + _current_frame + '.exr';

            logging.info("Busy...\n" + _Back_EXR_Path + "\n" + _Actors_EXR_Path + '\n' + _UV_EXR_Path);
            process = subprocess.Popen(
                [
                    self._compvv_exe_path,
                    "-back", 
                    _Back_EXR_Path, 
                    "-actors", 
                    _Actors_EXR_Path,
                    "-uv",
                    _UV_EXR_Path, 
                    "-omain",
                    _base_main_path + _current_frame + ".png",
                    "-olight",
                    _base_light_path + _current_frame + ".png",
                    "-ostencil",
                    _base_stencil_path + _current_frame + ".png",
                    "-omap",
                    _base_map_path + _current_frame + ".png",
                    "-ouv",
                    _base_uv_path + _current_frame + ".png"
                ], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            stdout_data, stderr_data = process.communicate()

            if process.returncode != 0:
                logging.info("" + str(stdout_data))
                logging.info("\nError: Compvv failed")
                logging.info("_______________________________________________________________________________________\n")
                return False
            else:
                logging.info("-Success-")

        return True;

    def Assign_Variables(self):

        logging.info("_______________________________________________________________________________________(switches):")
        # Creating the options for commandline switches
        opts, args = getopt.getopt(sys.argv[1:], "i:o:f:t:r:c:s:", ["ipath=", "opath=", "frange=", "cpath="])

        _expected_options = ["-i", "-o", "-f", "-c",]
        _added_options = []
        for opt, arg in opts:
            if opt in ("-i", "--ipath"):
                self._input_path = os.path.join(arg, "")
                _added_options.append(opt)
                logging.info("input path:     " + arg)

            if opt in ("-c", "--cpath"):
                self._compvv_exe_path = arg
                _added_options.append(opt)
                logging.info("compvv path:    " + arg)

            if opt in ("-o", "--opath"):
                self._png_output_path = os.path.join(arg, "")
                _added_options.append(opt)
                logging.info("output path:    " + arg)


            if opt in ("-f", "--frange"):
                self._frame_list = arg.split('-')
                _frame_numbers = [int(s) for s in self._frame_list if s.isdigit()]

                if len(_frame_numbers) <= 2 and len(_frame_numbers) > 1:
                    self._from_frame = _frame_numbers[0]
                    self._to_frame = _frame_numbers[1]

                elif len(_frame_numbers) == 1:
                    self._from_frame = _frame_numbers[0]
                    self._to_frame = _frame_numbers[0]

                _added_options.append(opt)
                self._frame_count = (int(self._to_frame) - int(self._from_frame)) + 1 # Difference + 1 for _from_frame
                logging.info("from frame:     " + str(self._from_frame) + "\nto frame:       " + str(self._to_frame) + "\nframe count:    " + str(self._frame_count))

        _missing_option = False
        _missing_string = "\nError: Missing switch: "
        for opt in _expected_options:
            if not opt in _added_options:
                _missing_option = True
                _missing_string += opt + ", "

        if(_missing_option):
            logging.info(_missing_string)
            logging.info("_______________________________________________________________________________________\n")
            return False
        else:
            logging.info("\nall inputs recorded")
            return True

if __name__ == "__main__":
    program = MultiCompVV()
    program.main()