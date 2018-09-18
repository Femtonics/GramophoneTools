import os
import sys
import sysconfig

if sys.platform == 'win32':
    from win32com.client import Dispatch
    import winreg

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


def install_shortcuts():
    """ Make Windows shotcuts on the public desktop. """
    print('Creating shortcuts...')
    scriptsDir = sysconfig.get_path('scripts')
    create_shortcut('Gramophone Recorder', os.path.join(scriptsDir, 'gramrec.exe'),
                    os.path.join(DIR, 'res\\vinyl.ico'),
                    comment='Lauch the Gramophone Recorder.')
    create_shortcut('Gramophone User Guide', os.path.join(scriptsDir, 'gram.exe'),
                    os.path.join(DIR, 'res\\manual.ico'),
                    arguments='guide',
                    comment='Lauch the Gramophone Recorder.')
    create_shortcut('Update GramophoneTools', os.path.join(scriptsDir, 'pip.exe'),
                    os.path.join(DIR, 'res\\update.ico'),
                    arguments='install -U GramophoneTools',
                    comment='Use pip to update the GramophoneTools package to the newest version')


if __name__ == '__main__':
    install_shortcuts()
