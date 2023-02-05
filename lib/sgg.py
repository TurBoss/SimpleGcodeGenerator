#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Main logic of SimpleGcodeGenerator

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
170415    Erik Schuster   <def LoadProject>: Added "Project insert" feature.
                          <def SaveProject>: Added "Project save selection" feature.
170506    Erik Schuster   Added functions <def AxisLoad>, <def AxisRunning>
                          The output filename is now remebered during runtime.
                          Added <class ncObject> to track object changes and reduce unneccessary caclulations.
                          Removed <GetClassNames>.
170507    Erik Schuster   Bugfix <ObjectDublicate>: Deepcopy instead of copy.
170516    Erik Schuster   List modification functions moved to the module <utils>
                          Bugfix: <AxisRunning>, <__SendCommand>.
170708    Erik Schuster   Paths are now read from the <sgg.ini> file.
"""

import pickle
import datetime
import sys
import os
import copy
import subprocess
import re
import ConfigParser

import ncclasses                                                                # import g-code shapes (outlining, pocketing, ...)
import tooltable                                                                # reading the linux cnc tool table
import counterbore                                                              # provides drill paraemetrs for counter bores
import ngcsub                                                                   # support for ngc subroutines
import utils                                                                    # common utility functions
import feedsnspeeds
import font2vector

APP = "SimpleGcodeGenerator"                                                    # name of the application
VERSION = "170708"                                                              # version of this file (jjmmtt)

IN_AXIS = os.environ.has_key("AXIS_PROGRESS_BAR")                               # started within Axis?
LCNC_BIN_DIR = ""                                                               # path to LinuxCNC (only if <PATH> not set)

PREAMBLE_DEFAULT = "G17\t( set xy-plane )\nG21\t( units: millimeters )\nG94\t( feed rate mode: units per minute )\nG61\t( Exact path mode )\nG90\t( distance mode )\nF1000\t( feed rate )"
POSTAMBLE_DEFAULT = "M5\t( spindle control: stop the spindle )\nM9\t( coolant control: turn all coolant off )\nM2\t( end program )"
GCODEFILE_EXTENSION = "ngc"                                                     # default g-code output file extension
PROJECTFILE_EXTENSION = "sgg"                                                   # default project file extension
PROJECTFILE_DEFAULT = "default.sgg"                                             # default project file name

class ncobject(object):  # =====================================================
    """Wrapper class for ncclasses instances, to keep track of changes"""
   
    def __init__(self, obj):
        """Initialise the class"""
        self.obj = obj                                                          # ncclass instance
        self.gcode = obj.GetGcode(obj.Update())                                 # g-code result of the instance
        self.varcopy = self.CopyVars(obj)                                       # current values of the instance variables
        
    def GetGcode(self, recalculate=False):
        """Returns the g-code of the object and updates the g-code only when neccessary"""
        if recalculate:
            self.gcode = self.obj.GetGcode(self.obj.Update())
            self.varcopy = self.CopyVars(self.obj)
        else:
            if not self.varcopy==self.CopyVars(self.obj):                           # compare last to current parameters
                self.gcode = self.obj.GetGcode(self.obj.Update())
                self.varcopy = self.CopyVars(self.obj)
        return self.gcode
        
    def CopyVars(self, obj):
        """Copies the variable contents of the given object into a list"""
        p = []
        for name in vars(obj):
            p.append(obj.__dict__[name])
        return p


class sgg():  # ================================================================
    """Implements the basic logic of the SimpleGcodeGenerator"""

    def __init__(self):
        """Initialise the logic"""
        self.objlist = []               # list of generated objects/instances of ncobject(ncclasses)
        self.fn_project = "default.sgg"            # stores the name of the project-file
        self.fn_output = "default.ngc"             # stores the path to the g-code output file
        self.axis_remote_path = ""      # determined path to axis-remote
        self.preamble_found = False
        self.postamble_found = False
        self.__InitDefaults()
        self.AxisRemoteSetPath()
        
    def __InitDefaults(self):
        """Init the application with defaults for pre and postamble"""
        obj = self.ObjectCreate(0,0)                                            # create the default preamble
        obj.objectname = "Preamble"
        try:                                                                    # load an existing file or use the source code defaults
            file = open("preamble.ngc", 'r')
            preamble = file.read()
            file.close()
            self.preamble_found = True
        except:
            preamble = PREAMBLE_DEFAULT
            self.preamble_found = False
        obj.text = preamble
        
        obj = self.ObjectCreate(0,1)                                            # create the default postamble
        obj.objectname = "Postamble"
        try:                                                                    # load an existing file or use the source code defaults
            file = open("postamble.ngc", 'r')
            postamble = file.read()
            file.close()
            self.postamble_found = True
        except:
            postamble = POSTAMBLE_DEFAULT
            self.postamble_found = False
        obj.text = postamble

        tooltable.Init()                                                        # init the tooltable module
        ngcsub.Init()                                                           # init the subroutines module
        counterbore.Init()                                                      # init the counterbore module
        font2vector.Init()                                                      # init the font2vector module
        ncclasses.Init()                                                        # init the ncclasses module
        feedsnspeeds.Init()                                                     # init the feedsnspeeds module
        
        config = ConfigParser.ConfigParser()
        config.read('sgg.ini')
        global LCNC_BIN_DIR
        LCNC_BIN_DIR = config.get('LINUXCNC', 'LCNC_BIN_DIR', 0)
    
    def ObjectCreate(self, classindex, objectindex):
        """Creates a new instance and inserts the object into the objectlist after the given index. Returns the new object"""
        obj = ncobject(ncclasses.NCCLASSES[classindex]())
        self.objlist.insert(objectindex + 1, obj)
        return obj.obj

    def ObjectDublicate(self, index):
        """Dublicates the object at the given index and inserts it at index +1. Returns the index of the inserted object."""
        return utils.ListItemDublicate(self.objlist, index)

    def ObjectDelete(self, index):
        """Deletes the object at the given index"""
        self.objlist.pop(index)

    def ObjectsDelete(self, indexes):
        """Deletes the objects at the given indexes"""
        utils.ListItemsDelete(self.objlist, indexes)
        
    def ObjectsMoveUp(self, indexes):
        """Moves up the selected objects in the objectlist"""
        return utils.ListItemsMoveUp(self.objlist, indexes)
        
    def ObjectsMoveDown(self, indexes):
        """Moves down the selected objects in the objectlist"""
        return utils.ListItemsMoveDown(self.objlist, indexes)
        
    def GetObject(self, index):
        """Returns the nc-object with the given index from the objectlist"""
        return self.objlist[index].obj

    def SaveProject(self, filename, indexes=None):
        """Save the current project"""
        if indexes==None:
            ol = self.objlist
        else:
            ol = []
            for i in indexes:
                ol.append(self.objlist[i])
        with open(filename, 'wb') as handle:
            pickle.dump(ol, handle, pickle.HIGHEST_PROTOCOL)
        self.fn_project = filename
            
    def LoadProject(self, filename, index=None):
        """Load a project"""
        with open(filename, 'rb') as handle:
            if index==None:                             # overwrite
                self.objlist = pickle.load(handle)
            else:                                       # insert
                for o in pickle.load(handle):
                    self.objlist.insert(index, o)
                    index+=1
        self.fn_project = filename
        self.GetGcode(recalculate=True)
        
    def ResetProject(self):
        """Reset the current project (delete all objects)"""
        del(self.objlist)
        self.objlist = []
        self.__InitDefaults()
        
    def SaveGcode(self, filename, indexes=None):
        """Write g-code of the whole project or the selected objects to a file"""
        retval = True
        try:
            of = open(filename, 'w')
            of.write(self.GetGcode(indexes=indexes))
            of.close()
            self.fn_output = filename
        except:
            retval = False
        return retval

    def GetGcode(self, indexes=None, recalculate=False):
        """Return the complete g-code of all objects as a string"""
        gcode = "( Project: " + self.fn_project + " )\n"
        gcode += "( Date: " + str(datetime.date.today()) + " )\n"
        gcode += "( Generator: " + APP + " v" + VERSION + " )\n\n"
        if indexes==None:
            for o in self.objlist:
                gcode += o.GetGcode(recalculate)
        else:
            for i in indexes:
                gcode += self.objlist[i].GetGcode(recalculate)
        return gcode
        
    def AxisReload(self):
        """If LinuxCNC Axis is running, let it reload the current loaded file"""
        try:
            self.__SendCommand(self.axis_remote_path + "axis-remote -r")
            return 0
        except:
            return subprocess.STDOUT

    def AxisLoad(self, fn=None):
        """If LinuxCNC Axis is running, load the given or already saved file"""
        try:
            if fn==None: fn = self.fn_output                                    # did not work as default parameter. why?
            return self.__SendCommand(self.axis_remote_path + "axis-remote " + fn)
        except:
            return False

    def AxisRunning(self):
        """Check if LinuxCNC-AXIS is running"""
        v = self.__SendCommand(self.axis_remote_path + "axis-remote --ping")
        if v==0: return True
        else:    return False

    def WriteGcodeToStdout(self):
        """Write the gcode to stdout"""
        sys.stdout.write(self.GetGcode())
    
    def __SendCommand(self, cmd):
        """Send a command to STDOUT"""
        return subprocess.call(cmd, shell=True)  
        #return subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, bufsize=1024, cwd=DIR_LINUXCNC_BIN)

    def GetObjectNames(self):
        """Return the names of all created objects in the objectlist"""
        l = []
        for o in self.objlist:
            l.append(o.obj.objectname)
        return l

    def GetClassIndex(self, index_objlist):
        """Return the index of the class of the object with the given index"""
        index = -1
        name = self.objlist[index_objlist].obj.__class__
        for i, o in enumerate(ncclasses.NCCLASSES):
            if name == o:
                index = i
                break
        return index
        
    def AxisRemoteSetPath(self):
        """Determine the path to axis-remote"""
        paths = ["",LCNC_BIN_DIR]
        for p in paths:
            if os.path.isfile(p+"axis-remote"):
                self.axis_remote_path = p
                break
