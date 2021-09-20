from . import Comms
from . import Recorder
from . import LinMaze
import os
import sys

__version__ = '0.7.1'


def main(args=None):
    """ The main routine. """
    project_dir = os.path.split(__file__)[0]

    if args is None:
        args = sys.argv[1:]

    if args:
        if args[0] == 'examples':
            os.startfile(project_dir+r'\examples')
        if args[0] == 'guide':
            os.startfile(
                project_dir+r'\docs\_downloads\Gramophone User Guide.pdf')
        if args[0] == 'docs':
            os.startfile(project_dir+r'\docs\index.html')
        if args[0] == 'ver':
            print('\n Gramophone Tools version:', __version__)
            input(' Press ENTER to continnue...')
        if args[0] == 'make_icons':
            from GramophoneTools import shortcuts
            shortcuts.install_shortcuts()
        if args[0] not in ['examples', 'guide', 'docs', 'ver', 'make_icons']:
            help_text()
    else:
        help_text()


def help_text():
    print('\n Use one of the following arguments:\n')
    print('    ver - Displays the current version of the GramophoneTools package in the command line.')
    print('    guide - Opens the user guide of the Gramophone system.')
    print('    docs - Opens the documentation of the GramophoneTools package.')
    print('    examples - Opens a folder containing examples for the LinMaze submodule.')
    print('    make_icons - Create shortcuts for Gramohone related things on the desktop (admin).')
    print('\n eg.: gram guide\n')
    input(' Press ENTER to continnue...')
