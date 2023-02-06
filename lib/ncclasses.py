#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Provides classes to create g-code for milling pocktes, outlines, etc.

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
170416    Erik Schuster   Added classes <OutlineCircularArc>, <PocketCircularArc>.
170417    Erik Schuster   Added class <Text>,<Line>,<Character> for text engraving.
                          Classes based on source code from <engrave-11.py> from <Lawrence Glaister>.
170426    Erik Schuster   Rewrite of class <Text>. Added circular text and mirror.
                          Added exact path option to <OutlineCircularArc>,<OutlineRectangle>,<OutlineCircle>
170506    Erik Schuster   Class <Text> updated.
                          Some comments and minor changes.
170509    Erik Schuster   Added the standard parameters check to <PocketRectangle>, <PocketCircle>, <OutlinePolygon>
170521    Erik Schuster   Bufgix class <Text>: Rotation of single characters was not correct.
170529    Erik Schuster   Added ncclass <Subroutine>. Now ngc-subroutines can be included.
170625    Erik Schuster   Bufix class <Reflief>: Rotation is now possible
                          Class <Text>: Added option for text orientation within arc.
                          Bugfix DefaultPostamble: Frist go to sefatey height, before turning off coolant.
                          Added class <Counterbore>.
                          Class <PocketCircle>: Milling path optimised.
170708    Erik Schuster   Each new object is initialised with default values for the ini-file <defaults.ini>.
170712    Erik Schuster   Bugfix class <Text>. Entry move to origin 0,0 instead of given position.
                                               Now subpasses (z-increment) is possible.

ToDo:
- class Basemethods references variables of the deriving class. working but not good!!!
- Add bridges option to OutlineEllipse
- Add bridges option to OutlineCircularArc
- Improve <Text> class with: more aligning options
- Finalise <Relief> class.
"""

import tkinter as tk
import math
import string
import copy
import numpy
import re
import unicodedata
from PIL import Image
import configparser

from . import mathutils as mu                                                          # import math helper functions
from . import gcode as gc                                                              # import basic g-code classes
from . import font2vector as f2v                                                       # import module for class "Text"
from . import ngcsub
from . import utils                                                                    # common utility functions
from . import nclib as ncl                                                             # nc library functions

VERSION = "230206"                                                              # version of this file (jjmmtt)
DEFAULTS = {}                                                                   # default parameters


def Init():  # =================================================================
    """Initialises the module"""
    pl = ["tn","td","so","frtd","frso","frz","ss","zsh","zsh0","z0","z1","zi",\
          "posx","posy","posz","rx","ry","rz","deg","plane",\
          "preamble_gcode","preamble_tool","preamble_zsh","preamble_plane",\
          "preamble_spindle_cw","preamble_spindle_ccw","preamble_mist","preamble_flood",\
          "postamble_gcode","postamble_zsh","postamble_spindle_off","postamble_coolant_off"]
    config = configparser.ConfigParser()
    config.read('defaults.ini')
    global DEFAULTS
    for p in pl:
        DEFAULTS[p] = config.get('PARAMETERS', p)


class Basedata(object):  # =====================================================
    """Implements the basic class for most nc classes"""

    def __init__(self):
        """Initialise the basic variables"""
        self.objectname = self.name + "_" + str(self.i)
        self.tn = int(DEFAULTS["tn"])                # tool number
        self.td = float(DEFAULTS["td"])              # tool diameter
        self.so = float(DEFAULTS["so"])              # step over % of tool diameter
        self.frtd = float(DEFAULTS["frtd"])          # feedrate @ tool diameter
        self.frso = float(DEFAULTS["frso"])          # feedrate @ stepover
        self.frz = float(DEFAULTS["frz"])            # feedrate z
        self.ss = float(DEFAULTS["ss"])              # spindle speed (rpm)
        self.zsh = float(DEFAULTS["zsh"])            # safety height
        self.zsh0 = float(DEFAULTS["zsh0"])          # safety height for rapid move towards workpiece
        self.z0 = float(DEFAULTS["z0"])              # cut start height
        self.z1 = float(DEFAULTS["z1"])              # cut stop height
        self.zi = float(DEFAULTS["zi"])              # z increment
        self.posx = float(DEFAULTS["posx"])          # object position x
        self.posy = float(DEFAULTS["posy"])          # object position y
        self.posz = float(DEFAULTS["posz"])          # object position z      ***not used yet***
        self.rx = float(DEFAULTS["rx"])              # center of rotation (x)
        self.ry = float(DEFAULTS["ry"])              # center of rotation (y)
        self.rz = float(DEFAULTS["rz"])              # center of rotation (z)
        self.deg = float(DEFAULTS["deg"])            # rotation around center of rotation
        self.plane = int(DEFAULTS["plane"])          # plane selection 0=G17, 1=G18, 2=G19, 3=G17.1, 3=G18.1, 4=G19.1

        self.preamble_gcode = DEFAULTS["preamble_gcode"]             # user defined preamble g-code
        self.preamble_tool = DEFAULTS["preamble_tool"]               # select and change tool
        self.preamble_zsh  = DEFAULTS["preamble_zsh"]                # go to safety height
        self.preamble_plane = DEFAULTS["preamble_plane"]             # select the plane
        self.preamble_spindle_cw = DEFAULTS["preamble_spindle_cw"]   # turn on the spindle clockwise
        self.preamble_spindle_ccw = DEFAULTS["preamble_spindle_ccw"] # turn on the spindle counter clockwise
        self.preamble_mist = DEFAULTS["preamble_mist"]               # turn on mist collant
        self.preamble_flood = DEFAULTS["preamble_flood"]             # turn on flood coolant

        self.postamble_gcode = DEFAULTS["postamble_gcode"]               # user defined postamble g-code
        self.postamble_zsh = DEFAULTS["postamble_zsh"]                   # got to safety height
        self.postamble_spindle_off = DEFAULTS["postamble_spindle_off"]   # turn spindle off
        self.postamble_coolant_off = DEFAULTS["postamble_coolant_off"]   # turn coolant off

    def BaseparametersOK(self):
        """Check the basic variables for plausibility, e.g. avoid endless loops"""
        if self.z1 < self.z0 and \
           self.zi > 0 and \
           self.zsh > 0 and \
           self.tn > 0 and \
           self.td > 0 and \
           self.so > 0 and self.so <= 100 and \
           self.plane < 3:
           return True
        else:
            return False


class Basemethods(object): # ===================================================
    """Implements the basic methods for most nc-classes"""

    def GetGcode(self, objectlist):
        """Returns the g-code of all generated objects as a string, adds offset and rotates."""
        ol = copy.deepcopy(objectlist)                                          # copy the objects, we do not want to modify the original data
        for o in ol:
            try:    o.AddOffset([self.posx, self.posy, self.posz])              # try to add the offset to the gcode object
            except: pass                                                        # not all gcode objects support AddOffset ;-)
        for o in ol:
            try:    o.Rotate([self.rx, self.ry, 0], self.deg)                   # try to rotate the gcode object
            except: pass                                                        # not all gcode objects support Rotate ;-)
        gcode = "( " + self.objectname + " )\n"                                 # insert the object name a a comment
        for o in ol:                                                            # insert g-code of the object
            gcode += o.GetGcode() + "\n"
        gcode += "\n"                                                           # final line break
        return gcode

    def DefaultPreamble(self):
        """Creates a default preamble and returns an object list"""
        ol = []
        if self.preamble_tool: ol.append(gc.T(self.tn, c="Select tool"))
        if self.preamble_tool: ol.append(gc.M(6, c="Tool change"))
        if self.preamble_zsh: ol.append(gc.G00(z=self.zsh, c="To safety height"))
        p = [17,18,19,17.1,18.1,19.1]
        if self.preamble_plane: ol.append(gc.G(p[self.plane], c="Select plane"))
        if self.preamble_spindle_cw: ol.append(gc.M(3, s=self.ss, c="Start spindle clockwise"))
        if self.preamble_spindle_ccw: ol.append(gc.M(4, s=self.ss, c="Start spindle counter clockwise"))
        if self.preamble_mist: ol.append(gc.M(7, c="Turn mist coolant on"))
        if self.preamble_flood: ol.append(gc.M(8, c="Turn flood coolant on"))
        if not self.preamble_gcode=="": ol.append(gc.TEXT(self.preamble_gcode, c="User specific preamble"))
        return ol

    def DefaultPostamble(self):
        """Creates a default postamble and returns an object list"""
        ol = []
        if self.postamble_zsh: ol.append(gc.G00(z=self.zsh, c="To safety height"))
        if self.postamble_coolant_off: ol.append(gc.M(9, c="All coolant off"))
        if self.postamble_spindle_off: ol.append(gc.M(5, c="spindle control: stop the spindle"))
        if not self.postamble_gcode=="": ol.append(gc.TEXT(self.postamble_gcode, c="User specific postamble"))
        return ol


class CustomCode(Basemethods):  # ==============================================
    """Generate g-code for Free text/g-code"""

    name="CustomCode"
    description="Individual g-code or text"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        self.objectname = self.name + "_" + str(self.i)
        super(CustomCode, self).__init__()
        self.text = "( Add your g-code... )"

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        ol = []
        ol.append(gc.TEXT(self.text))
        return ol


class OutlineRectangle(Basedata, Basemethods):  # ==============================
    """Generate g-code for OutlineRectangle"""

    name="OutlineRectangle"
    description="Outline a rectangle"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(OutlineRectangle, self).__init__()

        self.w = 40                 # width (x)
        self.h = 20                 # height (y)
        self.climb = True           # machining direction,  0=conventional, 1=climb cutting
        self.contour = 1            # contour: 0=inside, 1=exact, 2=outside
        self.br = True              # bridges 0=none, 1=x4
        self.brh = 1.0              # height of bridges
        self.brw = 1.0              # width of bridges
        self.rsx = 0                # rotation center x of shape
        self.rsy = 0                # rotation center y of shape
        self.rsdeg = 0              # degrees of shape rotation

        self.rur = 5
        self.rul = 5
        self.rlr = 5
        self.rll = 5

    def ParametersOk(self):
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() and\
           self.w > 0 and\
           self.h > 0 and\
           self.brh > 0 and\
           self.brw > 0 :
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]

        if self.br: ze = self.z1 + self.brh                                     # determine end depth before bridges
        else:       ze = self.z1

        if self.contour==0:     x,y = (self.w-self.td)/2, (self.h-self.td)/2    # inside
        elif self.contour==2:   x,y = (self.w+self.td)/2, (self.h+self.td)/2    # outside
        else:                   x,y = self.w/2, self.h/2                        # no tool compensation

        p = [[x,y],[x,-y],[-x,-y],[-x,y],[x,y]]                                 # define the waypoints for the rectangle

        br = (self.brw + self.td)/ 2                                            # define the waypoints for bridges
        br = ["-",[x,y],"-",[x,br],"+",[x,-br],"-",[x,-y],"-",[br,-y],"+",
             [-br,-y],"-",[-x,-y],"-",[-x,-br],"+",[-x,br],"-",[-x,y],"-",
             [-br,y],"+",[br,y],"-",[x,y],"-"]

        if not self.climb:      p, br = p[::-1], br[::-1]                       # reverse the waypoints for climb cutting
        if self.contour==1:     p, br = p[::-1], br[::-1]                       # reverse the waypoints for inside cutting

        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=p[0][0], y=p[0][1], c="Rapid move to start point"))
        ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))

        z = self.z0                                                             # mill the shape
        while z > ze:
            z -= self.zi
            if z < ze:
                z = ze
            ol.append(gc.G01(z=z, f=self.frz))
            for xy in p:
                ol.append(gc.G01(x=xy[0],y=xy[1], f=self.frtd))

        if self.br and not self.brh==0 and not self.brw==0:                     # mill the bridges
            while z > self.z1:
                z -= self.zi
                if z < self.z1:
                    z = self.z1
                for xy in br:
                    if len(xy)==2:
                        ol.append(gc.G01(x=xy[0],y=xy[1], f=self.frtd))
                    if len(xy)==1 and xy=="+":
                        ol.append(gc.G01(z=ze, f=self.frz))
                    if len(xy)==1 and xy=="-":
                        ol.append(gc.G01(z=z, f=self.frz))

        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()

        for o in ol:
            try:    o.Rotate([self.rsx, self.rsy, 0], self.rsdeg)               # rotate the gcode object
            except: pass                                                        # not all gcode objects support Rotate ;-)
        return ol


class OutlineCircle(Basedata, Basemethods):  # =================================
    """Generate g-code for OutlineCircle"""

    name="OutlineCircle"
    description="Outline a circle"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(OutlineCircle, self).__init__()

        self.r = 10                 # radius
        self.climb = True           # machining direction,  0=conventional, 1=climb cutting
        self.contour = 1            # contour: 0=inside, 1=exact, 2=outside
        self.br = True              # bridges 0=none, 1=x4
        self.brh = 1.0              # height of bridges
        self.brw = 1.0              # width of bridges

    def ParametersOk(self):
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() and\
           self.r > 0 and\
           self.brh > 0 and\
           self.brw > 0 :
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]
        if self.contour==0: r = self.r - self.td / 2.0                          # determine cutting radius
        elif self.contour==1: r = self.r
        elif self.contour==2: r = self.r + self.td / 2.0
        phi = ((self.td + self.brw) * 360.0) / (2.0 * math.pi * r) / 2.0        # half-angle for the bridges
        if self.br: ze = self.z1 + self.brh                                     # determine end depth before bridges
        else:       ze = self.z1

        if (self.contour==0 and self.climb) or \
           (not self.contour==0 and not self.climb):                                # define g02 or g03 and define arc angles for bridges
            fn = gc.G03
            deg = [0,0+phi,90-phi,90+phi,180-phi,180+phi,270-phi,270+phi,360-phi]
        else:
            fn = gc.G02
            deg = [0,360-phi,270+phi,270-phi,180+phi,180-phi,90+phi,90-phi,0+phi]

        bl = []                                                                 # calculate points for bridges
        for d in deg:
            bl.append(mu.PointRotate([r,0],[0,0],d))

        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=r, y=0, c="Rapid move to start point"))
        if self.br and self.brh > abs(self.z1):
            ol.append(gc.G00(z=self.z1 + self.brh, c="Rapid down to workpiece"))
        else:
            ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))

        z = self.z0                                                             # cut arc
        while z > ze:
            z -= self.zi
            if z < ze:
                z = ze
            ol.append(fn(z=z, i=-r, j=0, f=self.frtd))

        if self.br and not self.brh==0 and not self.brw==0:                     # cut bridges
            while z > self.z1:
                z -= self.zi
                if z < self.z1:
                    z = self.z1
                for i in [0, 2, 4, 6]:
                    ol.append(fn(x=bl[i+1][0], y=bl[i+1][1], i=-bl[i][0], j=-bl[i][1], f=self.frtd))
                    ol.append(gc.G01(z=z))
                    ol.append(fn(x=bl[i+2][0], y=bl[i+2][1], i=-bl[i+1][0], j=-bl[i+1][1], f=self.frtd))
                    ol.append(gc.G01(z=ze))
                ol.append(fn(x=bl[0][0], y=bl[0][1], i=-bl[8][0], j=-bl[8][1], f=self.frtd))

        if not self.br or self.brh==0 or self.brw==0:
            ol.append(fn(z=z, i=-r, j=0, f=self.frtd))  # final pass
        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()
        return ol


class OutlineEllipse(Basedata, Basemethods):  # ================================
    """Generate g-code for OutlineEllipse"""

    name="OutlineEllipse"
    description="Outline an ellipse"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(OutlineEllipse, self).__init__()

        self.a = 20                 # radius x
        self.b = 10                 # radius b
        self.ai = 5                 # angle increment (resolution)
        self.climb = True           # machining direction,  0=conventional, 1=climb cutting
        self.contour = 1            # contour: 0=inside, 1=exact, 2=outside
        self.br = False             # bridges 0=none, 1=x4
        self.brh = 1.0              # height of bridges
        self.brw = 1.0              # width of bridges

    def ParametersOk(self):
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() and\
           self.a>0 and self.b>0 and \
           self.a>self.td/2 and self.b>self.td/2 and \
           self.ai>0 and \
           self.brh > 0 and\
           self.brw > 0 :
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]

        # determine end depth before bridges
        if self.br: ze = self.z1 + self.brh
        else:       ze = self.z1
        if self.contour==0:
            a = self.a - self.td / 2.0
            b = self.b - self.td / 2.0
            ai = self.ai
            if not self.climb:
                rng = list(range(360,0,-ai))
                x, y = mu.PointEllipse(a, b, ai) #define start point
            else:
                rng = list(range(0,360,ai))
                x, y = mu.PointEllipse(a, b, -ai) #define start point
        elif self.contour==2:
            a = self.a + self.td / 2.0
            b = self.b + self.td / 2.0
            ai = self.ai
            if not self.climb:    #conventional
                rng = list(range(0,360,ai))
                x, y = mu.PointEllipse(a, b, -ai) #define start point
            else:                   # climb
                rng = list(range(360,0,-ai))
                x, y = mu.PointEllipse(a, b, ai) #define start point
        else:
            a = self.a
            b = self.b
            ai = self.ai
            if not self.climb:    #conventional
                rng = list(range(0,360,ai))
                x, y = mu.PointEllipse(a, b, -ai) #define start point
            else:                   # climb
                rng = list(range(360,0,-ai))
                x, y = mu.PointEllipse(a, b, ai) #define start point

        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=x, y=y, c="Rapid move to start point"))
        ol.append(gc.G(64,p=0.05))
        z = self.z0
        while z > ze:
           # z -= self.zi
            if z < ze:
                z = ze
            for r in rng:
                z -= self.zi / (360 / ai)
                x, y = mu.PointEllipse(a, b, r)
                ol.append(gc.G01(x=x, y=y, z=z, c=str(r)))
        for r in rng:  # final pass
            x, y = mu.PointEllipse(a, b, r)
            ol.append(gc.G01(x=x, y=y, c=str(r)))
        i = 0
        for r in rng:  # lead out
            x, y = mu.PointEllipse(a, b, r)
            ol.append(gc.G01(x=x, y=y, z=z, c=str(r)))
            if z > self.z0:
                break
            if i > 0:
                z += self.zi / (360.0 * 0.0625 / abs(ai))
            i = 1
        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()
        ol.append(gc.G(61))
        return ol


class OutlinePolygon(Basedata, Basemethods):  # ================================
    """Generate g-code for OutlinePolygon"""

    name="OutlinePolygon"
    description="Cut along a polygon path"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(OutlinePolygon, self).__init__()

        self.scalex = 1
        self.scaley = 1
        self.x = 0
        self.y = 0
        self.cc = 0                 # cutter compensation: 0=none, 1=left of path, 2=right of path
        self.close = True           # automatically close the polygon
        self.poly = []              # list of g-code objects
        self.rsx = 0                # rotation center of shape x
        self.rsy = 0                # rotation center of shape y
        self.rsdeg = 0              # degrees of shape rotation
        self.g64 = 0.01             # path blending 0=G61

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() :
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====
        poly2 = copy.deepcopy(self.poly)

        if len(poly2) > 2:
            for o in poly2:
                o.x *= self.scalex
                o.y *= self.scaley
            x = poly2[0].x
            y = poly2[0].y
            p0 = [poly2[0].x, poly2[0].y]
            p1 = [poly2[-1].x, poly2[-1].y]
            if p0==p1:
                p1 = [poly2[-2].x, poly2[-2].y]
            x2, y2 = mu.GetPointOnLine(p0,p1,self.td)
        else:
            x = y = x2 = y2 = 0
        ol = self.DefaultPreamble()
        ol.append(gc.G(64, p=self.g64, c="Blend path mode"))
        if self.cc==1:
            ol.append(gc.G00(x=x2,y=y2,c="Rapid move to lead in point"))
            ol.append(gc.G00(z=self.z0 + self.zsh0, f=self.frz))
            ol.append(gc.G(41, c="cutter compensation left of programmed path"))
        elif self.cc==2:
            ol.append(gc.G00(x=x2,y=y2,c="Rapid move to lead in point"))
            ol.append(gc.G00(z=self.z0 + self.zsh0, f=self.frz))
            ol.append(gc.G(42, c="cutter compensation right of programmed path"))

        ol.append(gc.G00(x=x, y=y, c="Rapid move to start point"))
        z = self.z0
        while z > self.z1:
            z -= self.zi
            if z < self.z1:
                z = self.z1
            ol.append(gc.G01(z=z, f=self.frz))
            ol.append(gc.F(self.frtd))
            for o in poly2:
                ol.append(copy.copy(o))
            if self.close and len(poly2)>0:
                ol.append(copy.copy(poly2[0]))
        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()
        if not self.cc==0:
            ol.append(gc.G(40, c="cutter compensation off"))
        ol.append(gc.G(61, c="Exact path mode"))
        for o in ol:
            try:
                # try to rotate the gcode object
                o.Rotate([self.rsx, self.rsy, 0], self.rsdeg)
            except:
                pass
        return ol

    def Import(self, filename):
        handle = open(filename, 'rb')
        self.poly = []
        for line in handle:
            parts = line.split()
            if len(parts)==2:
                try:
                    parts = [float(component) for component in parts]
                    self.poly.append(gc.G01(x=parts[0], y=parts[1]))
                except ValueError:
                    pass
        handle.close()

    def GetPoly(self, index):
        if len(self.poly)>=index:
            return self.poly[index].x, self.poly[index].y

    def ObjectUpdate(self, index, x, y):
        if len(self.poly)>=index:
            self.poly[index].x = x
            self.poly[index].y = y

    def ObjectInsert(self, index, x, y):
        self.poly.insert(index, gc.G01(x=x, y=y))

    def ObjectDelete(self, index):
        utils.ListItemsDelete(self.poly, index)

    def ObjectsMoveUp(self, indexes):
        """Moves up the selected objects in the objectlist"""
        return utils.ListItemsMoveUp(self.poly, indexes)

    def ObjectsMoveDown(self, indexes):
        """Moves down the selected objects in the objectlist"""
        return utils.ListItemsMoveDown(self.poly, indexes)

    def GetObjectNames(self):  # ok
        l = []
        for o in self.poly:
            l.append(o.name + "  x:%04.4f" % o.x + "   y:%04.4f"% o.y)
        return l

    def AddG01(self):
        self.poly.append(gc.G01(x=self.x, y=self.y))


class PocketRectangle(Basedata, Basemethods):  # ===============================
    """Generate g-code for PocketRectangle"""

    name="PocketRectangle"
    description="Pocketing a rectangle"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(PocketRectangle, self).__init__()

        self.w = 50                # width
        self.h = 40                # height
        self.climb = True          # machining direction,  0=conventional, 1=climb cutting
        self.corners = False       # mill out the corners to fit an rectangle
        self.rur = 0               # corner radius upper right
        self.rul = 0               # corner radius upper left
        self.rll = 0               # corner radius lower left
        self.rlr = 0               # corner radius lower right

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() :
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====
        d = self.td * (self.so / 100.0)
        r = self.td / 2
        if self.w > self.td and self.h > self.td:
            xm = (self.w - self.td) / 2.0                       # maximum x-position
            ym = (self.h - self.td) / 2.0                       # maximum y-position
        else:
            return []
        dx = d
        dy = (ym / xm) * d
        c = math.sqrt(2*self.td/2*self.td/2) - self.td/2
        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=0, y=0, c="Rapid move to start point"))
        ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))
        z = self.z0
        while z > self.z1:
            z -= self.zi
            if z < self.z1:
                z = self.z1
            ol.append(gc.G01(x=0, y=0))
            ol.append(gc.G01(z=z, f=self.frtd))
            ol.append(gc.G(64))
            x = y = 0
            while True :
                x += dx
                if x > xm:
                    x = xm
                ol.append(gc.G01(x=x, y=y))
                y += dy
                if y > ym:
                    y = ym
                ol.append(gc.G01(x=x, y=-y))
                ol.append(gc.G01(x=-x, y=-y))
                ol.append(gc.G01(x=-x, y=y))
                if x>=xm and y>=ym :
                    break
            ol.append(gc.G(61))
            if self.corners:
                ol.append(gc.G01(x=x, y=y))
                ol.append(gc.G01(x=x+c, y=y+c))
                ol.append(gc.G01(x=x, y=y))
                ol.append(gc.G01(x=x, y=-y))
                ol.append(gc.G01(x=x+c, y=-y-c))
                ol.append(gc.G01(x=x, y=-y))
                ol.append(gc.G01(x=-x, y=-y))
                ol.append(gc.G01(x=-x-c, y=-y-c))
                ol.append(gc.G01(x=-x, y=-y))
                ol.append(gc.G01(x=-x, y=y))
                ol.append(gc.G01(x=-x-c, y=y+c))
                ol.append(gc.G01(x=-x, y=y))
            else:
                ol.append(gc.G01(x=x, y=y))
                ol.append(gc.G01(x=x, y=-y))
                ol.append(gc.G01(x=-x, y=-y))
                ol.append(gc.G01(x=-x, y=y))
            ol.append(gc.G(64))
            ol.append(gc.G01(x=0, y=y))
            ol.append(gc.G(61))
        if self.climb:
            for o in ol:
                try:
                    o.x *= -1
                    o.y *= -1
                except:
                    pass
        ol.append(gc.G00(x=0, y=0, z=0))
        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()
        return ol


class PocketCircle(Basedata, Basemethods):  # ==================================
    """Generate g-code for PocketCircle"""

    name="PocketCircle"
    description="Pocketing a circle"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(PocketCircle, self).__init__()

        self.ri = 5                 # inner radius
        self.ra = 20                # outer radius
        self.climb = True           # machining direction,  0=conventional, 1=climb cutting

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() :
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====
        dr = self.td * (self.so / 100.0)
        if self.ri==0:
            ri = self.td / 3
        else:
            ri = self.ri + self.td / 2
        ra = self.ra - self.td / 2
        if self.climb:
            fn = gc.G02
        else:
            fn = gc.G03
        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=ri, y=0, c="Rapid move to start point"))
        ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))
        ol += ncl.PocketCircle(fn,self.z0,self.z1,self.zi,ri,ra,dr,self.frtd,self.frso)
        ol.append(gc.G01(x=(ri+(ra-ri)/2), y=0))
        ol += self.DefaultPostamble()
        return ol


class Grill(Basedata, Basemethods):  # =========================================
    """Generate g-code for Grill"""

    name="Grill"
    description="Drilling a grill"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(Grill, self).__init__()
        self.w = 80         # width, radius or a
        self.h = 40         # height or b
        self.shape = 0      # shape of the grill: 0=rectangle, 1=circle, 2=ellipse
        self.dist = 2.0     # distance between holes
        self.peck = False   # plunge strategy (linear or peck)

    def ParametersOk(self):
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() :
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]
        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=0, y=0, c="Rapid move to start point"))
        for xy in self.GetPlist():
            ol.append(gc.G00(z=self.zsh))
            ol.append(gc.G00(x=xy[0], y=xy[1]))
            ol.append(gc.G00(z=self.z0 + self.zsh0))
            if self.peck == 0:
                ol.append(gc.G01(z=self.z1, f=self.frz))
            else:
                ol.append(gc.G83(x=xy[0], y=xy[1], z=self.z1, r=0, q=self.zi, f=self.frz))
        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()
        return ol

    def GetPlist(self):
        dxy = self.td + self.dist
        nx = self.w / 2 / dxy
        ny = self.h / 2 / dxy
        if self.shape == 1:  # circle
            ny = nx
        plist = []
        for x in range(int(-nx), int(nx + 1)):
            for y in range(int(-ny), int(ny + 1)):
                plist.append([x * dxy, y * dxy])    # list of drill points within the boundary box
        plist2 = []
        if self.shape == 0:      # rectangle, keep all points
            plist2 = plist
        elif self.shape == 1:    # circle, remove points which are not within the shape
            A = (self.w / 2.0) * (self.w / 2.0)
            for xy in plist:
                if ((xy[0] * xy[0] + xy[1] * xy[1]) < A):
                    plist2.append(xy)
        elif self.shape == 2:    # ellipse, remove points which are not within the shape
            Ax = (self.w / 2.0) * (self.w / 2.0)
            Ay = (self.h / 2.0) * (self.h / 2.0)
            for xy in plist:
                if (((xy[0] * xy[0] / Ax) + (xy[1] * xy[1] / Ay)) < 1.0):
                    plist2.append(xy)
        return plist2


class Bezel(Basedata, Basemethods):  # =========================================
    """Generate g-code for Bezel"""

    name="Bezel"
    description="Engraving a bezel"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(Bezel, self).__init__()
        self.ri    = 15     # inner radius
        self.romaj = 22.5   # outer radius major tick
        self.romin = 20     # outer rdius minor tick
        self.a0    = 240    # start angle
        self.a1    = -60    # end angle
        self.div   = 25     # divisions
        self.divmaj = 4     # major ticks every n divisions

    def ParametersOk(self):
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() and\
        self.ri>0 and\
        self.romin>0 and\
        self.romaj>0 and\
        self.div>1 and\
        self.divmaj>=0:
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]
        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=0, y=0, c="Rapid move to start point"))
        for xy in self.GetPlist():
            ol.append(gc.G00(z=self.zsh))
            ol.append(gc.G00(x=xy[0], y=xy[1]))
            ol.append(gc.G00(z=self.z0 + self.zsh0))
            ol.append(gc.G01(z=self.z1, f=self.frz))
            ol.append(gc.G01(x=xy[2], y=xy[3]))
        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()
        return ol

    def GetPlist(self):
        a = (self.a1 - self.a0) / (self.div - 1)  # delta angle
        plist = []
        j = 0
        for i in range(self.div):
            start = mu.PointRotate([self.ri, 0], [0, 0], i * a + self.a0)
            if j == 0:
                end = mu.PointRotate([self.romaj, 0], [0, 0], i * a + self.a0)
            else:
                end = mu.PointRotate([self.romin, 0], [0, 0], i * a + self.a0)
            j += 1
            if j == self.divmaj:
                j = 0
            plist.append([start[0], start[1], end[0], end[1]])
        return plist


class DrillMatrix(Basedata, Basemethods):  # ===================================
    """Generate g-code for DrillMatrix"""

    name="DrillMatrix"
    description="Drilling a matrix"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(DrillMatrix, self).__init__()
        self.dx = 2.54*4
        self.dy = 2.54*4
        self.nx = 5
        self.ny = 2
        self.peck = False   # plunge strategy (linear or peck)
        self.center = True

    def ParametersOk(self):
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() and\
            self.nx>0 and\
            self.ny>0:
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]
        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=0, y=0, c="Rapid move to start point"))
        for xy in self.GetPlist():
            ol.append(gc.G00(z=self.zsh))
            ol.append(gc.G00(x=xy[0], y=xy[1]))
            ol.append(gc.G00(z=self.z0 + self.zsh0))
            if self.peck == 0:
                ol.append(gc.G01(z=self.z1, f=self.frz))
            else:
                ol.append(gc.G83(x=xy[0], y=xy[1], z=self.z1, r=0, q=self.zi, f=self.frz))
        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()
        return ol

    def GetPlist(self):
        plist = []
        if self.center:
            ox = ((self.nx-1) * self.dx) / 2
            oy = ((self.ny-1) * self.dy) / 2
        else:
            ox = oy = 0
        for y in range(self.ny):
            for x in range(self.nx):
                plist.append([x*self.dx-ox, y*self.dy-oy])
        return plist


class Slot(Basedata, Basemethods):  # ==========================================
    """Generate g-code for Slot"""

    name="Slot"
    description="Pocketing a slot"
    i = 0

    def __init__(self):
        self.__class__.i += 1
        super(Slot, self).__init__()
        self.dx = 50
        self.dy = 0
        self.peck = False   # plunge strategy (linear or peck)

    def ParametersOk(self):
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() :
            return True
        else:
            return False

    def Update(self):
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]
        ol = self.DefaultPreamble()
        ol.append(gc.G(61))
        ol.append(gc.G00(x=0, y=0, c="Rapid move to start point"))
        ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))
        z = self.z0
        while z > self.z1:
            z -= self.zi
            if z < self.z1:
                z = self.z1
            if self.peck == 1: ol.append(gc.G83(z=z, r=z+self.zi, q=self.zi/2, f=self.frz))
            ol.append(gc.G01(z=z, f=self.frz))
            ol.append(gc.G01(x=self.dx, y=self.dy, f=self.frtd))
            if z == self.z1:
                break
            z -= self.zi
            if z < self.z1:
                z = self.z1
            if self.peck == 1: ol.append(gc.G83(z=z, r=z+self.zi, q=self.zi/2, f=self.frz))
            ol.append(gc.G01(z=z, f=self.frz))
            ol.append(gc.G01(x=0, y=0, f=self.frtd))

        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()
        return ol


class PocketCircularArc(Basedata, Basemethods):  # =============================
    """Generate g-code for PocketCircularArc"""

    name="PocketCircularArc"
    description="Pocketing a circular arc"
    i = 0

    def __init__(self):         # ==== MANDATORY METHOD ====
        self.__class__.i += 1
        super(PocketCircularArc, self).__init__()
        self.ri = 25        # inner radius
        self.ro = 50        # outer radius
        self.a0 = 0         # start angle
        self.a1 = 90        # end angle
        self.climb = True   # machining direction,  0=conventional, 1=climb cutting

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() :
            return True
        else:
            return False

    def Update(self):           # ==== MANDATORY METHOD ====
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====

        so = self.td / 100 * self.so
        r0 = self.ri + (self.ro - self.ri) / 2.0
        drmax = (self.ro - self.ri) / 2.0 - so
        drmax2 = drmax - so
        a = mu.ArcAngle(so, r0)
        x0, y0 = mu.PointRotate([r0,0],[0,0],self.a0+a)

        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=x0, y=y0, c="Rapid move to start point"))
        ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))

        z = self.z0
        while z > self.z1:
            z -= self.zi
            if z < self.z1:
                z = self.z1
            ol.append(gc.G01(z=z, f=self.frtd))
            ol.append(gc.G(64, c="Blend path mode"))
            dr = -so/2
            while dr <= drmax:
                dr += so
                if dr>drmax:
                    dr = drmax
                    ol.append(gc.G(61, c="Exact path mode"))
                ol += self.GetArc(self.a0, self.a1, r0-dr, r0+dr)
                if dr>=drmax:
                    break
            ol.append(gc.G01(x=x0, y=y0))

        x0, y0 = mu.PointRotate([r0,0],[0,0],self.a0+a*1.5)
        ol.append(gc.G01(x=x0, y=y0, z= z + self.zi))
        #ol.append(gc.G00(z=self.zsh, c="To afety height"))
        ol += self.DefaultPostamble()
        return ol

    def GetArc(self, a0, a1, ri, ro):
        ol = []
        a = mu.ArcAngle(self.td/2.0, ro)
        x0, y0 = mu.PointRotate([ro,0],[0,0],a0+a)
        x1, y1 = mu.PointRotate([ro,0],[0,0],a1-a)
        ol.append(gc.G01(x=x0, y=y0, f=self.frtd))
        ol.append(gc.G03(x=x1, y=y1, i=-x0, j=-y0))

        a = mu.ArcAngle(self.td/2.0, ri)
        x0, y0 = mu.PointRotate([ri,0],[0,0],self.a1-a)
        x1, y1 = mu.PointRotate([ri,0],[0,0],self.a0+a)
        ol.append(gc.G01(x=x0, y=y0, f=self.frtd))
        ol.append(gc.G02(x=x1, y=y1, i=-x0, j=-y0))
        return ol


class OutlineCircularArc(Basedata, Basemethods):  # ============================
    """Generate g-code for OutlineCircularArc"""

    name="OutlineCircularArc"
    description="Outlining a circular arc"
    i = 0

    def __init__(self):         # ==== MANDATORY METHOD ====
        self.__class__.i += 1
        super(OutlineCircularArc, self).__init__()
        self.ri = 25        # inner radius
        self.ro = 50        # outer radius
        self.a0 = 0         # start angle
        self.a1 = 90        # end angle
        #self.climb = True   # machining direction,  0=conventional, 1=climb cutting
        self.contour = 1            # contour: 0=inside, 1=exact, 2=outside
        self.br = False             # bridges 0=none, 1=x4
        self.brh = 1.0              # height of bridges
        self.brw = 1.0              # width of bridges

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() :
            return True
        else:
            return False

    def Update(self):           # ==== MANDATORY METHOD ====
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====
        if self.contour==0:
            ri = self.ri + self.td / 2.0
            ro = self.ro - self.td / 2.0
        elif self.contour==1:
            ri = self.ri
            ro = self.ro
        else:
            ri = self.ri - self.td / 2.0
            ro = self.ro + self.td / 2.0
        if self.ri==0: ri = 0
        a = mu.ArcAngle(self.td/2.0, ro)
        if self.contour==0:
            x0, y0 = mu.PointRotate([ro,0],[0,0],self.a0+a)
        elif self.contour==1:
            x0, y0 = mu.PointRotate([ro,0],[0,0],self.a0)
        else:
            x0, y0 = mu.PointRotate([ro,0],[0,0],self.a0-a)
        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=x0, y=y0, c="Rapid move to start point"))
        ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))
        z = self.z0
        while z > self.z1:
            z -= self.zi
            if z < self.z1:
                z = self.z1
            ol.append(gc.G01(z=z, f=self.frtd))
            ol += self.GetArc(self.a0, self.a1, ri, ro)
            ol.append(gc.G01(x=x0, y=y0))

        ol.append(gc.G01(x=x0, y=y0, z= z + self.zi))
        #ol.append(gc.G00(z=self.zsh, c="To afety height"))
        ol += self.DefaultPostamble()
        return ol

    def GetArc(self, a0, a1, ri, ro, br=True):
        ol = []
        a = mu.ArcAngle(self.td/2.0, ro)
        if self.contour==0:
            x0, y0 = mu.PointRotate([ro,0],[0,0],a0+a)
            x1, y1 = mu.PointRotate([ro,0],[0,0],a1-a)
        elif self.contour==1:
            x0, y0 = mu.PointRotate([ro,0],[0,0],a0)
            x1, y1 = mu.PointRotate([ro,0],[0,0],a1)
        else:
            x0, y0 = mu.PointRotate([ro,0],[0,0],a0-a)
            x1, y1 = mu.PointRotate([ro,0],[0,0],a1+a)
        ol.append(gc.G01(x=x0, y=y0, f=self.frtd))
        ol.append(gc.G03(x=x1, y=y1, i=-x0, j=-y0))
        if not ri==0:
            a = mu.ArcAngle(self.td/2.0, ri)
            if self.contour==0:
                x0, y0 = mu.PointRotate([ri,0],[0,0],a1-a)
                x1, y1 = mu.PointRotate([ri,0],[0,0],a0+a)
            elif self.contour==1:
                x0, y0 = mu.PointRotate([ri,0],[0,0],a1)
                x1, y1 = mu.PointRotate([ri,0],[0,0],a0)
            else:
                x0, y0 = mu.PointRotate([ri,0],[0,0],a1+a)
                x1, y1 = mu.PointRotate([ri,0],[0,0],a0-a)
            ol.append(gc.G01(x=x0, y=y0, f=self.frtd))
            ol.append(gc.G02(x=x1, y=y1, i=-x0, j=-y0))
        return ol


class Text(Basedata, Basemethods):  # ==========================================
    """Generate g-code for Text"""

    name="Text"
    description="Engrave text"
    i = 0

    def __init__(self):         # ==== MANDATORY METHOD ====
        self.__class__.i += 1
        super(Text, self).__init__()

        self.text = "Simple G-Code\nGenerator!!!"                               # text to engrave
        self.fontfile = "courier.cxf"                                           # font file to use (cxf v1 only)
        self.char_height = 10                                                   # character height
        self.char_width = 10                                                    # character width
        self.char_space = 1                                                     # space between chars [mm/in]
        self.line_space = 10                                                    # space between lines [mm/in]
        self.g64 = 0.01                                                         # path blending 0=G61
        self.arcres = 10                                                        # arc resoultion in degrees
        self.radius = 0                                                         # radius of circular text
        self.arcjust = 0                                                        # justification of text within arc (0=center is bottom, 1=center is top)
        self.align = 1                                                          # 0=upper left, 1=upper center, 2=upper right
        self.mirrorh = False                                                    # mirrors the characters (horizontally)
        self.mirrorv = False                                                    # mirrors the characters (vertically)

        self.font = None                                                        # instance of class <Font> from <textengrave.py>
        self.parsed = False                                                     # if true, fontfile is successfully parsed

        self.LoadFont(self.fontfile)

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() and \
           self.parsed :
            return True
        else:
            return False

    def Update(self):           # ==== MANDATORY METHOD ====
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====
        ol = self.DefaultPreamble()
        #ol.append(gc.G00(x=0, y=0, c="Rapid move to start point!!!"))
        #ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))
        ol.append(gc.G(64, p=self.g64, c="Blend path mode"))
        if self.parsed and not self.text=="":
            scalex, scaley = self.GetScale()
            ol2 = self.GetTextGcode(self.text, scalex, scaley)
            if self.mirrorv:
                for o in ol2:
                    try:     o.x = o.x * -1
                    except:  pass
            if self.mirrorh:
                for o in ol2:
                    try:     o.y = o.y * -1
                    except:  pass
            ol += ol2
        ol.append(gc.G(61, c="Exact path mode"))
        ol += self.DefaultPostamble()
        return ol

    def GetTextGcode(self, text, scalex, scaley):
        """Generates the g-code for the whole text"""
        ol = []
        if scaley==1: ch = self.font.ymax
        else:         ch = self.char_height
        if self.arcjust==0: r = self.radius - ch
        else:               r = (self.radius - self.GetTextHeight(text, scaley)) * -1
        row = 0
        for line in text.split("\n"):
            if line=="": break
            linewidth = self.GetTextWidth(line, scalex)
            c = f2v.CharToKey(line[0])
            if self.align==0 or self.align==3 or self.align==6:      # left
                x = 0 - self.font.chars[c].xmin
            elif self.align==1 or self.align==4 or self.align==7:    # center
                x = -linewidth / 2
            elif self.align==2 or self.align==5 or self.align==8:    # right
                x = - linewidth + self.font.chars[c].xmin
            else:                                                    # default
                x = 0
            for c in line:
                c = f2v.CharToKey(c)
                if not self.font.HasChar(c): break
                o = self.GetCharGcode(c, scalex, scaley)
                if not self.radius==0 and not self.radius=="" and not self.radius==None:    # circular text
                    a = mu.ArcAngle(x+self.font.chars[c].xmax*scalex/2,r)
                    for oo in o:
                        oo.Rotate([0+self.font.chars[c].xmax*scalex/2,-r],-a)
                        oo.AddOffset([-self.font.chars[c].xmax*scalex/2,r,0])
                else:                                                                       # normal text
                    for oo in o:
                        oo.AddOffset([x,row,0])
                ol += o
                x += self.font.chars[c].xmax * scalex + self.char_space
            r -= self.line_space
            row -= self.line_space
        return ol

    def GetCharGcode(self, char, scalex, scaley):
        """Returns the g-code of the given character aligned to 0,0"""
        ol = []
        if char==" ": return ol
        if not self.font.HasChar(char): return ol

        z = self.z0
        while z > self.z1:
            z -= self.zi
            if z < self.z1:
                z = self.z1
            x1 = y1 = -1000
            first_stroke = True
            for stroke in self.font.chars[char].stroke_list:
                x0, y0 = stroke.x0 * scalex, stroke.y0 * scaley
                dist = mu.PointsDistance([x0,y0],[x1,y1])
                if dist>0.001 or first_stroke:
                    first_stroke = False
                    ol.append(gc.G00(z=self.zsh))                   # up
                    ol.append(gc.G00(x=x0, y=y0))                   # rapid move to start
                    ol.append(gc.G00(z=z+0.1))                      # rapid move down
                    ol.append(gc.G01(z=z, f=self.frtd))             # down
                x1, y1 = stroke.x1 * scalex, stroke.y1 * scaley
                ol.append(gc.G01(x=x1, y=y1))                       # engrave
        return ol

    def GetTextWidth(self, text, scalex):
        """Returns the width of the text"""
        l = 0
        for c in text:
            c = f2v.CharToKey(c)
            if not self.font.HasChar(c):
                l += self.font.xmax * scalex + self.char_space
            else:
                if self.font.chars[c].xmin>=0:
                    l += self.font.chars[c].xmax * scalex + self.char_space
                else:
                    l += self.font.chars[c].xmax * scalex + self.char_space
        c = f2v.CharToKey(text[0])
        if self.font.HasChar(c):
            l -= self.char_space - self.font.chars[c].xmin
        return l

    def GetTextHeight(self, text, scaley):
        """Returns the height of the text"""
        if not scaley==1: l = text.count("\n") * self.char_height
        else:             l = text.count("\n") * self.font.ymax
        return l

    def GetScale(self):
        """Returns the scale factor for x and y. If height or with are zero, the scale is set one."""
        if self.char_width==0 or self.char_height==0:
            scalex = scaley = 1
        else:
            scalex = self.char_width / self.font.wmax
            scaley = self.char_height / self.font.hmax
        return scalex, scaley

    def LoadFont(self, fn):
        """Loads the given fontfile"""
        self.font = f2v.LoadFont(fn, self.arcres)
        if self.font==None:
            self.parsed = False
            self.fontfile = ""
        else:
            self.parsed = True
            self.fontfile = fn
        return self.parsed

    def GetWholeFont(self):
        """Returns all "usable" characters of the current font"""
        text = ""
        for key in self.font.chars:
            text += chr(key)
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)        # remove control characters
        text = self.InsertNewLine(text, step=10)
        return text

    def InsertNewLine(self, text, step=80):
        """Inserts new line characters into the given string"""
        return '\n'.join(text[i:i+step] for i in range(0, len(text), step))


class Relief(Basedata, Basemethods):  # ========================================  UNDER DEVELOPMENT!!!
    """Generate g-code from an image"""

    name="Relief"
    description="Milling an image"
    i = 0

    def __init__(self):         # ==== MANDATORY METHOD ====
        self.__class__.i += 1
        super(Relief, self).__init__()

        self.fn_image = ""          # filename of the image
        self.image = None
        self.image_width = ""
        self.image_height = ""
        self.scale = 0.5
        self.cuth = True
        self.cutv = False

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() :
            return True
        else:
            return False

    def Update(self):           # ==== MANDATORY METHOD ====
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====
        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=0, y=0, c="Rapid move to start point"))
        ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))
        ol.append(gc.G01(z=0, f=self.frtd))
        ol.append(gc.G(64, p=0.1, c="Blend path mode"))
        ol += self.Gif2Gcode(self.posx, self.posy, self.z0)
        ol.append(gc.G(61, c="Exact path mode"))
        ol += self.DefaultPostamble()
        return ol

    def Gif2Gcode(self, x0, y0, z0):
        if self.image==None: return []
        ol = []
        colmax = max(list(self.image.getdata()))
        factor = self.z1 / colmax

        pix = self.image.load()
        xmax = self.image_width
        ymax = self.image_height
        f = self.scale

        if self.cuth:
            pix_= pix__ = 1000
            reverse = False
            ol.append(gc.G00(x=x0, y=y0, z=z0))
            x = 0
            for y in range(self.image_height):
                ol.append(gc.G01(x=x0+x*f, y=y0+y*f))
                for x in range(self.image_width):
                    if reverse: x = self.image_width - x - 1
                    if pix_==pix[x,y]:
                        ol.append(gc.G01(x=x0+x*f, y=y0+y*f))
                    else:
                        ol.append(gc.G01(x=x0+x*f, y=y0+y*f, z=self.z1-pix[x,y]*factor))
                    if pix_==pix__==pix[x,y]:
                        ol.pop(-2)
                    pix__ = pix_
                    pix_ = pix[x,y]
                if reverse:  reverse = False
                else:        reverse = True
                pix_= 1000
                ol.append(gc.G01(z=z0))

        if self.cutv:
            pix_= pix__ = 1000
            reverse = False
            ol.append(gc.G00(x=x0, y=y0, z=z0))
            y = 0
            for x in range(self.image_width):
                ol.append(gc.G01(x=x0+x*f, y=y0+y*f))
                for y in range(self.image_height):
                    if reverse: y = self.image_height - y - 1
                    if pix_==pix[x,y]:
                        ol.append(gc.G01(x=x0+x*f, y=y0+y*f))
                    else:
                        ol.append(gc.G01(x=x0+x*f, y=y0+y*f, z=self.z1-pix[x,y]*factor))
                    if pix_==pix__==pix[x,y]:
                        ol.pop(-2)
                    pix__ = pix_
                    pix_ = pix[x,y]
                if reverse:  reverse = False
                else:        reverse = True
                pix_= 1000
                ol.append(gc.G01(z=z0))
        return ol

    def Calc(self):
        print("Start...")
        print(self.image.format)
        print(self.image.size)
        print(self.image.mode)
        #print self.image.getcolors()
        print(max(list(self.image.getdata())))
        print(min(list(self.image.getdata())))
        #pix = self.image.load()
        #print pix[0,0]
        #print self.image.getpixel(10, 20)
        print("...End")

    def LoadImage(self, fn):
        """Loads the given image file"""
        try:
            self.image = Image.open(fn)
            self.image = self.image.rotate(180)
            self.image_width, self.image_height = self.image.size
            self.fn_image = fn
            return self.image
        except:
            self.image = None
            self.fn_image = ""
            return None


class Subroutine(Basemethods):  # ==============================================
    """Generate g-code with subroutines"""

    name="Subroutine"
    description="NGC subroutine"
    i = 0

    def __init__(self):         # ==== MANDATORY METHOD ====
        self.__class__.i += 1

        self.objectname = self.name + "_" + str(self.i)
        self.number = None                                                      # number of the routine
        self.valuelist = []                                                     # list of values to pass to the subroutine
        self.incsub = True                                                      # include the subroutine into the g-code

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.number>=0 and \
           self.number<len(ngcsub.SUBROUTINES) :
            return True
        else:
            return False

    def Update(self):           # ==== MANDATORY METHOD ====
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====
        command = "o<" + ngcsub.SUBROUTINES[self.number].name + "> CALL"
        for v in self.valuelist:
            if not v=="": command += " [" + str(v) + "]"
        ol = []
        if self.incsub: ol.append(gc.TEXT(ngcsub.SUBROUTINES[self.number].code))
        ol.append(gc.TEXT(command))
        return ol


class Counterbore(Basedata, Basemethods):  # ===================================
    """Generate g-code for TEMPLATE"""

    name="Counterbore"
    description="Counterbore"
    i = 0

    def __init__(self, d=1, d1=1, d2=1, T=1, t=0):
        self.__class__.i += 1
        super(Counterbore, self).__init__()

        self.d = d                  # through hole diameter
        self.T = T                  # Sinkhole depth
        self.d1 = d1                # Head sinkhole diameter
        self.d2 = d2                # 90° Phase for compensation of head reinforcement. From M12 on.
        self.t = t                  # washer height
        self.z1 = -10

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.d>=self.td and \
           self.d1>=self.td and \
           abs(self.z1)>=(self.T + self.t):
            return True
        else:
            return False

    def Update(self):           # ==== MANDATORY METHOD ====
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====
        ol = []
        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=0, y=0, c="Rapid move to start point"))
        ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))
        ol.append(gc.G01(z=self.z0))
        ri = dr = self.td * self.so / 100
        ra = self.d1 / 2.0 - self.td / 2.0
        ol.append(gc.G(61))
        ol += self.PocketCircle(gc.G03,self.z0,(-self.T-self.t),self.zi,ri,ra,dr)
        ra = self.d / 2.0 - self.td / 2.0
        ol.append(gc.G(61))
        ol += self.PocketCircle(gc.G03,(-self.T-self.t),self.z1,self.zi,ri,ra,dr)
        ol.append(gc.G01(x=0, y=0, f=self.frtd))
        ol.append(gc.G(61))
        ol += self.DefaultPostamble()
        return ol

    def PocketCircle(self,fn,z0,z1,zi,ri,ra,dr):
        ol = []
        if ri>=ra:
            turns = math.ceil(abs((z1-z0)/zi))
            ol.append(gc.G01(x=ra, y=0, f=self.frtd))
            ol.append(gc.G(64))
            ol.append(fn(x=ra, y=0, z=z1, i=-ra, j=0, p=turns, f=self.frso))
            ol.append(fn(x=ra, y=0, i=-ra, j=0, f=self.frso))
            ol.append(fn(x=0, y=ra, i=-ra, j=0, f=self.frso))
            return ol
        z = z0
        while z > z1:
            z -= zi
            if z < z1: z = z1
            r = ri - dr
            spiralin = True
            while r < ra:
                r += dr
                if r > ra: r = ra
                if spiralin:
                    ol.append(gc.G01(x=r, y=0, f=self.frtd))
                    ol.append(gc.G(64))
                    ol.append(fn(x=r, y=0, z=z, i=-r, j=0, f=self.frtd))
                    ol.append(fn(x=r, y=0, i=-r, j=0, f=self.frso))
                    spiralin = False
                ol.append(gc.G01(x=r, y=0, f=self.frtd))
                ol.append(fn(x=r, y=0, i=-r, j=0, f=self.frso))
            ol.append(fn(x=0, y=r, i=-r, j=0, f=self.frso))
        return ol

    class Positions():
        def __init__(self, x=0, y=0, z=0):
            self.x = x
            self.y = y
            self.z = z


class TEMPLATE(Basedata, Basemethods):  # ======================================
    """Generate g-code for TEMPLATE"""

    name="PocketCircle"
    description="Pocketing a circle"
    i = 0

    def __init__(self):         # ==== MANDATORY METHOD ====
        self.__class__.i += 1
        super(PocketCircle, self).__init__()

    def ParametersOk(self):     # ==== RECOMMENDED METHOD ====
        """Check the variables for plausibility, e.g. avoid endless loops"""
        if self.BaseparametersOK() :
            return True
        else:
            return False

    def Update(self):           # ==== MANDATORY METHOD ====
        """Calculates the path for the nc-object and returns it as a list of gcode-objects"""
        if not self.ParametersOk(): return [gc.COMMENT("PARAMETER ERROR")]  # ==== RECOMMENDED CALL ====

        ol = self.DefaultPreamble()
        ol.append(gc.G00(x=0, y=0, c="Rapid move to start point"))
        ol.append(gc.G00(z=self.z0 + self.zsh0, c="Rapid down to workpiece"))
        z = self.z0
        while z > self.z1:
            z -= self.zi
            if z < self.z1:
                z = self.z1
            ol.append(gc.G01(z=z, f=self.frtd))
        #ol.append(gc.G00(z=self.zsh, c="To safety height"))
        ol += self.DefaultPostamble()
        return ol


# ==============================================================================
# List of all available NC-Classes (need to be the same order as GUI-Classes)
NCCLASSES = [CustomCode,
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
