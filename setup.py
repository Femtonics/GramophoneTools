# Always prefer setuptools over distutils
import os
import sys
import sysconfig

import GramophoneTools
from setuptools import find_packages, setup

if sys.platform == 'win32':
    from win32com.client import Dispatch
    import winreg

readme = open('README.md', 'r')
README_TEXT = readme.read()
readme.close()

DIR = os.path.dirname(os.path.abspath(__file__))

def create_shortcut(name, target, icon, arguments='', comment=''):
    desktopFolder = os.getenv('PUBLIC')+'\\Desktop'
    linkName = name+'.lnk'
    pathLink = os.path.join(desktopFolder, linkName)

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(pathLink)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(target))
    shortcut.IconLocation = icon
    shortcut.Arguments = arguments
    shortcut.Description = comment
    shortcut.save()
    print("Created shortcut for '{}' called '{}'.".format(target, name))

setup(
    name='GramophoneTools',
    version=GramophoneTools.__version__,
    description='Tools for Gramophone systems by Femtonics Ltd.',
    long_description=README_TEXT,
    long_description_content_type='text/markdown',
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
        'User Guide': 'http://gramophonetools.readthedocs.io/en/latest/_downloads/Gramophone%20User%20Guide.pdf',
        'Product page':'http://femtonics.eu/femtonics-accessories/gramophone/'},
    packages=['GramophoneTools', 'GramophoneTools.Comms', 'GramophoneTools.LinMaze',
              'GramophoneTools.LinMaze.Tools', 'GramophoneTools.Recorder', 'GramophoneTools.examples', 'GramophoneTools.docs'],
    # py_modules=["GramophoneTools.ver"],
    package_dir={'GramophoneTools.examples': 'examples',
                 'GramophoneTools.docs': 'docs/build/html'},
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
        'pyusb',
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
        'GramophoneTools.Recorder': ['*.ui'],
        'GramophoneTools.Comms': ['*.dll'],
        'GramophoneTools.docs': ['*', '*/*', '*/*/*', '*/*/*/*']
    },
    include_package_data=True,
    entry_points={
        'gui_scripts': ['gramrec = GramophoneTools.Recorder.__main__:main'],
        'console_scripts': ['gramver = GramophoneTools:print_version', 'gram = GramophoneTools:main']
    }
)

if sys.argv[1] in ['install', '-install'] and sys.platform == 'win32':
    print('Creating shortcuts...')
    scriptsDir = sysconfig.get_path('scripts')
    create_shortcut('Gramophone Recorder', os.path.join(scriptsDir, 'gramrec.exe'), os.path.join(DIR, 'res\\vinyl.ico'),
                    comment='Lauch the Gramophone Recorder.')
    create_shortcut('Gramophone User Guide', os.path.join(scriptsDir, 'gram.exe'), os.path.join(DIR, 'res\\manual.ico'),
                    arguments='guide',
                    comment='Lauch the Gramophone Recorder.')
    create_shortcut('Update GramophoneTools', os.path.join(scriptsDir, 'pip.exe'), os.path.join(DIR, 'res\\update.ico'),
                    arguments='install -U GramophoneTools',
                    comment='Use pip to update the GramophoneTools package to the newest version')
