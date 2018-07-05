# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import GramophoneTools

setup(
    name='GramophoneTools',
    version=GramophoneTools.__version__,
    description='Tools for Gramophone systems by Femtonics Ltd.',
    url='http://femtonics.eu/',
    author='Femtonics Ltd.',
    author_email='info@femtonics.eu',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Scientific/Engineering',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Programming Language :: Python :: 3.6'],
    license='GNU GPLv3',
    keywords='femtonics gramophone',
    project_urls={
        'GitHub': 'https://github.com/Femtonics/GramophoneTools',
        'Documentation': 'http://gramophonetools.readthedocs.io',
        'User Guide': 'http://gramophonetools.readthedocs.io/en/latest/_downloads/Gramophone%20User%20Guide.pdf'},
    packages=['GramophoneTools.Comms', 'GramophoneTools.LinMaze',
              'GramophoneTools.LinMaze.Tools', 'GramophoneTools.Recorder'],
    py_modules=["GramophoneTools.ver"],
    install_requires=[
        'h5py',
        'PyQt5',
        'numpy',
        'dill',
        'pillow',
        'pyglet',
        'pyqtgraph',
        'matplotlib',
        'opencv-python',
        'pywinusb',
        'xlsxwriter'],
    extras_require={
        'tests': [
            'pytest'],
        'docs': [
            'sphinx',
            'sphinx_rtd_theme']},
    python_requires='>=3',
    package_data={
        'GramophoneTools.LinMaze': ['res/icon.png', '*.dll'],
        'GramophoneTools.Recorder': ['*.ui', '*.pyw'],
    },
    entry_points={
        'gui_scripts': ['gramrec = GramophoneTools.Recorder.__main__:main'],
        'console_scripts': ['gramver = GramophoneTools:print_version']
    }
)
