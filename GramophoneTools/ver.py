""" Simple module for single sourcing the version. """

__version__ = '0.4.3'


def print_version():
    """ Prints the version. Called by the command line function 'gramver'. """
    print('Gramophone Tools version:', __version__)
