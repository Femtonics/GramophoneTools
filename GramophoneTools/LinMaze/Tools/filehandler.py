''' Tools for reading and writing pyVR related files '''

import csv
import os


def save_lists(filename, headers, lists, delimiter=","):
    ''' Writes the provided lists into a csv '''

    with open(filename, "w", newline='') as csv_file:
        csv_file.write('sep=' + delimiter + os.linesep)
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        writer.writerows(zip(*lists))
        # for row in list(zip(*lists)):
        #     print(row)

    print('Data written to: ' + filename + '\n')


def select_file(*args, **kwargs):
    ''' Displays a file selection dialog and returns the file selected '''
    ''' eg. defaultextension='.csv', filetypes=[('VR Log (.csv)', '.csv')],
        title='Save log for this session', initialdir='C:/VR/Results',
        initialfile=self.start_datetime_str '''

    import tkinter
    from tkinter import filedialog
    root = tkinter.Tk()
    root.withdraw()
    file = filedialog.asksaveasfilename(parent=root, *args, **kwargs)

    return str(file)
