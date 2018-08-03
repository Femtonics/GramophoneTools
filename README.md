# Gramophone Tools
Collection of tools to be used with the Gramophone system by Femtonics Ltd. Contains 3 subpackages: **Comms** for communicating with Gramophone devices, **LinMaze** for conditioning mice in a simple linear virtual maze and **Recorder** for making velocity recordings in a harware triggered manner.

# Installation
Open an admin terminal by right clicking the start menu and selecting "Windows PowerShell (admin)".

To install run the following command:

``` pip install GramophoneTools ```

After install you can run the ```gram make_icons``` command to create shortcuts on the Windows desktop for all users. 

# Updating
To find out if there is a newer version available run:

``` pip list -o ```

If GramohoneTools shows up in the list you can update it by running:

``` pip install -U GramophoneTools ```

# Usage
The user guide for Gramophone systems can be found online: [http://gramophone.femtonics.eu/user_guide.html]

## Gramophone recorder
To start the velocity recorder run the ``` gramrec ``` command. In windows you can press the Win+R keyboard shortcut to display the 'Run' window and type it in there.

## LinMaze
Make a .py file that describes the conditioning task and run it with python.exe. See the examples folder, or run the ```gram examples``` command after install.

# Documentation
The full documentation of the GramophoneTools package is available online at: [http://gramophone.femtonics.eu]