import sys
import Recorder
import os.path

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    if 'devmode' in args:
        devmode = True
        print('Launching in developer mode...')
    else:
        devmode = False

    file_args = [f for f in args if os.path.isfile(f)]

    if file_args:
        log_file = file_args[0]
        print('Open file:', log_file)
    else:
        log_file = None

    Recorder.main(devmode=devmode, log_file=log_file)

if __name__ == "__main__":
    main()