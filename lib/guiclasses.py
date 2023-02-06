#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Provides a gui for each ncclass

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
170415    Erik Schuster   <Bezel>: Canvas output updated
170416    Erik Schuster   Added classes <OutlineCircularArc>, <PocketCircularArc>.
170417    Erik Schuster   Added class <Text> for text engraving.
                          Added exact path option to <OutlineCircularArc>,<OutlineRectangle>,<OutlineCircle>
170506    Erik Schuster   Some comments and minor changes.
170517    Erik Schuster   Bugfix: OnClose event was not triggered due to wrong binding.
                          Added ToolTable and Pre-Postamble selection dialog.
                          GUIs have a fixed size now.
                          Renamed defs <OnClose> to <Hide>.
                          Added def <Destroy>.
                          Moved defs <Hide>, <Destroy>, <Show> to <Baseclass>.
                          Several corrections of tool-tips (helps) and widget texts.
170529    Erik Schuster   Added guiclass <Subroutine>. Now ngc-subroutines can be included.
170625    Erik Schuster   Reduced code length by optimised read and write to ncclasses.
                          Added class <Counterbore>.
170709    Erik Schuster   Added class <FeedAndSpeed>.
230206    TurBoss         Port to Python3.

ToDo:
- The tooltip ist not displayed at the correct position if the root window was moved.
- The tooltip sometimes flickers. Moving the window "solves" it.
"""

import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog

from . import widgets
from . import widgets as wi  # imports pre-defined widgets class
from . import mathutils as mu
from . import sgg
from . import tooltable
from . import counterbore
from . import ngcsub
from . import font2vector
from . import feedsnspeeds
from . import nclib

VERSION = "230206"  # version of this file (jjmmdd)

WINPOSX = 6  # x-position in root window, where to put the child window
WINPOSY = 383  # y-position in root window, where to put the child window
TIME_UPDATE = 500  # interval to update the corresponding ncclass in [ms]


class FeedAndSpeed():  # =======================================================
    """Shows a dialog to calculate the proper feed and spindle speed.
    """

    def __init__(self, rootwin, toolvar, diametervar, speedvar, feedtdvar, feedsovar):
        """rootin = reference to the root frame
        toolvar = reference to the tk-variable which holds the tool number
        diametervar = reference to the tk-variable which hold the tool diameter"""
        self.rootwin = rootwin
        self.toolvar = toolvar
        self.diametervar = diametervar
        self.feedtdvar = feedtdvar
        self.feedsovar = feedsovar
        self.speedvar = speedvar
        self.index_t = 0
        self.index_d = 0
        self.fz = tk.DoubleVar(self.rootwin, 0.05)
        self.vc = tk.DoubleVar(self.rootwin, 100)
        self.z = tk.IntVar(self.rootwin, 2)
        self.ss = tk.DoubleVar(self.rootwin, 10000)
        self.td = tk.DoubleVar(self.rootwin, diametervar.get())
        self.frtd = tk.DoubleVar(self.rootwin, self.feedtdvar.get())
        self.frso = tk.DoubleVar(self.rootwin, 0)

    def show(self):
        """Creates a the popup window"""
        try:
            self.wints.deiconify()
            self.wints.lift()
        except:
            self.wints = tk.Toplevel(self.rootwin)
            self.wints.wm_title("Calculate feeds and speeds")
            self.wints.resizable(0, 0)
            self.wints.geometry("+" + str(self.rootwin.winfo_x()) + "+" + str(self.rootwin.winfo_y()))
            self.wints.protocol("WM_DELETE_WINDOW", self.wints.withdraw)
            self.lb_tables = wi.ListboxWithScrollbar(self.wints, help="<Double click> to select the table.", column=0, columnspan=10, row=5, width=80, height=5, rowspan=6)
            self.lb_tables.configure(font=("Courier New", "10", "normal"))
            for i, table in enumerate(feedsnspeeds.TABLES):
                text = "%s" % (table.description)
                self.lb_tables.insert(i, text)
            self.lb_tables.bind("<Double-1>", self.select_table)
            self.header = tk.Label(self.wints, text="", font=("Courier New", "10", "normal"), anchor="w")
            self.header.grid(column=0, row=11, columnspan=10, sticky="EW")
            self.lb_data = wi.ListboxWithScrollbar(self.wints, help="", column=0, columnspan=10, row=12, width=80, height=10)
            self.lb_data.configure(font=("Courier New", "10", "normal"))
            # self.lb_data.bind("<Double-1>", self.select_data)
            tk.Button(self.wints, text="Use data", command=self.ok).grid(column=3, row=3, rowspan=2)
            tk.Button(self.wints, text="Calc", command=self.calc).grid(column=2, row=3, rowspan=2)
            wi.LabelEntry(self.wints, self.vc, "Cut speed", help="mm,in / U", column=0, row=1)
            wi.LabelEntry(self.wints, self.fz, "Feed per tooth", help="mm,in / U", column=0, row=2)
            wi.LabelEntry(self.wints, self.z, "Number of teeth", help="#", column=0, row=3)
            wi.LabelEntry(self.wints, self.td, "Tool diameter (td)", help="mm,in", column=0, row=4)
            wi.LabelEntry(self.wints, self.ss, "Spindle speed", help="1/U", column=2, row=1)
            wi.LabelEntry(self.wints, self.frtd, "Feed rate @ td", help="mm,in / min", column=2, row=2)
            tk.Label(self.wints, text="Used formulas:").grid(column=4, row=1)
            tk.Label(self.wints, text="n = (vc*1000)/(PI*d)\nvf = n * z * fz").grid(column=4, row=2, rowspan=2)

    def select_table(self, event):
        """Select a atble and show the data in the listbox below"""
        ti = self.lb_tables.curselection()
        if ti:
            self.index_t = int(ti[0])
            self.FillDrillData(self.index_t)

    def select_data(self, event):
        """Select the data in the lower listbox"""
        ti = self.lb_data.curselection()
        if ti:
            i = int(ti[0])
            # print feedsnspeeds.TABLES[self.index_t].table[i].Get_fz(self.td.get())

    def ok(self):
        """Take the calculated data and wirte it to the object"""
        self.speedvar.set(self.ss.get())
        self.feedtdvar.set(self.frtd.get())
        self.feedsovar.set(self.frtd.get())
        self.wints.withdraw()
        try: self.rootwin.lift()
        except: pass

    def calc(self):
        """Calculate"""
        try:
            n = int(nclib.CalcRPM(self.vc.get(), self.td.get()))
            self.ss.set(n)
            frtd = int(nclib.CalcFeed(n, self.z.get(), self.fz.get()))
            self.frtd.set(frtd)
            self.frso.set(frtd)
        except:
            pass

    def FillDrillData(self, n):
        """Show the data of the selected table"""
        self.lb_data.delete(0, tk.END)
        fz = ""
        for i, f in enumerate(feedsnspeeds.TABLES[n].columnheaders):
            fz += "%*s  " % (feedsnspeeds.TABLES[n].width[i], f)
        self.header.configure(text=fz)
        # self.lb_data.insert(tk.END, fz)
        for r in feedsnspeeds.TABLES[n].table:
            fz = ""
            for i, c in enumerate(r):
                fz += "%*s  " % (feedsnspeeds.TABLES[n].width[i], c)
            self.lb_data.insert(tk.END, fz)


class ToolTable():  # ==========================================================
    """Shows the the LinuxCNC tool table and allow Loading a new tool table and to select a tool
    The selected tool-number and diameter are written the given tk-vars toolvar and diametervar"""

    def __init__(self, rootwin, toolvar, diametervar):
        """rootin = reference to the root frame
        toolvar = reference to the tk-variable which holds the tool number
        diametervar = reference to the tk-variable which hold the tool diameter"""
        self.rootwin = rootwin
        self.toolvar = toolvar
        self.diametervar = diametervar

    def show(self):
        """Creates a popup window to choose the tool and corresponding diameter"""
        try:
            self.wints.deiconify()
            self.wints.lift()
        except:
            self.wints = tk.Toplevel(self.rootwin)
            self.wints.wm_title("Select tool from tool table")
            self.wints.resizable(0, 0)
            self.wints.geometry("+" + str(self.rootwin.winfo_x()) + "+" + str(self.rootwin.winfo_y()))
            self.wints.protocol("WM_DELETE_WINDOW", self.wints.withdraw)
            tk.Button(self.wints, text="Load LinuxCNC tool table", command=self.load).grid(column=0, row=0)
            tk.Label(self.wints, text="<Double click> to select the tool.").grid(column=0, row=1, sticky="EW")
            lb = wi.ListboxWithScrollbar(self.wints, help="<Double click> to select the tool.", column=0, row=2, width=40, height=20)
            lb.configure(font=("Courier New", "10", "normal"))
            for i, tool in enumerate(tooltable.TOOLTABLE):
                text = "T%03d   D%05.3f   %s" % (tool.number, tool.diameter, tool.description)
                lb.insert(i, text)
            lb.bind("<Double-1>", self.select)

    def select(self, event):
        """Sets the values for tool number and tool diameter based on the loaded tooltable"""
        widget = event.widget
        index = int(widget.curselection()[0])
        self.toolvar.set(tooltable.TOOLTABLE[index].number)
        self.diametervar.set(tooltable.TOOLTABLE[index].diameter)
        self.wints.withdraw()
        try: self.rootwin.lift()
        except: pass

    def load(self):
        """Load a LinuxCNC tool table and rebuild the window"""
        fn = widgets.AskOpenFile("Open tool table", tooltable.DIR, "", "tool table", ".tbl")
        if not fn:
            return
        if not tooltable.LcncLoadToolTable(fn):
            tkinter.messagebox.showerror("Error", "Error loading LinucCNC tool table")
        else:
            self.wints.destroy()
            self.show()


class PrePostamble():

    def __init__(self, rootwin, plane, preamble_gcode, postamble_gcode, preamble_tool,
                 preamble_zsh, preamble_plane, preamble_spindle_cw, preamble_spindle_ccw,
                 preamble_mist, preamble_flood, postamble_zsh, postamble_spindle_off, postamble_coolant_off):
        self.rootwin = rootwin

        self.plane = plane
        self.preamble_gcode = preamble_gcode
        self.postamble_gcode = postamble_gcode
        self.preamble_tool = preamble_tool
        self.preamble_zsh = preamble_zsh
        self.preamble_plane = preamble_plane
        self.preamble_spindle_cw = preamble_spindle_cw
        self.preamble_spindle_ccw = preamble_spindle_ccw
        self.preamble_mist = preamble_mist
        self.preamble_flood = preamble_flood
        self.postamble_zsh = postamble_zsh
        self.postamble_spindle_off = postamble_spindle_off
        self.postamble_coolant_off = postamble_coolant_off

    def show(self):
        """Creates a popup window for the configuration of the per- and postamble"""
        try:
            self.winpp.deiconify()
            self.winpp.lift()
        except:
            self.winpp = tk.Toplevel(self.rootwin)
            self.winpp.wm_title("Object specific options")
            self.winpp.resizable(0, 0)
            self.winpp.geometry("+" + str(self.rootwin.winfo_x()) + "+" + str(self.rootwin.winfo_y()))
            self.winpp.protocol("WM_DELETE_WINDOW", self.winpp.withdraw)
            tk.Label(self.winpp, text="Preamble", font="bold", bg="Dark grey").grid(column=0, row=0, columnspan=2, sticky="EW", padx=1)
            wi.Optionbutton(self.winpp, self.preamble_tool, "Select and change tool", "Tx + M6", column=0, row=1)
            wi.Optionbutton(self.winpp, self.preamble_zsh, "Go to safety height", "", column=0, row=2)
            wi.Optionbutton(self.winpp, self.preamble_plane, "Select plane", "", column=0, row=3)
            wi.Radiobuttons(self.winpp, self.plane, "Plane", [["XY", "G17"], ["ZX", "G18"], ["YZ", "G19"]], column=0, row=4, columns=3, columnspan=1)
            # wi.Radiobuttons(self.winpp, self.plane, "Plane", [["XY","G17"],["ZX","G18"],["YZ","G19"],
            #                                        ["UV","G17.1"],["WU","G18.1"],["VW","G19.1"]], column=0, row=4, columns=3,columnspan=2)
            wi.Optionbutton(self.winpp, self.preamble_spindle_cw, "Turn on spindle clockwise", "M3", column=0, row=6)
            wi.Optionbutton(self.winpp, self.preamble_spindle_ccw, "Turn on spindle counter clockwise", "M4", column=0, row=7)
            wi.Optionbutton(self.winpp, self.preamble_mist, "Turn mist coolant on", "M7", column=0, row=8)
            wi.Optionbutton(self.winpp, self.preamble_flood, "Turn flood coolant on", "M8", column=0, row=9)
            wi.LabelEntry(self.winpp, self.preamble_gcode, "Individual g-code", "", column=0, row=10, width=20)
            tk.Label(self.winpp, text="Postamble", font="bold", bg="Dark grey").grid(column=0, row=11, columnspan=2, sticky="EW", padx=1)
            wi.Optionbutton(self.winpp, self.postamble_zsh, "Go to safety height", "", column=0, row=12)
            wi.Optionbutton(self.winpp, self.postamble_spindle_off, "Turn spindle off", "M5", column=0, row=13)
            wi.Optionbutton(self.winpp, self.postamble_coolant_off, "Turn coolant off", "M9", column=0, row=14)
            wi.LabelEntry(self.winpp, self.postamble_gcode, "Individual g-code", "", column=0, row=15, width=20)


class Baseclass(widgets.Widgets):  # ===========================================
    """Implements the basic variables, logic and widgets for the different gui"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        super(Baseclass, self).__init__(root)

        self.nco = ncclass_instance
        self.root = root
        self.winoffsetx = winoffsetx
        self.winoffsety = winoffsety

        # find the description for the following variables in <nclasses.py -> Basedata>
        self.objectname = tk.StringVar(self.root, "", "")
        self.tn = tk.IntVar(self.root, 6)
        self.td = tk.DoubleVar(self.root, 6.0)
        self.so = tk.DoubleVar(self.root, 50.0)
        self.frtd = tk.DoubleVar(self.root, 1000.0)
        self.frso = tk.DoubleVar(self.root, 1500.0)
        self.frz = tk.DoubleVar(self.root, 750.0)
        self.ss = tk.DoubleVar(self.root, 15000)
        self.zsh = tk.DoubleVar(self.root, 10.0)
        self.z0 = tk.DoubleVar(self.root, 0.0)
        self.z1 = tk.DoubleVar(self.root, -5.0)
        self.zi = tk.DoubleVar(self.root, 2.5)
        self.posx = tk.DoubleVar(self.root, 0.0)
        self.posy = tk.DoubleVar(self.root, 0.0)
        self.rx = tk.DoubleVar(self.root, 0.0)
        self.ry = tk.DoubleVar(self.root, 0.0)
        self.deg = tk.DoubleVar(self.root, 0.0)
        self.plane = tk.IntVar(self.root, 0)
        self.preamble_gcode = tk.StringVar(self.root, "", "")
        self.postamble_gcode = tk.StringVar(self.root, "", "")
        self.preamble_tool = tk.BooleanVar(self.root, False)
        self.preamble_zsh = tk.BooleanVar(self.root, False)
        self.preamble_plane = tk.BooleanVar(self.root, False)
        self.preamble_spindle_cw = tk.BooleanVar(self.root, False)
        self.preamble_spindle_ccw = tk.BooleanVar(self.root, False)
        self.preamble_mist = tk.BooleanVar(self.root, False)
        self.preamble_flood = tk.BooleanVar(self.root, False)
        self.postamble_zsh = tk.BooleanVar(self.root, False)
        self.postamble_spindle_off = tk.BooleanVar(self.root, False)
        self.postamble_coolant_off = tk.BooleanVar(self.root, False)

        self.parlist = ["objectname", "tn", "td", "so", "frtd", "frso", "frz", "ss", "zsh", "z0", "z1", "zi", "posx", "posy", "rx", "ry", "deg", "plane", "preamble_gcode",
        "postamble_gcode", "preamble_tool", "preamble_zsh", "preamble_plane", "preamble_spindle_cw", "preamble_spindle_ccw", "preamble_mist", "preamble_flood",
        "postamble_zsh", "postamble_spindle_off", "postamble_coolant_off"]  # list of relevant parameters (must be the same as in the ncclass)

        self.win = tk.Toplevel(root)  # create the class-window
        self.win.wm_title(self.nco.name)
        self.win.resizable(0, 0)
        winpos = "+" + str(self.root.winfo_x() + self.winoffsetx) + "+" + str(self.root.winfo_y() + self.winoffsety)
        self.win.geometry(winpos)
        self.win.protocol("WM_DELETE_WINDOW", self.Hide)
        self.win.bind("<Escape>", self.Hide)

        self.tooltable = ToolTable(self.win, self.tn, self.td)
        self.feednspeed = FeedAndSpeed(self.win, self.tn, self.td, self.ss, self.frtd, self.frso)

        self.prepostamble = PrePostamble(self.win, self.plane, self.preamble_gcode, self.postamble_gcode, self.preamble_tool, self.preamble_zsh,
                                         self.preamble_plane, self.preamble_spindle_cw, self.preamble_spindle_ccw, self.preamble_mist,
                                         self.preamble_flood, self.postamble_zsh, self.postamble_spindle_off, self.postamble_coolant_off)

        self.CreateBasewidgets(self.win)
        return self.win

    def Show(self):
        """Show the hidden window"""
        self.win.deiconify()
        self.win.lift()
        winpos = "+" + str(self.root.winfo_x() + self.winoffsetx) + "+" + str(self.root.winfo_y() + self.winoffsety)
        self.win.geometry(winpos)
        # self.win.update_idletasks()
        self.WriteDataToLogic()

    def Destroy(self):
        """Destroy the current window and update the ncclass before"""
        self.WriteDataToLogic()
        self.win.destroy()

    def Hide(self, *dummy):
        """Hide the current window"""
        self.win.withdraw()
        self.win.after_cancel(self.after)

    def GetDataFromLogic(self):
        """Update the gui with the data from the ncclass"""
        for p in self.parlist:
            try: getattr(self, p).set(getattr(self.nco, p))
            except: pass

    def WriteBaseDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        for p in self.parlist:
            try: setattr(self.nco, p, getattr(self, p).get())
            except: pass  # print("Error write nco: ", p)

    def CreateBasewidgets(self, f):
        """Create the basic widgets"""
        self.LabelEntry(f, 0, 1, 10, 10, self.objectname, "Name of object", "Individual name")
        # self.help = tk.Message(f, text="---", relief="sunken").grid(column=1, row=2, columnspan=10, sticky="EW")
        widget = self.LabelEntry(f, 0, 3, 1, 10, self.tn, "Tool Number", "#, <Right-click> to open tool table.")
        widget.bind("<Button-3>", lambda event: self.tooltable.show())
        widget = self.LabelEntry(f, 0, 4, 1, 10, self.td, "Tool Diameter", "[td] mm,in, <Right-click> to open tool table.")
        widget.bind("<Button-3>", lambda event: self.tooltable.show())
        self.LabelEntry(f, 0, 5, 1, 10, self.so, "Step over xy", "[so] % of tool diameter")
        self.LabelEntry(f, 0, 6, 1, 10, self.zi, "Increment z", "mm,in")
        widget = self.LabelEntry(f, 0, 7, 1, 10, self.frtd, "Feed rate xy @td", "mm/min,in/min, <Right-click> to open feed and speed calculator.")
        widget.bind("<Button-3>", lambda event: self.feednspeed.show())
        widget = self.LabelEntry(f, 0, 8, 1, 10, self.frso, "Feedrate xy @so", "mm/min,in/min, <Right-click> to open feed and speed calculator.")
        widget.bind("<Button-3>", lambda event: self.feednspeed.show())
        self.LabelEntry(f, 0, 9, 1, 10, self.frz, "Feedrate z", "mm/min,in/min")
        widget = self.LabelEntry(f, 0, 10, 1, 10, self.ss, "Spindle speed", "rpm, <Right-click> to open feed and speed calculator.")
        widget.bind("<Button-3>", lambda event: self.feednspeed.show())
        self.LabelEntry(f, 0, 11, 1, 10, self.zsh, "Safety height", "mm,in")
        self.LabelEntry(f, 0, 12, 1, 10, self.z0, "Start height", "mm,in")
        self.LabelEntry(f, 0, 13, 1, 10, self.z1, "End height", "mm,in")
        self.LabelEntry(f, 0, 14, 1, 10, self.posx, "Position x", "offset of the shape from origin\n[mm,in]")
        self.LabelEntry(f, 0, 15, 1, 10, self.posy, "Position y", "offset of the shape from origin\n[mm,in]")
        self.LabelEntry(f, 0, 16, 1, 10, self.rx, "Rotate X", "rotation point from origin\n[mm,in]")
        self.LabelEntry(f, 0, 17, 1, 10, self.ry, "Rotate Y", "rotation point from origin\n[mm,in]")
        self.LabelEntry(f, 0, 18, 1, 10, self.deg, "Rotation XY", "rotation around rotation point [°]")
        tk.Button(f, text="Set pre- and postamble", command=self.prepostamble.show).grid(column=0, row=19, columnspan=2, sticky="ew")


class CustomGcode(widgets.Widgets):  # =========================================
    """Gui for <CustomCode> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""

        self.nco = ncclass_instance
        self.root = root
        self.winoffsetx = winoffsetx
        self.winoffsety = winoffsety

        self.objectname = tk.StringVar(self.root, 0, "")

        self.win = tk.Toplevel(root)
        self.win.wm_title(self.nco.name)
        winpos = "+" + str(self.root.winfo_x() + self.winoffsetx) + "+" + str(self.root.winfo_y() + self.winoffsety)
        self.win.geometry(winpos)
        self.win.protocol("WM_DELETE_WINDOW", self.Hide)
        self.win.bind("<Escape>", self.Hide)

        self.LabelEntry(self.win, 0, 1, 3, 10, self.objectname, "Object name", "Individual name")
        self.textwidget = self.TextboxWithScrollbar(self.win, 1, 2, 1, 6, 66, 20, "nsew")
        widgets.ToolTip(self.textwidget, "Your custom g-code.")
        tk.Button(self.win, command=lambda: self.textwidget.yview(0), text="Pos1").grid(column=0, row=2, sticky="ew")
        tk.Button(self.win, command=lambda: self.textwidget.yview(tk.END), text="End").grid(column=0, row=3, sticky="ew")
        tk.Button(self.win, command=self.Delete, text="Delete\nall").grid(column=0, columnspan=1, row=4, sticky="ew")
        tk.Button(self.win, command=self.InsertFromClipboard, text="Insert from\nclipboard").grid(column=0, columnspan=1, row=5, sticky="ew")
        tk.Button(self.win, command=self.PasteFromClipboard, text="Paste from\nclipboard").grid(column=0, columnspan=1, row=6, sticky="ew")
        tk.Button(self.win, command=self.CopyToClipboard, text="Copy to\nclipboard").grid(column=0, columnspan=1, row=7, sticky="ew")

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def Show(self):
        """Show the hidden window"""
        self.win.deiconify()
        self.win.lift()
        winpos = "+" + str(self.root.winfo_x() + self.winoffsetx) + "+" + str(self.root.winfo_y() + self.winoffsety)
        self.win.geometry(winpos)
        self.WriteDataToLogic()

    def Hide(self, *dummy):
        """Hide the window"""
        self.win.withdraw()
        self.win.after_cancel(self.after)

    def Destroy(self):
        """Destroy the current window and update the ncclass before"""
        self.WriteDataToLogic()
        self.win.destroy()

    def GetDataFromLogic(self):
        """Update the gui with the data from the ncclass"""
        self.objectname.set(self.nco.objectname)
        self.textwidget.delete(1.0, tk.END)
        self.textwidget.insert(tk.END, self.nco.text)
        self.textwidget.yview(tk.END)

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.nco.objectname = self.objectname.get()
        self.nco.text = self.textwidget.get(1.0, tk.END)[:-1]
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)

    def CopyToClipboard(self):
        """Copy the content to the system clipboard"""
        self.win.clipboard_clear()
        self.win.clipboard_append(self.textwidget.get(1.0, tk.END)[:-1])

    def PasteFromClipboard(self):
        """Paste the content from the system clipboard"""
        if tkinter.messagebox.askokcancel("Paste from clipboard", "Replaces current content.\nSure?"):
            self.textwidget.delete(1.0, tk.END)
            self.textwidget.insert(tk.END, self.win.clipboard_get())
        self.win.lift()

    def InsertFromClipboard(self):
        """Insert the content from the system clipboard"""
        self.textwidget.insert(tk.INSERT, self.win.clipboard_get())

    def Delete(self):
        if tkinter.messagebox.askokcancel("Delete", "Sure?"):
            self.textwidget.delete(1.0, tk.END)
        self.win.lift()


class OutlineRectangle(Baseclass, widgets.Widgets):  # =========================
    """Gui for <OutlineRectangle> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(OutlineRectangle, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.w = tk.DoubleVar(self.win, 50)
        self.h = tk.DoubleVar(self.win, 25)
        self.contour = tk.IntVar(self.win, 0)
        self.climb = tk.BooleanVar(self.win, True)
        self.br = tk.BooleanVar(self.win, True)
        self.brw = tk.DoubleVar(self.win, 2.0)
        self.brh = tk.DoubleVar(self.win, 1.0)
        self.rsx = tk.DoubleVar(self.win, 0.0)
        self.rsy = tk.DoubleVar(self.win, 0.0)
        self.rsdeg = tk.DoubleVar(self.win, 0.0)

        self.parlist += ["w", "h", "contour", "climb", "br", "brw", "brh", "rsx", "rsy", "rsdeg"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.w, "Width", "mm,in")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.h, "Height", "mm,in")
        wi.Radiobuttons(self.win, self.contour, "Contour", [["inside", ""], ["exact", ""], ["outside", ""]], columns=1, column=4, row=5)
        self.Optionbutton(self.win, 4, 13, 1, self.br, "Bridges", "If checked, bridges with the given\nwidth and height are added.")
        self.entry_brw = self.LabelEntry(self.win, 4, 14, 1, 10, self.brw, "Bridges width", "mm,in")
        self.entry_brh = self.LabelEntry(self.win, 4, 15, 1, 10, self.brh, "Bridges height", "mm,in")
        self.LabelEntry(self.win, 4, 8, 1, 10, self.rsx, "Shape rotation x", "from shape center - mm,in")
        self.LabelEntry(self.win, 4, 9, 1, 10, self.rsy, "Shape rotation y", "from shape center - mm,in")
        self.LabelEntry(self.win, 4, 10, 1, 10, self.rsdeg, "Shape rotation", "°")
        wi.Radiobuttons(self.win, self.climb, "Machining\ndirection", [["conventional", ""], ["climb", ""]], columns=1, column=4, row=17)

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        if self.br.get():
            self.entry_brw.configure(state=tk.NORMAL)
            self.entry_brh.configure(state=tk.NORMAL)
        else:
            self.entry_brw.configure(state=tk.DISABLED)
            self.entry_brh.configure(state=tk.DISABLED)
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class OutlineCircle(Baseclass, widgets.Widgets):  # ============================
    """Gui for <OutlineCircle> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(OutlineCircle, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.r = tk.DoubleVar(self.win, 10.0)
        self.contour = tk.IntVar(self.win, 0)
        self.climb = tk.BooleanVar(self.win, True)
        self.br = tk.BooleanVar(self.win, True)
        self.brw = tk.DoubleVar(self.win, 2.0)
        self.brh = tk.DoubleVar(self.win, 1.0)

        self.parlist += ["r", "contour", "climb", "br", "brw", "brh"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.r, "Radius", "mm,in")
        wi.Radiobuttons(self.win, self.contour, "Contour", [["inside", ""], ["exact", ""], ["outside", ""]], columns=1, column=4, row=4)
        self.Optionbutton(self.win, 4, 7, 1, self.br, "Bridges", "If checked, bridges with the given\nwidth and height are added.")
        self.entry_brw = self.LabelEntry(self.win, 4, 8, 1, 10, self.brw, "Bridges width", "mm,in")
        self.entry_brh = self.LabelEntry(self.win, 4, 9, 1, 10, self.brh, "Bridges height", "mm,in")
        wi.Radiobuttons(self.win, self.climb, "Machining\ndirection", [["conventional", ""], ["climb", ""]], columns=1, column=4, row=17)

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        if self.br.get():
            self.entry_brw.configure(state=tk.NORMAL)
            self.entry_brh.configure(state=tk.NORMAL)
        else:
            self.entry_brw.configure(state=tk.DISABLED)
            self.entry_brh.configure(state=tk.DISABLED)
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class OutlineEllipse(Baseclass, widgets.Widgets):  # ===========================
    """Gui for <OutlineEllipse> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(OutlineEllipse, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.a = tk.DoubleVar(self.win, 10.0)
        self.b = tk.DoubleVar(self.win, 20.0)
        self.ai = tk.IntVar(self.win, 5)
        self.contour = tk.IntVar(self.win, 1)
        self.climb = tk.BooleanVar(self.win, True)
        self.br = tk.BooleanVar(self.win, True)
        self.brw = tk.DoubleVar(self.win, 2.0)
        self.brh = tk.DoubleVar(self.win, 1.0)

        self.parlist += ["a", "b", "ai", "contour", "climb", "br", "brw", "brh"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.a, "A", "mm,in")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.b, "B", "mm,in")
        self.LabelEntry(self.win, 4, 5, 1, 10, self.ai, "Angle resolution", "°")
        wi.Radiobuttons(self.win, self.contour, "Contour", [["inside", ""], ["exact", ""], ["outside", ""]], columns=1, column=4, row=6)
        wi.Radiobuttons(self.win, self.climb, "Machining\ndirection", [["conventional", ""], ["climb", ""]], columns=1, column=4, row=17)

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class OutlinePolygon(Baseclass, widgets.Widgets):  # ===========================
    """Gui for <OutlinePolygon> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(OutlinePolygon, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.scalex = tk.DoubleVar(self.win, 20.0)
        self.scaley = tk.DoubleVar(self.win, 20.0)
        self.x = tk.DoubleVar(self.win, 10.0)
        self.y = tk.DoubleVar(self.win, 5.0)
        self.cc = tk.IntVar(self.win, 2)
        self.close = tk.BooleanVar(self.win, True)
        self.rsx = tk.DoubleVar(self.win, 0.0)
        self.rsy = tk.DoubleVar(self.win, 0.0)
        self.rsdeg = tk.DoubleVar(self.win, 0.0)
        self.g64 = tk.DoubleVar(self.win, 0.01)

        self.parlist += ["scalex", "scaley", "x", "y", "cc", "close", "rsx", "rsy", "rsdeg", "g64"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.scalex, "scale x", "#, scale factor for x values in the list")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.scaley, "scale y", "#, scale factor for y values in the list")
        self.LabelEntry(self.win, 4, 5, 1, 10, self.rsx, "Shape rotation x", "mm,in")
        self.LabelEntry(self.win, 4, 6, 1, 10, self.rsy, "Shape rotation y", "mm,in")
        self.LabelEntry(self.win, 4, 7, 1, 10, self.rsdeg, "Shape rotation", "°")
        self.LabelEntry(self.win, 4, 8, 1, 10, self.g64, "Path blending\n(G64)", "mm,in")
        wi.Radiobuttons(self.win, self.cc, "Cutter\ncompensation", [["none", "G40"], ["left", "G41"], ["right", "G42"]], columns=1, column=4, row=10)
        self.LabelEntry(self.win, 4, 15, 1, 10, self.x, "x", "Selected/new x-value")
        self.LabelEntry(self.win, 4, 16, 1, 10, self.y, "y", "Selected/new y-value")
        tk.Button(self.win, text="Update\n xy-value", command=self.ObjectUpdate).grid(column=4, row=15, rowspan=2)
        self.Optionbutton(self.win, 4, 13, 1, self.close, "Close polygon", "Last position = First position")
        tk.Label(self.win, text="List of positions", justify="center").grid(column=7, row=3, columnspan=2, padx=0, pady=2, sticky="ew")
        self.lb = self.ListboxWithScrollbar(self.win, column=7, row=4, columnspan=2, rowspan=9, height=13, width=25, selectmode=tk.EXTENDED)
        self.lb.bind("<Double-1>", lambda x: self.ObjectEdit())
        tk.Button(self.win, text="Move up", command=self.ObjectsMoveUp).grid(column=7, row=13, rowspan=2)
        tk.Button(self.win, text="Move down", command=self.ObjectsMoveDown).grid(column=8, row=13, rowspan=2)
        tk.Button(self.win, text="Delete", command=self.ObjectDelete).grid(column=8, row=15, columnspan=1, rowspan=2)
        tk.Button(self.win, command=self.Import, text="Import file").grid(column=7, row=17, rowspan=2, columnspan=2)
        tk.Button(self.win, text="Insert G01", command=self.ObjectInsert).grid(column=7, row=15, rowspan=2)

        self.GetDataFromLogic()
        self.WriteDataToLogic()
        self.ListboxUpdate()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)

    def Import(self):
        """Import a dat file (eg. for airfoils"""
        fn = widgets.AskOpenFile("Import data file", "~", "", "Data file", ".dat")
        if not fn:
            return
        self.nco.Import(fn)
        self.ListboxUpdate()
        self.win.lift()

    def ObjectEdit(self):
        """Read the data of the selected object(segment) into the x-y widgets"""
        oi = self.lb.curselection()
        if oi:
            oi = int(oi[0])
            x, y = self.nco.GetPoly(oi)
            self.x.set(x)
            self.y.set(y)

    def ObjectUpdate(self):
        """Write the data of the x,y widgtet into the selcted object"""
        oi = self.lb.curselection()
        if oi:
            oi = int(oi[0])
            self.nco.ObjectUpdate(oi, self.x.get(), self.y.get())
            self.ListboxUpdate()
            self.lb.selection_set(oi)
            self.lb.see(oi)

    def ObjectInsert(self):
        """Insert a new segmnet based on x-y values of the widgets"""
        oi = self.lb.curselection()
        if oi:
            oi = int(oi[0]) + 1
        else:
            oi = 0
        self.nco.ObjectInsert(oi, self.x.get(), self.y.get())
        self.ListboxUpdate()
        self.lb.selection_set(oi)

    def ObjectDelete(self):
        """Delete the selected object/segment"""
        indexes = self.lb.curselection()
        if indexes and \
           tkinter.messagebox.askokcancel("Delete", "Delete selected object(s)?"):
            self.nco.ObjectDelete(indexes)
            self.ListboxUpdate()
            self.win.lift()

    def ObjectsMoveUp(self):
        """Changes the ordner of the cerated objects"""
        indexes = self.lb.curselection()
        if indexes:
            indexes = self.nco.ObjectsMoveUp(indexes)
            self.ListboxUpdate()
            for i in indexes:
                self.lb.selection_set(i)
            self.lb.see(i)

    def ObjectsMoveDown(self):
        """Changes the ordner of the cerated objects"""
        indexes = self.lb.curselection()
        if indexes:
            indexes = self.nco.ObjectsMoveDown(indexes)
            self.ListboxUpdate()
            for i in indexes:
                self.lb.selection_set(i)
            self.lb.see(i)

    def ListboxUpdate(self):
        """Update the content of the listbox"""
        self.lb.delete(0, tk.END)
        for n in self.nco.GetObjectNames():
            self.lb.insert(tk.END, n)


class PocketRectangle(Baseclass, widgets.Widgets):  # ==========================
    """Gui for <PocketRectangle> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(PocketRectangle, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.w = tk.DoubleVar(self.win, 100.0)
        self.h = tk.DoubleVar(self.win, 50.0)
        self.climb = tk.BooleanVar(self.win, True)
        self.corners = tk.BooleanVar(self.win, False)

        self.parlist += ["w", "h", "climb", "corners"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.w, "Width", "mm,in")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.h, "Height", "mm,in")
        self.Optionbutton(self.win, 4, 5, 1, self.corners, "Corners", "mill out corners")
        wi.Radiobuttons(self.win, self.climb, "Machining\ndirection", [["conventional", ""], ["climb", ""]], columns=1, column=4, row=17)

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class PocketCircle(Baseclass, widgets.Widgets):  # =============================
    """Gui for <PocketCircle> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(PocketCircle, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.ri = tk.DoubleVar(self.win, 10.0)
        self.ra = tk.DoubleVar(self.win, 50.0)
        self.climb = tk.BooleanVar(self.win, True)

        self.parlist += ["ri", "ra", "climb"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.ri, "Inner radius", "mm,in")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.ra, "Outer radius", "mm,in")
        wi.Radiobuttons(self.win, self.climb, "Machining\ndirection", [["conventional", ""], ["climb", ""]], columns=1, column=4, row=17)

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class Grill(Baseclass, widgets.Widgets):  # ====================================
    """Gui for <Grill> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(Grill, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.w = tk.DoubleVar(self.win, 80.0)
        self.h = tk.DoubleVar(self.win, 40.0)
        self.shape = tk.IntVar(self.win, 0)
        self.dist = tk.DoubleVar(self.win, 2.0)
        self.peck = tk.BooleanVar(self.win, False)

        self.parlist += ["w", "h", "shape", "dist", "peck"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.w, "Width, Radius, A", "mm,in")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.h, "Height, B", "mm,in")
        self.LabelEntry(self.win, 4, 5, 1, 10, self.dist, "Hole distance", "mm,in")
        wi.Radiobuttons(self.win, self.shape, "Shape", [["rectangle", ""], ["circle", ""], ["ellipse", ""]], columns=1, column=4, row=6)
        wi.Radiobuttons(self.win, self.peck, "Plunge\nstrategy", [["linear", ""], ["peck", ""]], columns=1, column=4, row=9)
        self.canvas = tk.Canvas(self.win, height=200, width=200, bg="white", bd=1, relief="sunken")
        self.canvas.grid(column=4, row=11, columnspan=2, rowspan=10, sticky="NE")

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.UpdateCanvas()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)

    def UpdateCanvas(self):
        """Display the result ina the canvas"""
        self.canvas.delete("all")
        x = y = x_ = y_ = None
        r = self.nco.td / 2
        s = 200 / (max([self.nco.w, self.nco.h]))
        for o in self.nco.Update():
            try:
                if not o.x == None: x = o.x
                if not o.y == None: y = o.y
                if not x == None and not y == None and not o.z == None and (o.name == "G01" or o.name == "G83"):
                    self.canvas.create_oval((x - r, y - r, x + r, y + r))
            except:
                pass
            x_ = x
            y_ = y
        self.canvas.scale("all", 0, 0, s, -s)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL), offset="center")


class Bezel(Baseclass, widgets.Widgets):  # ====================================
    """Gui for <Bezel> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(Bezel, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.ri = tk.DoubleVar(self.win, 50.0)
        self.romaj = tk.DoubleVar(self.win, 50.0)
        self.romin = tk.DoubleVar(self.win, 50.0)
        self.a0 = tk.DoubleVar(self.win, 50.0)
        self.a1 = tk.DoubleVar(self.win, 50.0)
        self.div = tk.IntVar(self.win, 50)
        self.divmaj = tk.IntVar(self.win, 50)

        self.parlist += ["ri", "romaj", "romin", "a0", "a1", "div", "divmaj"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.ri, "Inner radius", "mm,in")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.romaj, "Outer radius major tick", "mm,in")
        self.LabelEntry(self.win, 4, 5, 1, 10, self.romin, "Outer radius minor tick", "mm,in")
        self.LabelEntry(self.win, 4, 6, 1, 10, self.a0, "Start angle", "°")
        self.LabelEntry(self.win, 4, 7, 1, 10, self.a1, "End angle", "°")
        self.LabelEntry(self.win, 4, 8, 1, 10, self.div, "Divisions", "#")
        self.LabelEntry(self.win, 4, 9, 1, 10, self.divmaj, "Divisions major tick", "#")
        self.canvas = tk.Canvas(self.win, height=200, width=200, bg="white", bd=1, relief="sunken")
        self.canvas.grid(column=4, row=10, columnspan=2, rowspan=10, sticky="NE")

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.UpdateCanvas()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)

    def UpdateCanvas(self):
        """Display the result in the canvas"""
        self.canvas.delete("all")
        self.canvas.create_line(80, 100, 120, 100, fill='green')
        self.canvas.create_line(100, 80, 100, 120, fill='green')
        x = y = x_ = y_ = None
        s = 200 / (max([self.nco.ri, self.nco.romaj, self.nco.romin]) * 2)
        for o in self.nco.Update():
            try:
                if not o.x == None:
                    x = o.x
                if not o.y == None:
                    y = o.y
                if not x == None and not y == None and not x_ == None and not y_ == None and o.name == "G01":
                    p = mu.PointRotate([x, y], [self.rx.get(), self.ry.get()], self.deg.get())
                    x1, y1 = p[0], p[1]
                    p = mu.PointRotate([x_, y_], [self.rx.get(), self.ry.get()], self.deg.get())
                    x1_, y1_ = p[0], p[1]
                    self.canvas.create_line((100 + x1_ * s, 100 + y1_ * s * -1, 100 + x1 * s, 100 + y1 * s * -1))
                x_, y_ = x, y
            except:
                pass
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL), offset="center")


class DrillMatrix(Baseclass, widgets.Widgets):  # ==============================
    """Gui for <DrillMatrix> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(DrillMatrix, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.nx = tk.IntVar(self.win, 5)
        self.ny = tk.IntVar(self.win, 2)
        self.dx = tk.DoubleVar(self.win, 2.54)
        self.dy = tk.DoubleVar(self.win, 5.08)
        self.peck = tk.BooleanVar(self.win, False)
        self.center = tk.BooleanVar(self.win, True)

        self.parlist += ["nx", "ny", "dx", "dy", "peck", "center"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.nx, "n-x", "#, number of holes in x")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.ny, "n-y", "#, number of holes in y")
        self.LabelEntry(self.win, 4, 5, 1, 10, self.dx, "x distance", "mm/in")
        self.LabelEntry(self.win, 4, 6, 1, 10, self.dy, "y-distance", "mm/in")
        self.Optionbutton(self.win, 4, 7, 1, self.center, "Center", "")
        wi.Radiobuttons(self.win, self.peck, "Plunge\nstrategy", [["linear", ""], ["peck", ""]], columns=1, column=4, row=8)
        self.canvas = tk.Canvas(self.win, height=200, width=200, bg="white", bd=1, relief="sunken")
        self.canvas.grid(column=4, row=10, columnspan=2, rowspan=10, sticky="NE")

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.UpdateCanvas()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)

    def UpdateCanvas(self):
        """Display the rsult in the canvas"""
        self.canvas.delete("all")
        self.canvas.create_line((-10, 0, 10), fill="red")  # Paint cross at origin
        self.canvas.create_line((0, 10, 0, -10), fill="red")
        s = 5
        if self.nco.ParametersOk():
            x = y = x_ = y_ = None
            r = self.nco.td / 2.0
            s = 200 / max([self.nco.nx * self.nco.dx, self.nco.ny * self.nco.dy])
            for o in self.nco.Update():
                try:
                    if not o.x == None: x = o.x
                    if not o.y == None: y = o.y
                    if (o.name == "G01" or o.name == "G83"):
                        self.canvas.create_oval(((x - r) * s, (y - r) * s * -1, (x + r) * s, (y + r) * s * -1))
                except:
                    pass
        # self.canvas.scale("all", 0, 0, s, -s)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL), offset="center")


class Slot(Baseclass, widgets.Widgets):  # =====================================
    """Gui for <Slot> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(Slot, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.dx = tk.DoubleVar(self.win, 50.0)
        self.dy = tk.DoubleVar(self.win, 50.0)
        self.peck = tk.BooleanVar(self.win, False)

        self.parlist += ["dx", "dy", "peck"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.dx, "Delta x", "mm,in")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.dy, "Delty y", "mm, in")
        wi.Radiobuttons(self.win, self.peck, "Plunge\nstrategy", [["linear", ""], ["peck", ""]], columns=1, column=4, row=8)

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class PocketCircularArc(Baseclass, widgets.Widgets):  # ========================
    """Gui for <PocketCircularArc> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(PocketCircularArc, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.ri = tk.DoubleVar(self.win, 25.0)
        self.ro = tk.DoubleVar(self.win, 50.0)
        self.a0 = tk.DoubleVar(self.win, 0.0)
        self.a1 = tk.DoubleVar(self.win, 90.0)

        self.parlist += ["ri", "ro", "a0", "a1"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.ri, "Inner radius", "mm,in")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.ro, "Outer radius", "mm,in")
        self.LabelEntry(self.win, 4, 6, 1, 10, self.a0, "Start angle", "°")
        self.LabelEntry(self.win, 4, 7, 1, 10, self.a1, "End angle", "°")

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class OutlineCircularArc(Baseclass, widgets.Widgets):  # =======================
    """Gui for <OutlineCircularArc> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(OutlineCircularArc, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.ri = tk.DoubleVar(self.win, 25.0)
        self.ro = tk.DoubleVar(self.win, 50.0)
        self.a0 = tk.DoubleVar(self.win, 0.0)
        self.a1 = tk.DoubleVar(self.win, 90.0)
        self.contour = tk.IntVar(self.win, 1)
        # self.climb = tk.BooleanVar(self.win, True)
        self.br = tk.BooleanVar(self.win, True)
        self.brw = tk.DoubleVar(self.win, 2)
        self.brh = tk.DoubleVar(self.win, 1)

        self.parlist += ["ri", "ro", "a0", "a1", "contour", "br", "brw", "brh"]

        self.LabelEntry(self.win, 4, 3, 1, 10, self.ri, "Inner radius", "mm,in")
        self.LabelEntry(self.win, 4, 4, 1, 10, self.ro, "Outer radius", "mm,in")
        self.LabelEntry(self.win, 4, 5, 1, 10, self.a0, "Start angle", "°")
        self.LabelEntry(self.win, 4, 6, 1, 10, self.a1, "End angle", "°")
        wi.Radiobuttons(self.win, self.contour, "Contour", [["inside", ""], ["exact", ""], ["outside", ""]], columns=1, column=4, row=7)
        # self.Optionbutton(self.win, 4, 10, 1, self.br, "Bridges", "tbd")
        # self.entry_brw = self.LabelEntry(self.win, 4, 11, 1, 10, self.brw, "Bridges width", "mm,in")
        # self.entry_brh = self.LabelEntry(self.win, 4, 12, 1, 10, self.brh, "Bridges height", "mm,in")

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class Text(Baseclass, widgets.Widgets):  # =====================================
    """Gui for <Text> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(Text, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.fontfile = tk.StringVar(self.win, "")
        self.arcres = tk.DoubleVar(self.win, 10.0)
        self.char_height = tk.DoubleVar(self.win, 10.0)
        self.char_width = tk.DoubleVar(self.win, 10.0)
        self.char_space = tk.DoubleVar(self.win, 100.0)
        self.line_space = tk.DoubleVar(self.win, 10.0)
        # self.parsed = tk.BooleanVar(self.win, False)
        self.mirrorh = tk.BooleanVar(self.win, False)
        self.mirrorv = tk.BooleanVar(self.win, False)
        self.arcjust = tk.IntVar(self.win, 0)
        self.g64 = tk.DoubleVar(self.win, 0,0)
        self.align = tk.IntVar(self.win, 0)
        self.radius = tk.DoubleVar(self.win, 50.0)

        self.parlist += ["fontfile", "arcres", "char_height", "char_width", "char_space", "line_space", "mirrorh", "mirrorv", "arcjust", "g64", "align", "radius"]

        wi.LabelEntry(self.win, self.char_width, "Character width", "mm/in,\nWidth of the widest character in the font.\n0 = no scaling", column=4, row=3)
        wi.LabelEntry(self.win, self.char_height, "Character height", "mm/in\nHeight of the highest character in the font.\n0 = no scaling", column=4, row=4)
        wi.LabelEntry(self.win, self.char_space, "Character space", "mm/in\nSpace between chars", column=4, row=5)
        wi.LabelEntry(self.win, self.line_space, "Line space", "mm/in\nSpace between lines", column=4, row=6)

        wi.LabelEntry(self.win, self.radius, "Radius", "mm/in\nBend text around a radius. 0=linear text" , column=4, row=7)
        wi.Radiobuttons(self.win, self.arcjust, "Text-Arc\norientation", [["", "arc-center to text bottom"], ["", "arc-center to text top"]], column=4, row=10, columns=2)

        wi.Optionbutton(self.win, self.mirrorv, "Mirror Y", "Mirror the text vertically", column=4, row=8)
        wi.Optionbutton(self.win, self.mirrorh, "Mirror X", "Mirror the text horizontally", column=4, row=9)

        wi.Radiobuttons(self.win, self.align, "Text alignment", [["", "top left"], ["", "top center"], ["", "top right"]], column=6, row=10, columns=3)

        wi.LabelEntry(self.win, self.g64, "Blend (G64)", "mm/in", column=6, row=3)
        # wi.Radiobuttons(self.win, self.align, "Text alignment", [["","top left"],["","top center"],["","top right"],
        # ["","center left"],["","center"],["","center right"],["","bottom left"],["","bottom center"],["","bottom right"]], columns=3, column=4, row=8)
        wi.LabelEntry(self.win, self.fontfile, "Font file", "Filename of the font. If nothing, loading the font was not successful.", column=6, row=6)
        wi.LabelEntry(self.win, self.arcres, "Arc resolution", "°\nArcs in font characters are split into line segments.\nTakes effect after loading a font only!", column=6, row=7)
        tk.Button(self.win, command=self.LoadFont, text="Load Font").grid(column=6, row=4, rowspan=2, columnspan=1)
        tk.Button(self.win, command=self.ShowFont, text="Show Font").grid(column=7, row=4, rowspan=2, columnspan=1)
        self.textwidget = wi.TextboxWithScrollbar(self.win, column=4, row=12, columnspan=4, rowspan=8, width=55, height=14, sticky="nsew")

        self.GetDataFromLogic()
        self.textwidget.delete(1.0, tk.END)
        self.textwidget.insert(tk.END, self.nco.text)
        self.textwidget.yview(tk.END)
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        try:
            self.nco.text = self.textwidget.get(1.0, tk.END)[:-1]
        except:
            pass
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)

    def ShowFont(self):
        """Write all available characters of the font to the text widget"""
        self.textwidget.delete(1.0, tk.END)
        self.textwidget.insert(tk.END, self.nco.GetWholeFont())
        self.textwidget.yview(tk.END)

    def LoadFont(self):
        """Load a CXF font"""
        fn = widgets.AskOpenFile("Load CXF font", font2vector.DIR, "", "Font file", ".cxf")
        if not fn:
            return
        self.nco.LoadFont(fn)
        self.win.lift()


class Relief(Baseclass, widgets.Widgets):  # ===================================  UNDER DEVELOPMENT!!!
    """Gui for <Relief> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        super(Relief, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.fn_image = tk.StringVar(self.win, "")
        self.image_width = tk.IntVar(self.win, 0)
        self.image_height = tk.IntVar(self.win, 0)
        self.scale = tk.DoubleVar(self.win, 0.0)
        self.image = None

        self.parlist += ["fn_image", "scale"]

        tk.Label(self.win, text="***UNDER DEVELOPMENT***").grid(column=4, row=7, columnspan=3)
        wi.LabelEntry(self.win, self.fn_image, "Image file", help="gif only!", column=4, row=3)
        widget = wi.LabelEntry(self.win, self.image_width, "Image width", help="px", column=4, row=4)
        widget.configure(state=tk.DISABLED)
        widget = wi.LabelEntry(self.win, self.image_height, "Image height", help="px", column=4, row=5)
        widget.configure(state=tk.DISABLED)
        wi.LabelEntry(self.win, self.scale, "Scale", help="mm/px, in/px", column=4, row=6)
        tk.Button(self.win, command=self.LoadImage, text="Load\nImage").grid(column=6, row=3, rowspan=3)
        tk.Button(self.win, command=self.nco.Calc, text="Calc").grid(column=6, row=6, rowspan=1)
        self.canvas = tk.Canvas(self.win, height=320, width=320, bg="white", bd=1, relief="sunken")
        self.canvas.grid(column=4, row=8, columnspan=3, rowspan=12, sticky="NE")

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)

    def LoadImage(self):
        """Load a CXF font"""
        fn = widgets.AskOpenFile("Load picture", "", "", "Picture", ".gif")
        if not fn:
            return
        self.image = self.nco.LoadImage(fn)
        if not self.image == None:
            self.fn_image.set(fn)
            w, h = self.image.size
            self.image_width.set(w)
            self.image_height.set(h)
            self.image2 = tk.PhotoImage(file=fn)
            self.canvas_image = self.canvas.create_image(160, 160, anchor=tk.CENTER, image=self.image2)
        else:
            self.fn_image.set("")
        self.win.lift()


class Subroutine(object):  # ===================================================
    """Gui for <Subroutine> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        self.nco = ncclass_instance
        self.root = root
        self.winoffsetx = winoffsetx
        self.winoffsety = winoffsety

        self.objectname = tk.StringVar(0, "")
        self.name = tk.StringVar(0, "")
        self.incsub = tk.BooleanVar(0, True)
        self.number = None

        self.win = tk.Toplevel(root)
        self.win.wm_title(self.nco.name)
        winpos = "+" + str(self.root.winfo_x() + self.winoffsetx) + "+" + str(self.root.winfo_y() + self.winoffsety)
        self.win.geometry(winpos)
        self.win.protocol("WM_DELETE_WINDOW", self.Hide)

        wi.LabelEntry(self.win, self.objectname, "Name of object", help="Individual name", column=0, row=0, columnspan=6)
        tk.Label(self.win, text="Subroutine:", anchor="e").grid(column=0, row=1, columnspan=1, sticky="e")
        tk.Label(self.win, textvariable=self.name, anchor="w").grid(column=1, row=1, columnspan=3, sticky="w")
        self.lb = wi.ListboxWithScrollbar(self.win, column=4, row=2, columnspan=2, rowspan=15, width=15, height=20)
        self.lb.bind("<Double-1>", lambda x: self.SelectSubroutine())
        for s in ngcsub.SUBROUTINES:
            self.lb.insert(tk.END, s.name)
        wi.Optionbutton(self.win, self.incsub, "Include\nsubroutine",
        help="Include the subroutine\ninto the g-code output", column=4, row=15, columnspan=1, rowspan=2)

        self.valuelist = []
        self.parlist = []
        self.helplist = []
        c = r = 0
        for p in range(30):
            self.parlist.append(tk.StringVar(0, "Parameter" + str(p + 1)))
            self.valuelist.append(tk.StringVar())
            tk.Label(self.win, textvariable=self.parlist[-1], anchor="e", width=10).grid(column=0 + c, row=2 + p + r, padx=0, pady=2, sticky="e")
            widget = tk.Entry(self.win, text=self.valuelist[-1], justify="center", width=5)
            widget.grid(column=1 + c, row=2 + p + r, padx=0, pady=2, sticky="e")
            self.helplist.append(wi.ToolTip(widget, "#" + str(p + 1)))
            if p == 14:
                c = 2
                r = -15
        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def SelectSubroutine(self):
        oi = self.lb.curselection()
        if oi:
            self.number = int(oi[0])
            self.UpdateWidgets(self.number)

    def UpdateWidgets(self, num):
        if num == None: return
        i = 0
        for i, p in enumerate(ngcsub.SUBROUTINES[num].parlist):
            self.parlist[i].set(p.name)
            self.helplist[i].text = p.comment

        for v in range(30 - i - 1):
            self.parlist[i + v + 1].set("")
            self.valuelist[i + v + 1].set("")
            self.helplist[i + v + 1].text = "#" + str(i + v + 2)

        self.name.set(ngcsub.SUBROUTINES[num].name)

    def Show(self):
        """Show the hidden window"""
        self.win.deiconify()
        self.win.lift()
        winpos = "+" + str(self.root.winfo_x() + self.winoffsetx) + "+" + str(self.root.winfo_y() + self.winoffsety)
        self.win.geometry(winpos)
        self.WriteDataToLogic()

    def Hide(self):
        """Hide the window"""
        self.win.withdraw()
        self.win.after_cancel(self.after)

    def Destroy(self):
        """Destroy the current window and update the ncclass before"""
        self.WriteDataToLogic()
        self.win.destroy()

    def GetDataFromLogic(self):
        """Update the gui with the data from the ncclass"""
        self.objectname.set(self.nco.objectname)
        self.number = self.nco.number
        self.incsub.set(self.nco.incsub)
        for i, v in enumerate(self.nco.valuelist):
            self.valuelist[i].set(v)
        self.UpdateWidgets(self.number)

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        try:
            self.nco.objectname = self.objectname.get()
            self.nco.number = self.number
            self.nco.valuelist = []
            self.nco.incsub = self.incsub.get()
            for v in self.valuelist:
                self.nco.valuelist.append(v.get())
        except:
            pass
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class Counterbore(Baseclass):  # =========================================
    """Gui for <CustomCode> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""

        super(Counterbore, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        self.d = tk.DoubleVar(self.win, 0.0)
        self.d1 = tk.DoubleVar(self.win, 0.0)
        self.T = tk.DoubleVar(self.win, 0.0)
        self.t = tk.DoubleVar(self.win, 0.0)
        self.index_dt = 0

        self.parlist += ["d", "d1", "T", "t"]

        tk.Label(self.win, text="***UNDER DEVELOPMENT***").grid(column=2, row=6, columnspan=2)

        self.lb = wi.ListboxWithScrollbar(self.win, column=2, row=3, columnspan=2, rowspan=3, width=40, height=4)
        self.lb.bind("<Double-1>", lambda x: self.SelectTable())
        for f in counterbore.TABLES:
            self.lb.insert(tk.END, f.description)

        self.header = tk.StringVar(0, "")
        self.l_header = tk.Label(self.win, textvariable=self.header)
        self.l_header.grid(column=2, row=7, columnspan=2, sticky="w")
        self.l_header.configure(font=("Courier New", "10", "normal"))

        self.lb_drilldata = wi.ListboxWithScrollbar(self.win, column=2, row=8, columnspan=2, rowspan=7, width=40, height=9)
        self.lb_drilldata.configure(font=("Courier New", "10", "normal"))
        self.lb_drilldata.bind("<Double-1>", lambda x: self.SelectDrill())
        self.FillDrillData(0)

        wi.LabelEntry(self.win, self.d, "Through hole diameter [d] ", help="mm/in", column=2, row=15, columnspan=1)
        wi.LabelEntry(self.win, self.d1, "Head sink hole diameter [d1] ", help="mm/in", column=2, row=16, columnspan=1)
        wi.LabelEntry(self.win, self.T, "Sinkhole depth [T]", help="mm/in", column=2, row=17, columnspan=1)
        wi.LabelEntry(self.win, self.t, "Washer height", help="mm/in", column=2, row=18, columnspan=1)

        tk.Label(self.win, text="Use the <End height> to define\nthe maximum depth of the through hole.").grid(column=2, columnspan=2, row=19)

        self.GetDataFromLogic()
        self.WriteDataToLogic()

    def FillDrillData(self, n):
        self.lb_drilldata.delete(0, tk.END)
        h = counterbore.TABLES[n].table[n].GetHeaders()
        header = "%6s %7s %7s %7s %7s" % (h[0], h[1], h[2], h[3], h[4])
        self.header.set(header)
        for c in counterbore.TABLES[n].table:
            data = "%6s %7s %7s %7s %7s" % (c.name, c.d, c.d1, c.d2, c.T)
            self.lb_drilldata.insert(tk.END, data)

    def SelectTable(self):
        ti = self.lb.curselection()
        if ti:
            ti = int(ti[0])
            self.index_dt = ti
            self.FillDrillData(ti)

    def SelectDrill(self):
        i = self.lb_drilldata.curselection()
        if i:
            i = int(i[0])
            self.d.set(counterbore.TABLES[self.index_dt].table[i].d)
            self.d1.set(counterbore.TABLES[self.index_dt].table[i].d1)
            self.T.set(counterbore.TABLES[self.index_dt].table[i].T)

    def Show(self):
        """Show the hidden window"""
        self.win.deiconify()
        self.win.lift()
        winpos = "+" + str(self.root.winfo_x() + self.winoffsetx) + "+" + str(self.root.winfo_y() + self.winoffsety)
        self.win.geometry(winpos)
        self.WriteDataToLogic()

    def Hide(self):
        """Hide the window"""
        self.win.withdraw()
        self.win.after_cancel(self.after)

    def Destroy(self):
        """Destroy the current window and update the ncclass before"""
        self.WriteDataToLogic()
        self.win.destroy()

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


class TEMPLATE(Baseclass):  # ==================================================
    """Gui for <tbd> ncclass"""

    def __init__(self, root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY):
        """Init variables and create widgets"""
        self.win = super(TEMPLATE, self).__init__(root, ncclass_instance, winoffsetx=WINPOSX, winoffsety=WINPOSY)

        # variables (use same names as in the logic class, otherwise GetDataFromLogic and WriteDataToLogic will fail)
        self.w = tk.DoubleVar(0, 50)

        # add the names as strings of all relevant parameters for the logic
        self.parlist += [""]

        # create widgets
        wi.LabelEntry(self.win, self.w, "Width", help="mm,in", column=4, row=3)

        self.GetDataFromLogic()  # remove if Baseclass it not derived
        self.WriteDataToLogic()  # mandatory to periodically update the logic module

    def WriteDataToLogic(self):
        """Update the ncclass with the data from the gui"""
        self.WriteBaseDataToLogic()
        self.after = self.win.after(TIME_UPDATE, self.WriteDataToLogic)


# ==============================================================================
# List of all available GUI-Classes (need to be the same order as the NC-Classes)
GUICLASSES = [CustomGcode,
              OutlineRectangle,
              OutlineCircle,
              OutlineCircularArc,
              OutlineEllipse,
              OutlinePolygon,
              PocketRectangle,
              PocketCircle,
              PocketCircularArc,
              Slot,
              DrillMatrix,
              Grill,
              Bezel,
              Text,
              Relief,
              Subroutine,
              Counterbore]
