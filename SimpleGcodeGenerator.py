#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Main gui for SimpleGcodeGenerator

Copyright (C) 2017  Erik Schuster  erik at muenchen - ist - toll dot de
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Version   Author          Changes:
170409    Erik Schuster   First version
170415    Erik Schuster   Added "Project Insert" feature.
                          Added "Project save selection" feature.
                          Corrected some typos.
170506    Erik Schuster   Bugfix of button status <Write to AXIS & quit> when started within AXIS.
                          Function and Button <Save G-code & AXIS reload> changed to <Save G-code & AXIS Load>
                          Now constantly checking if AXIS is running.
170508    Erik Schuster   Bugfix: <No such file or directory>: Now correct Unix style EOL (LF only).
170517    Erik Schuster   Small optimisations.
                          ncclass gui's are not destroyed and created anymore each time they are selected.
                          Changed font for Listboxes and output text box.
170527    Erik Schuster   Removed continous check if Axis is running since it slowed down everything.
170625    Erik Schuster   Bugfix <CheckForUpdate> : Selection of list-objects was discarded.
170724    Erik Schuster   Implemented a litte better filename handling.
                          Added Key-bindings for the object list.
                          Added selection check in <ProjectSaveSelection>.
230206    TurBoss         Port to Python3.
"""

import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
import os
import sys

from lib import sgg  # import the nc-logic
from lib import widgets  # import widgets
from lib import guiclasses  # import gui for nc-objects
from lib import utils  # import utility module
from lib import ncclasses  # import the module for version info only
from lib import gcode  # import the module for version info only
from lib import mathutils  # import the module for version info only
from lib import font2vector  # import the module for version info only
from lib import tooltable  # import the module for version info only
from lib import ngcsub  # import the module for version info only
from lib import counterbore  # import the module for version info only
from lib import nclib  # import the module for version info only
from lib import feedsnspeeds  # import the module for version info only

VERSION = "230206"  # version of this file (jjmmdd)
APP_VERSION = "3.7.0"  # overall application version
APP_NAME = sgg.APP + " " + APP_VERSION  # application name
TIME_UPDATE = 500  # polling interval to update the generated g-code


class MainGUI(tk.Frame, widgets.Widgets):  # ===================================
    """Main GUI"""

    def __init__(self, master):
        """Initialise the gui"""
        tk.Frame.__init__(self, master)
        self.grid(sticky="NW")
        master.wm_resizable(0, 0)
        master.protocol("WM_DELETE_WINDOW", self.QuitHandler)
        self.sgg = sgg.sgg()  # create instance of the logic
        self.numlinesoutput = tk.StringVar(self, 0, "")  # number of lines of current g-code output
        self.output = ""  # copy of the current g-code output
        self.CreateWidgets()  # populate the main gui with widgets
        self.lb_ncClasses.delete(0, tk.END)  # initialise the gui (fill the <create objects> listbox)
        for o in ncclasses.NCCLASSES:
            self.lb_ncClasses.insert(tk.END, o.name)
        self.ObjectListbox_update()  # update the <generated objects> listbox with generated objects
        self.SetTitle()  # set the title of the application window
        self.InitGuiList()
        self.CheckForUpdate()  # start polling for updates

    def SetTitle(self, filename=""):
        """Sets the title of the application"""
        s = APP_NAME
        if not filename == "": s += " - [" + filename + " ]"
        self.master.title(s)

    def InitGuiList(self):
        """Initialie the list that holds the gui of each created object"""
        try: self.guilist[self.gui_active_index].Destroy()
        except: pass
        self.gui_active_index = None
        self.guilist = []  # list that holds all reated gui for nc-objects
        for i in range(len(self.sgg.objlist)):  # fill the the list with dummies
            self.guilist.append(None)

    def CheckForUpdate(self):
        """Updates the output if neccessary every n milliseconds"""
        new = self.sgg.GetGcode()
        if not new == self.output:
            self.output = new
            self.tbOutput.delete(1.0, tk.END)
            self.tbOutput.insert(tk.END, self.output)
            self.tbOutput.yview(tk.END)
            self.numlinesoutput.set(str(self.output.count("\n")) + " lines of code")
            indexes = self.lb_ncObjects.curselection()
            if indexes: self.ObjectListbox_update(indexes)
            else: self.ObjectListbox_update()
        self.after(TIME_UPDATE, self.CheckForUpdate)

    def QuitHandler(self):
        """Handles quit of the application"""
        self.master.destroy()  # destroy root window
        self.master.quit()  # Quit main loop

    def ObjectCreate(self, gui=True):
        """Creates a new nc-object, based on the selected class"""
        class_selected = int(self.lb_ncClasses.curselection()[0])  # determine selected class
        target_index = self.lb_ncObjects.curselection()  # determine list position to insert the new object
        if target_index: target_index = int(target_index[0])
        else: target_index = int(self.lb_ncObjects.index(tk.END))
        obj = self.sgg.ObjectCreate(class_selected, target_index)  # create new object
        self.ObjectListbox_update()  # update listbox of created objects
        self.lb_ncObjects.selection_set(target_index + 1)  # select the newly generated object in the listbox
        self.lb_ncObjects.see(target_index + 1)  # adjust the the listbox to show the active item
        try: self.guilist[self.gui_active_index].Hide()  # hide the current gui
        except: pass
        self.guilist.insert(target_index + 1, guiclasses.GUICLASSES[class_selected](root, obj))  # create gui and hand over a reference of the nc-object
        self.gui_active_index = target_index + 1

    def ObjectDelete(self, *dummy):
        """Deletes the selected object"""
        indexes = self.lb_ncObjects.curselection()
        if indexes and \
           tkinter.messagebox.askokcancel("Delete", "Delete selected object(s)?"):
            indexes2 = sorted(list(map(int, indexes)), reverse=True)
            for i in indexes2:
                try: self.guilist[int(i)].Destroy()
                except: pass
                self.guilist.pop(int(i))
            self.sgg.ObjectsDelete(indexes)
            self.ObjectListbox_update(indexes)

    def ObjectsMoveUp(self, *dummy):
        """Changes the ordner of the cerated objects"""
        indexes = self.lb_ncObjects.curselection()
        if indexes:
            utils.ListItemsMoveUp(self.guilist, indexes)
            indexes = self.sgg.ObjectsMoveUp(indexes)
            self.ObjectListbox_update(indexes)
            if self.gui_active_index > 1: self.gui_active_index -= 1
        try: self.guilist[self.gui_active_index].lift()
        except: pass

    def ObjectsMoveDown(self, *dummy):
        """Changes the ordner of the cerated objects"""
        indexes = self.lb_ncObjects.curselection()
        if indexes:
            utils.ListItemsMoveDown(self.guilist, indexes)
            indexes = self.sgg.ObjectsMoveDown(indexes)
            self.ObjectListbox_update(indexes)
            if self.gui_active_index < len(self.guilist): self.gui_active_index += 1
        try: self.guilist[self.gui_active_index].lift()
        except: pass

    def ObjectDublicate(self, *dummy):
        """Dublicates the selected object"""
        index = self.lb_ncObjects.curselection()
        if index and \
           tkinter.messagebox.askokcancel("Dublicate", "Dublictae selected object?"):
            index = int(index[0])
            i = self.sgg.ObjectDublicate(index)
            self.guilist.insert(index + 1, None)
            self.ObjectListbox_update(i)
            self.ObjectEdit()

    def ObjectEdit(self, *dummy):
        """Edits the selected object, by creating the corresponding gui"""
        oi = self.lb_ncObjects.curselection()
        if oi:
            oi = int(oi[0])
            if not self.gui_active_index == oi:
                try: self.guilist[self.gui_active_index].Hide()
                except: pass
            try:
                self.guilist[oi].Show()
            except:
                ci = self.sgg.GetClassIndex(oi)
                self.guilist[oi] = guiclasses.GUICLASSES[ci](root, self.sgg.GetObject(oi))
            self.gui_active_index = oi

    def ObjectListbox_update(self, indexes=None):
        """Update the displayed objectlist in the widget"""
        self.lb_ncObjects.delete(0, tk.END)
        for n in self.sgg.GetObjectNames():
            self.lb_ncObjects.insert(tk.END, n)
        if not indexes == None:
            try:
                for i in indexes:
                    self.lb_ncObjects.selection_set(i)
                    self.lb_ncObjects.activate(i)
                self.lb_ncObjects.see(i)
            except:
                self.lb_ncObjects.selection_set(indexes)
                self.lb_ncObjects.see(indexes)

    def ProjectLoad(self):
        """Loads a project"""
        filename = widgets.AskOpenFile("Load project", "~", sgg.PROJECTFILE_DEFAULT, "Simple Gcode Generator", "*." + sgg.PROJECTFILE_EXTENSION)
        if not filename: return
        self.sgg.LoadProject(filename, None)
        self.ObjectListbox_update()
        self.SetTitle(filename)
        self.InitGuiList()

    def ProjectInsert(self):
        """Loads a project"""
        index = self.lb_ncObjects.curselection()
        if index: index = int(index[0]) + 1
        else: index = int(self.lb_ncObjects.index(tk.END))
        filename = widgets.AskOpenFile("Load project", "~", sgg.PROJECTFILE_DEFAULT, "Simple Gcode Generator", "*." + sgg.PROJECTFILE_EXTENSION)
        if not filename: return
        self.sgg.LoadProject(filename, index)
        self.ObjectListbox_update(index)
        self.SetTitle(filename)
        self.InitGuiList()

    def ProjectSave(self):
        """Saves a project"""
        filename = widgets.AskSaveFile("Save project", "~", self.sgg.fn_project, "Simple Gcode Generator", "*." + sgg.PROJECTFILE_EXTENSION)
        if not filename: return
        self.sgg.SaveProject(filename, None)
        self.SetTitle(filename)

    def ProjectSaveSelection(self):
        """Saves a project"""
        indexes = self.lb_ncObjects.curselection()
        if (len(indexes) > 0):
            if not indexes: indexes = None
            filename = widgets.AskSaveFile("Save project selection", "~", sgg.PROJECTFILE_DEFAULT, "Simple Gcode Generator", "*." + sgg.PROJECTFILE_EXTENSION)
            if not filename: return
            self.sgg.SaveProject(filename, indexes)
            self.SetTitle(filename)
        else:
            return

    def GcodeSave(self):
        """Saves the g-code to the current file"""
        if not self.sgg.fn_output == "" and tkinter.messagebox.askokcancel("Save", "Overwrite existing file?"):
            if not self.sgg.SaveGcode(self.sgg.fn_output):
                tkinter.messagebox.showerror("ERROR", "Error saving gcode")

    def GcodeSaveAs(self):
        """Saves the g-code under a name to a file"""
        filename = widgets.AskSaveFile("Save G-code", "~", self.sgg.fn_output, "LinuxCNC-G-code-file", "*." + sgg.GCODEFILE_EXTENSION)
        if not filename: return
        if not self.sgg.SaveGcode(filename):
            tkinter.messagebox.showerror("ERROR", "Error saving gcode")

    def GcodeSaveSelection(self):
        """Save the g-code of the selected objects to a file"""
        selected = list(self.lb_ncObjects.curselection())
        if (len(selected) > 0):
            filename = widgets.AskSaveFile("Save selected G-code", "~", self.sgg.fn_output, "LinuxCNC-G-code-file", "*." + sgg.GCODEFILE_EXTENSION)
            if not filename: return
        else:
            return
        if not self.sgg.SaveGcode(filename, indexes=selected):
            tkinter.messagebox.showerror("ERROR", "Error saving gcode")

    def LCNC_WriteToAxisAndQuit(self):
        """Write the g-code to AXIS and quit the application"""
        if sgg.IN_AXIS:
            if tkinter.messagebox.askokcancel("Write to AXIS and quit", "Are you sure?"):
                self.sgg.WriteGcodeToStdout()
                self.QuitHandler()

    def LCNC_SaveAndLoad(self):
        """Saves the g-code to the current file and forces AXIS to load the last saved file"""
        if self.sgg.fn_output:
            if self.sgg.SaveGcode(self.sgg.fn_output):
                retval = self.sgg.AxisLoad()
                if not retval == 0:
                    tkinter.messagebox.showerror("ERROR", "LinuxCNC reload error.\nReturncode:" + str(retval))
            else:
                tkinter.messagebox.showerror("Error saving gcode")
        try: self.guilist[self.gui_active_index].lift()
        except: pass

    def ProjectReset(self):
        """Resets the whole project"""
        if tkinter.messagebox.askokcancel("Reset", "Reset application?"):
            self.sgg.ResetProject()
            self.ObjectListbox_update()
            self.SetTitle()

    def Info(self):
        """Show the versions of all modules"""
        v = sgg.APP + "\n\n"
        v += "Version: " + APP_VERSION + "\n\n"
        v += "Module versions:\n"
        v += "gui\t\t" + VERSION + "\n"
        v += "guiclasses\t" + guiclasses.VERSION + "\n"
        v += "widgets\t\t" + widgets.VERSION + "\n"
        v += "sgg\t\t" + sgg.VERSION + "\n"
        v += "tooltable\t\t" + tooltable.VERSION + "\n"
        v += "feedsnspeeds\t" + feedsnspeeds.VERSION + "\n"
        v += "ncclasses\t\t" + ncclasses.VERSION + "\n"
        v += "nclib\t\t" + nclib.VERSION + "\n"
        v += "font2vector\t" + font2vector.VERSION + "\n"
        v += "ngcsub\t\t" + ngcsub.VERSION + "\n"
        v += "counterbore\t" + counterbore.VERSION + "\n"
        v += "gcode\t\t" + gcode.VERSION + "\n"
        v += "mathutils\t\t" + mathutils.VERSION + "\n"
        v += "utils\t\t" + utils.VERSION + "\n\n"
        v += "For further information,\nplease read the CHANGELOG file.\n"
        tkinter.messagebox.showinfo("Info", v)

    def HelpShow(self):
        """Show the helpwindow"""
        tkinter.messagebox.showinfo("Help", "Please read the MANUAL file int the doc folder.")

    def ShowStatus(self):
        """Show the directories"""
        cwd = os.getcwd()
        v = "Directory SimpleGcodeGenerator: " + os.getcwd() + "\n\n"
        v += "Directory LinuxCNC axis-remote: " + self.sgg.axis_remote_path + "\n\n"
        v += "Path LinuxCNC tool-table: " + tooltable.PATH + "\n\n"
        v += "Preamble loaded: " + str(self.sgg.preamble_found) + "\n"
        v += "Postamble loaded: " + str(self.sgg.postamble_found) + "\n\n"
        v += "Python:" + sys.version + "\n\n"
        tkinter.messagebox.showinfo("Status", v)

    def CreateWidgets(self):
        """Create the widgets for the gui"""
        if not sgg.IN_AXIS: state = tk.DISABLED  # application started stand alone
        else: state = tk.NORMAL  # application started from AXIS

        self.menu = tk.Frame(self, bd=5)
        self.menu.grid(column=0, row=0, sticky="NEW")
        tk.Label(self.menu, text="Project", font="bold", bg="SeaGreen3").grid(column=0, row=0, columnspan=2, sticky="EW", padx=1)
        tk.Button(self.menu, text="Load", command=self.ProjectLoad).grid(column=0, row=1, sticky="ew")
        tk.Button(self.menu, text="Insert", command=self.ProjectInsert).grid(column=1, row=1, sticky="ew")
        tk.Button(self.menu, text="Save", command=self.ProjectSave).grid(column=0, row=2, sticky="ew")
        tk.Button(self.menu, text="Save selection", command=self.ProjectSaveSelection).grid(column=1, row=2, sticky="ew")
        tk.Button(self.menu, text="Reset", command=self.ProjectReset).grid(column=0, row=3, columnspan=2, sticky="ewn")
        tk.Label(self.menu, text="G-Code", font="bold", bg="SeaGreen3").grid(column=2, row=0, sticky="EW", padx=1)
        tk.Button(self.menu, text="Save", command=self.GcodeSave).grid(column=2, row=1, sticky="ew")
        tk.Button(self.menu, text="Save as", command=self.GcodeSaveAs).grid(column=2, row=2, sticky="ew")
        tk.Button(self.menu, text="Save selection", command=self.GcodeSaveSelection).grid(column=2, row=3, rowspan=1, sticky="ewns")
        tk.Label(self.menu, text="LinuxCNC", font="bold", bg="SeaGreen3").grid(column=3, row=0, sticky="EW", padx=1)
        tk.Button(self.menu, text="Write to AXIS & quit", command=self.LCNC_WriteToAxisAndQuit, state=state).grid(column=3, row=1, rowspan=1, sticky="ewns")
        tk.Button(self.menu, text="Save G-code & AXIS Load", command=self.LCNC_SaveAndLoad).grid(column=3, row=2, rowspan=1, sticky="ewns")
        tk.Label(self.menu, text="Help", font="bold", bg="SeaGreen3").grid(column=4, row=0, sticky="EW", padx=1)
        tk.Button(self.menu, text="Help", command=self.HelpShow).grid(column=4, row=1, sticky="ew")
        tk.Button(self.menu, text="Info", command=self.Info).grid(column=4, row=2, sticky="ew")
        tk.Button(self.menu, text="Status", command=self.ShowStatus, state=tk.NORMAL).grid(column=4, row=3, sticky="ew")
        for i in range(3):
            self.menu.columnconfigure(i, weight=1)

        self.edit = tk.Frame(self, bd=5)
        self.edit.grid(column=0, row=1, sticky="NSEW")
        tk.Label(self.edit, text="Create Object", font="bold", bg="SeaGreen3").grid(column=0, row=0, sticky="EW", padx=1)
        self.lb_ncClasses = self.ListboxWithScrollbar(self.edit, column=0, row=1, rowspan=4, width=25, height=10, sticky="nsew")
        self.lb_ncClasses.bind("<Double-1>", lambda x: self.ObjectCreate())
        self.lb_ncClasses.configure(font=("Courier New", "12", "normal"))
        tk.Label(self.edit, text="Created Objects", font="bold", bg="SeaGreen3").grid(column=1, columnspan=2, row=0, sticky="EW", padx=1)
        self.lb_ncObjects = self.ListboxWithScrollbar(self.edit, column=1, row=1, rowspan=4, width=27, height=10, sticky="nsew", selectmode=tk.EXTENDED)
        self.lb_ncObjects.configure(font=("Courier New", "12", "normal"))
        self.lb_ncObjects.bind("<Double-1>", self.ObjectEdit)
        self.lb_ncObjects.bind("<Return>", self.ObjectEdit)
        self.lb_ncObjects.bind("<Control-Prior>", self.ObjectsMoveUp)
        self.lb_ncObjects.bind("<Control-Next>", self.ObjectsMoveDown)
        self.lb_ncObjects.bind("<Control-Delete>", self.ObjectDelete)
        self.lb_ncObjects.bind("<Control-Insert>", self.ObjectDublicate)
        tk.Button(self.edit, text="Move up", command=self.ObjectsMoveUp).grid(column=2, row=1, sticky="ew")
        tk.Button(self.edit, text="Move down", command=self.ObjectsMoveDown).grid(column=2, row=2, sticky="ew")
        tk.Button(self.edit, text="Delete", command=self.ObjectDelete).grid(column=2, row=3, sticky="ew")
        tk.Button(self.edit, text="Dublicate", command=self.ObjectDublicate).grid(column=2, row=4, sticky="ew")
        for i in range(1):
            self.edit.columnconfigure(i, weight=1)

        self.output = tk.Frame(self, bd=5)
        self.output.grid(column=0, row=2, rowspan=1, sticky="NEW")
        tk.Label(self.output, text="Generated G-Code", font="bold", bg="cornflower blue").grid(column=0, columnspan=3, sticky="EW", padx=1)
        self.tbOutput = widgets.TextboxWithScrollbar(self.output, column=0, row=1, columnspan=3, rowspan=1, width=80, height=30, sticky="nsew")
        self.tbOutput.configure(font=("Courier New", "10", "normal"))
        tk.Label(self.output, textvariable=self.numlinesoutput).grid(column=1, row=2, sticky="ew")

        self.rowconfigure(1, weight=2)


# start the program
root = tk.Tk()
app = MainGUI(master=root)
app.mainloop()
