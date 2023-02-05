#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Provides semi-automatic creation of widgets.

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
170319    Erik Schuster   First version
170521    Erik Schuster   Started to create single defs instead a class <Widgets>
                          ToolTip optimised.
170529    Erik Schuster   Added rowspan option to <def Optionbutton>

ToDo:
- Move File-Dialogs to seperate module
- Rethink ToolTip class, since ist does not work directly from other modules
- Actually not Widgets class needed. Better without!
"""

import Tkinter as tk
import tkMessageBox
import tkFileDialog

VERSION = "170529"                                                              # version of this file (jjmmtt)

TOOLTIP_SHOW = True                                                             # flag to enable/disable the tool tips

def ValidateInteger(d, i, P, s, S, v, V, W):  # ================================
    """Validate the user input in widgtes for integer"""
    if not P == "" and not P == "-":
        try:
            int(P)
        except ValueError:
            return False
    return True
vInteger = ((ValidateInteger),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')


def ValidateDouble(d, i, P, s, S, v, V, W):  # =================================
    """Validate the user input in widgtes for double"""
    if not P == "" and not P == "." and not P == "-" \
       and not P == "-." and not P == "," and not P == "-,":
        try:
            float(P)
        except ValueError:
            return False
    return True
vDouble = ((ValidateDouble),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')


def AskOpenFile(title, initaldir, initalfile, extname, ext):  # ================
    #title = Title of dialog
    #initaldir = inital dir name
    #initalfile = inital file name
    #extname = Name of extension
    #ext = Extension
    #returnvalue = Path to selected file, false if cancelled
    #define options for opening files
    file_opt = options = {}
    options['defaultextension'] = ext
    options['filetypes'] = [ (extname, ext), ('all files', '.*')]
    options['initialdir'] = initaldir
    options['initialfile'] = initalfile
    options['multiple'] = 0
    options['title'] = title
    filename = tkFileDialog.askopenfilename(**file_opt)
    return filename


def AskSaveFile(title, initaldir, initalfile, extname, ext):  # ================
    #title = Title of dialog
    #initaldir = inital dir name
    #initalfile = inital file name
    #extname = Name of extension
    #ext = Extension
    #returnvalue = Path to selected file, false if cancelled
    #define options for opening files
    file_opt = options = {}
    options['title'] = title
    options['initialdir'] = initaldir
    options['initialfile'] = initalfile
    options['defaultextension'] = ext
    options['filetypes'] = [(extname, ext), ('all files', '.*')]
    filename = tkFileDialog.asksaveasfilename(**file_opt)
    return filename


class ToolTip(object):  # ======================================================
    """Implements a tool-tip for mouse-over event"""
    
    def __init__(self, widget, tooltiptext):
        self.widget = widget
        self.text = tooltiptext
        self.tipwindow = None
        self.widget.bind('<Enter>', lambda x: self.showtip(self.text))
        self.widget.bind('<Leave>', self.hidetip)

    def showtip(self, text):
        if not self.tipwindow==None or not text or not TOOLTIP_SHOW: return
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        self.tipwindow = tk.Toplevel(self.widget)
        self.tipwindow.wm_overrideredirect(1)
        self.tipwindow.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tipwindow, text=text, justify="left", fg="dark green",
                      background="pale green", relief="solid", borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.grid(ipadx=1)

    def hidetip(self, event):
        try: self.tipwindow.destroy()
        except: pass
        self.tipwindow = None


class Widgets(object):  # ======================================================
    """Provides semi automatic creation of widgets - DEPRECATED - Do not use for new classes!"""

    def __init__(self, root):
        self.vDouble = (root.register(self.ValidateDouble),
                        '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.vInteger = (root.register(self.ValidateInteger),
                        '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

    def ValidateInteger(self, d, i, P, s, S, v, V, W):
        if not P == "" and not P == "-":
            try:
                int(P)
            except ValueError:
                return False
        return True

    def ValidateDouble(self, d, i, P, s, S, v, V, W):
        if not P == "" and not P == "." and not P == "-" \
           and not P == "-." and not P == "," and not P == "-,":
            try:
                float(P)
            except ValueError:
                return False
        return True
        
    def Description(self, fr, desc="", **par):
        """Adds a decription frame with text"""
        if desc == "":
            desc = self.__class__.__name__
        tk.Label(fr, text=desc, font="bold", bg="dark orange")\
            .grid(par, pady=0, sticky="ew")

    def LabelEntry(self, fr, col, row, cs, w, var, txt, hlp):
        if txt.count("\n") > 0:
            rs = txt.count("\n") + 1
        else:
            rs = 1
        tk.Label(fr, text=txt, justify="right").grid(column=col, row=row, rowspan=rs, padx=0, pady=2, sticky="e")
        if (type(var.get()) is int):
            widget = tk.Entry(fr, textvariable=var, width=w, justify=tk.CENTER, validate="key",
                validatecommand=self.vInteger)
        elif (type(var.get()) is int):
            widget = tk.Entry(fr, textvariable=var, width=w, justify=tk.CENTER, validate="key",
                validatecommand=self.vDouble)
        elif (type(var.get()) is float):
            widget = tk.Entry(fr, textvariable=var, width=w, justify=tk.CENTER, validate="key",
                validatecommand=self.vDouble)
        else:
            widget = tk.Entry(fr, textvariable=var, width=w, justify=tk.LEFT)
        widget.grid(column=col + 1, row=row, columnspan=cs, rowspan=rs, padx=0, sticky="we")
        ToolTip(widget, hlp)
        return widget

    def ListboxWithScrollbar(self, target, column=0, row=0, listvariable=None, width=20, height=10, selectmode=tk.SINGLE, sticky="NSEW", rowspan=1, columnspan=1):
        f = tk.Frame(target)
        f.grid(column=column, row=row, columnspan=columnspan, rowspan=rowspan, sticky=sticky)
        lb = tk.Listbox(f, listvariable=listvariable, selectmode=selectmode, width=width, height=height, exportselection=0)
        lb.grid(column=0, row=0, sticky="NS")
        widget = tk.Scrollbar(f, command=lb.yview, width=15)
        widget.grid(column=1, row=0, pady=0, sticky="NSW")
        lb.config(yscrollcommand=widget.set)
        return lb
    
    def TextboxWithScrollbar(self, target, column, row, columnspan, rowspan, width, height, sticky):
        f = tk.Frame(target)
        f.grid(column=column, row=row, rowspan=rowspan, columnspan=columnspan, sticky=sticky)
        tb = tk.Text(f, borderwidth=1, height=height, width=width, wrap=tk.WORD)
        tb.grid()
        widget = tk.Scrollbar(f, command=tb.yview, width=15)
        widget.grid(column=1, row=0, pady=0, sticky="NS")
        tb.config(yscrollcommand=widget.set)
        return tb
        
    def Optionbutton(self, fr, col, row, cs, var, txt, hlp):
        tk.Label(fr, text=txt, justify="right").grid(column=col, row=row, rowspan=1, padx=0, pady=2, sticky="e")
        widget = tk.Checkbutton(fr, text="", variable=var, justify=tk.LEFT)
        widget.grid(column=col + 1, row=row, columnspan=cs, rowspan=1, padx=0, sticky="we")
        ToolTip(widget, hlp)
        
    def Radiobuttons(self, fr, col, row, cs, a, var, txt, opt, hlp):
        #fr=traget frame, col=column in target frame, row=row in target frame
        #cs=column span in target frame, a="v","v2", var=variable, txt=text, opt=list of options, hlp=list of helps
        wf = tk.Frame(fr)               # widget frame1 (left)
        wf2 = tk.Frame(fr)              # widget frame2 (right)
        if a == "v":
            rs = len(opt)
            if txt.count("\n") > rs:
                rs = txt.count("\n")
            if ("".join(opt)).count("\n") + len(opt) > rs:
                rs = ("".join(opt)).count("\n") + len(opt)
        else:
            rs = 1
        wf.grid(row=row, column=col, columnspan=1, rowspan=rs, sticky="e")
        wf2.grid(row=row, column=col + 1, columnspan=cs, rowspan=rs, sticky="w")
        iNL = 0  # add radiobuttons
        for i, o in enumerate(opt):
            iNL += opt[i].count("\n")
            widget = tk.Radiobutton(wf2, variable=var, text=opt[i], justify=tk.LEFT, value=i)
            if a == "v":  # vertical
                widget.grid(column=2, row=row, columnspan=1, padx=0, sticky="w")
                row += 1
            else:  # horizontal
                widget.grid(column=2 + i, row=row, columnspan=1, padx=0, sticky="w")
            ToolTip(widget, hlp[i])
        if a == "v":  # add bracket if vertical
            tk.Label(wf, text=txt, justify="right").grid(column=0, row=(row - i - 1), rowspan=i + 1, padx=0, sticky="e")
            txt = (unichr(0x250C)) + "\n"
            if rs > 2:
                txt += ((unichr(0x2502)) + "\n") * (rs - 1)
            else:
                txt += ((unichr(0x2502)) + "\n") * (rs - 2)
            txt += (unichr(0x2514))
            tk.Label(wf, text=txt).grid(column=1, row=(row - i - 1), rowspan=i + 1, padx=0, sticky="w")
        else:
            tk.Label(wf, text=txt, justify="right").grid(column=0, row=row, padx=0, sticky="e")


def TextboxWithScrollbar(frame, column=0, row=0, columnspan=1, rowspan=1, width=20, height=10, sticky="nsew"):
    """Add a text box widget with a scrollbar"""
    f = tk.Frame(frame)
    f.grid(column=column, row=row, rowspan=rowspan, columnspan=columnspan, sticky=sticky)
    tb = tk.Text(f, borderwidth=1, height=height, width=width, wrap=tk.WORD)
    tb.grid()
    widget = tk.Scrollbar(f, command=tb.yview, width=15)
    widget.grid(column=1, row=0, pady=0, sticky="NS")
    tb.config(yscrollcommand=widget.set)
    return tb


def ListboxWithScrollbar(frame, listvariable=None, help=False, column=0, row=0, width=20, height=10, selectmode=tk.SINGLE, sticky="NSEW", rowspan=1, columnspan=1):
    """Add a list box with a scrollbar"""
    f = tk.Frame(frame)
    f.grid(column=column, row=row, columnspan=columnspan, rowspan=rowspan, sticky=sticky)
    lb = tk.Listbox(f, listvariable=listvariable, selectmode=selectmode, width=width, height=height, exportselection=0)
    lb.grid(column=0, row=0, sticky="NS")
    if help: ToolTip(lb, help)
    widget = tk.Scrollbar(f, command=lb.yview, width=15)
    widget.grid(column=1, row=0, pady=0, sticky="NSW")
    lb.config(yscrollcommand=widget.set)
    return lb


def Optionbutton(frame, variable, text, help=False, column=0, row=0, columnspan=1, rowspan=1, sticky="e"):
    """Add an label-option button combo with a tooltip for the option"""
    
    #f = tk.Frame(frame)
    #f.grid(column=column, row=row, columnspan=columnspan, rowspan=rowspan, sticky=sticky)
    f = frame
    tk.Label(f, text=text, justify="right").grid(column=column, row=row, padx=0, pady=2, sticky="e")
    widget = tk.Checkbutton(f, text="", variable=variable, justify=tk.LEFT)
    widget.grid(column=column + 1, row=row, columnspan=columnspan, padx=0, sticky="w")
    if help: ToolTip(widget, help)
    return widget


def LabelEntry(frame, variable, text, help=False, width=10, column=0, row=0, columnspan=1, rowspan=1, sticky="e"):
    """Creates a label-entry combo with tooltip for the entry"""
    #f = tk.Frame(frame)
    #f.grid(column=column, row=row, columnspan=columnspan, rowspan=rowspan, sticky=sticky)
    f = frame
    if text.count("\n") > 0:  rowspan = text.count("\n") + 1
    else:                     rowspan = 1
    tk.Label(f, text=text, justify="right").grid(column=column, row=row, rowspan=rowspan, padx=0, pady=2, sticky="e")
    if (type(variable.get()) is int):
        widget = tk.Entry(f, textvariable=variable, width=width, justify=tk.CENTER, validate="key",
            validatecommand=vInteger)
    elif (type(variable.get()) is int):
        widget = tk.Entry(f, textvariable=variable, width=width, justify=tk.CENTER, validate="key",
            validatecommand=vDouble)
    elif (type(variable.get()) is float):
        widget = tk.Entry(f, textvariable=variable, width=width, justify=tk.CENTER, validate="key",
            validatecommand=vDouble)
    else:
        widget = tk.Entry(f, textvariable=variable, width=width, justify=tk.LEFT)
    widget.grid(column=column + 1, row=row, columnspan=columnspan, rowspan=rowspan, padx=0, sticky="we")
    if help: ToolTip(widget, help)
    return widget


def Radiobuttons(frame, variable, text, options, columns=0, column=0, row=0, columnspan=1):
    """Creates a label-radiobuttons combo with tooltip for every radiobutton
       options: [["Text1","Help1"],["Text2","Help2"],...]
    """
    frame_left = tk.Frame(frame)
    frame_right = tk.Frame(frame)
    frame_sep = tk.Frame(frame_right, bg="dark grey", width=2)
    frame_sep_t = tk.Frame(frame_right, bg="dark grey", height=2, width=5)
    frame_sep_b = tk.Frame(frame_right, bg="dark grey", height=2, width=5)
    c = r = 0
    for i, [t, h] in enumerate(options):
        widget = tk.Radiobutton(frame_right, variable=variable, text=t, justify=tk.LEFT, value=i)
        widget.grid(column=3+c, row=r, sticky="w", padx=0)
        ToolTip(widget, h)
        c += 1
        if not columns==0 and c>=columns:
            r += 1
            c = 0
    if text.count("\n") >= r:  r = text.count("\n") + 1
    tk.Label(frame_left, text=text, justify="right").grid(column=0, row=0, rowspan=r, padx=0, sticky="e")
    frame_left.grid(row=row, column=column, columnspan=1, rowspan=r, sticky="e")
    frame_right.grid(row=row, column=column + 1, columnspan=columnspan, rowspan=r, sticky="w")
    if r>0:
        frame_sep.grid(row=0, column=0, rowspan=r+1, sticky="ns")
        frame_sep_t.grid(row=0, column=1, sticky="new")
        frame_sep_b.grid(row=r, column=1, sticky="sew")
    frame_left.rowconfigure(0, weight=2)


class ListBoxWithLogic(object):  #============================================== DO NOT USE
    
    def __init__(self, f):
        self.lb = self.ListboxWithScrollbar(f)
        #self.lb.bind("<Double-1>", lambda x: self.ObjectEdit())
        
    def Update(self, content):
        self.lb.delete(0, tk.END)
        for n in content:
            self.lb.insert(tk.END, n)
            
    def SelectionMoveUp(self):
        indexes = self.lb.curselection()
        if indexes:
            indexes = self.sgg.ObjectsMoveUp(indexes)
            self.ObjectListbox_update()
            for i in indexes:
                self.lb_ncObjects.selection_set(i)
            self.lb_ncObjects.see(i)
        try:    self.gui.win.lift()
        except: pass
