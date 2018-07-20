from . import Comms
from . import Recorder
from . import LinMaze
import os
import sys
import subprocess

__version__ = '0.5.21'

def main(args=None):
    """ The main routine. """
    project_dir = os.path.split(__file__)[0]

    if args is None:
        args = sys.argv[1:]
    
    if args:
        if args[0] == 'examples':
            # subprocess.Popen(r'explorer "{}\examples"'.format(project_dir))
            os.startfile(project_dir+r'\examples')
        if args[0] == 'guide':
            os.startfile(project_dir+r'\docs\_downloads\Gramophone User Guide.pdf')
        if args[0] == 'docs':
            os.startfile(project_dir+r'\docs\index.html')
        if args[0] == 'ver':
            print('\n Gramophone Tools version:', __version__)
            input(' Press ENTER to continnue...')
        if args[0] not in ['examples', 'guide', 'docs', 'ver']:
            help_text()
    else:
        help_text()

def help_text():
    print('\n Use one of the following arguments:\n')
    print('    ver - Displays the current version of the GramophoneTools package in the command line.')
    print('    guide - Opens the user guide of the Gramophone system.')
    print('    docs - Opens the documentation of the GramophoneTools package.')
    print('    examples - Opens a folder containing examples for the LinMaze submodule.')
    print('\n eg.: gram guide\n')
    input(' Press ENTER to continnue...')