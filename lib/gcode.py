#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Provides the classes for basic g-codes.

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

ToDo:
- Optimise the number of classes and code
"""

import math
import numpy

from . import mathutils as mu

VERSION = "230206"                                                              # version of this file (jjmmtt)

# FORMAT
# TEXT, COMMENT
# T, F, M, G00, G01, G02, G03, G83

class FORMAT(object):  # =======================================================
    """Formatting of g-code"""

    def FV(self, v):
        """Returns a floating point number as a formatted string for g-code output file"""
        return ('%4.4f' % v)

    def CMT(self, c):
        """Returns a comment string"""
        return "\t\t\t\t\t\t( " + str(c) + " )"


class TEXT(FORMAT):  # =========================================================
    """Implemets a plain text"""

    def __init__(self, text, c=None):
        self.t = text
        self.c = c

    def GetGcode(self):
        """Retuns the g-code as a string"""
        g = self.t
        if self.c is not None:
                g += self.CMT(self.c)
        return g


class COMMENT(FORMAT):  # ======================================================
    """Implemets a comment for g-code"""

    def __init__(self, comment):
        self.c = comment

    def GetGcode(self):
        """Retuns the g-code as a string"""
        return "( " + str(self.c) + " )"


class T(FORMAT):  # ============================================================
    """Implements tool selection"""

    name = "T"
    description = "Tool select"

    def __init__(self, tn=None, c=None):
        self.tn = tn
        self.c = c

    def GetGcode(self):
        """Retuns the g-code as a string"""
        if self.tn is not None:
            g = "T" + str(self.tn)
            if self.c is not None:
                g += self.CMT(self.c)
        else:
            g = "T!!  ( *** ERROR *** )"
        return g


class F(FORMAT):  # ============================================================
    """Implements feed rate command"""

    name = "F"
    description = "Feed rate command"

    def __init__(self, f, c=None):
        self.f = f
        self.c = c

    def GetGcode(self):
        """Retuns the g-code as a string"""
        if self.f is not None:
            g = "F" + str(self.f)
            if self.c is not None: g += self.CMT(self.c)
        else:
            g = "F!!  ( *** ERROR *** )"
        return g


class M(FORMAT):  # ============================================================
    """Implements tool selection"""

    name = "M"
    description = "Machine command"

    def __init__(self, n, s=None, c=None):
        self.n = n
        self.s = s
        self.c = c

    def GetGcode(self):
        """Retuns the g-code as a string"""
        if self.n is not None:
            g = "M" + str(self.n)
            if self.s is not None: g += " S" + self.FV(self.s)
            if self.c is not None: g += self.CMT(self.c)
        else:
            g = "M!!  ( *** ERROR *** )"
        return g


class G(FORMAT):  # ============================================================
    """Implements default g-command"""

    name = "G"
    description = "Default command"

    def __init__(self, n, p=None, q=None, c=None):
        self.n = n
        self.c = c
        self.p = p
        self.q = q

    def GetGcode(self):
        """Retuns the g-code as a string"""
        if self.n is not None:
            g = "G" + str(self.n)
            if self.p is not None: g += " P" + self.FV(self.p)
            if self.q is not None: g += " Q" + self.FV(self.q)
            if self.c is not None: g += self.CMT(self.c)
        else:
            g = "M!!  ( *** ERROR *** )"
        return g


class G00(FORMAT):  # ====================================================
    """Implements the g-code G00, rapid move"""

    name = "G00"
    description = "Rapid move"

    def __init__(self, x=None, y=None, z=None, f=None, c=None):
        self.x = x
        self.y = y
        self.z = z
        self.f = f
        self.c = c

    def AddOffset(self, o):
        if self.x is not None: self.x += o[0]
        if self.y is not None: self.y += o[1]
        if self.z is not None: self.z += o[2]

    def Rotate(self, c, d):  # c=[x,y,z], d=n°
        if not self.x==None and not self.y==None:
            [self.x, self.y] = mu.PointRotate([self.x, self.y], c, d)

    def GetGcode(self):
        """Retuns the g-code as a string"""
        g = "G00"
        if self.x is not None: g += " X" + self.FV(self.x)
        if self.y is not None: g += " Y" + self.FV(self.y)
        if self.z is not None: g += " Z" + self.FV(self.z)
        if self.f is not None: g += " F" + self.FV(self.f)
        if self.c is not None: g += self.CMT(self.c)
        return g


class G01(FORMAT):  # ====================================================
    """Implements the g-code G01, linear move"""

    name = "G01"
    description = "Linear interpolated move"

    def __init__(self, x=None, y=None, z=None, f=None, c=None):
        self.x = x
        self.y = y
        self.z = z
        self.f = f
        self.c = c

    def AddOffset(self, o):
        if self.x is not None: self.x += o[0]
        if self.y is not None: self.y += o[1]
        if self.z is not None: self.z += o[2]

    def Rotate(self, c, d):  # c=[x,y,z], d=n°
        if not self.x==None and not self.y==None:
            [self.x, self.y] = mu.PointRotate([self.x, self.y], c, d)

    def GetGcode(self):
        """Retuns the g-code as a string"""
        g = "G01"
        if self.x is not None: g += " X" + self.FV(self.x)
        if self.y is not None: g += " Y" + self.FV(self.y)
        if self.z is not None: g += " Z" + self.FV(self.z)
        if self.f is not None: g += " F" + self.FV(self.f)
        if self.c is not None: g += self.CMT(self.c)
        return g


class G02(FORMAT):  # ====================================================
    """Implements the g-code G02, clockwise arc"""

    name = "G02"
    description = "Arc clockwise"

    def __init__(self, x=None, y=None, z=None, i=None, j=None, k=None, p=None, f=None, c=None):
        self.x = x
        self.y = y
        self.z = z
        self.i = i
        self.j = j
        self.k = k
        self.p = p
        self.f = f
        self.c = c

    def AddOffset(self, o):
        if self.x is not None: self.x += o[0]
        if self.y is not None: self.y += o[1]
        if self.z is not None: self.z += o[2]

    def Rotate(self, c, d):  # p=[x,y,z], d=n°
        if not self.x==None and not self.y==None:
            [self.x, self.y] = mu.PointRotate([self.x, self.y], c, d)
        if not self.i==None and not self.j==None:
            [self.i, self.j] = mu.PointRotate([self.i, self.j], [0,0], d)

    def GetGcode(self):
        """Retuns the g-code as a string"""
        g = "G02"
        if self.x is not None: g += " X" + self.FV(self.x)
        if self.y is not None: g += " Y" + self.FV(self.y)
        if self.z is not None: g += " Z" + self.FV(self.z)
        if self.i is not None: g += " I" + self.FV(self.i)
        if self.j is not None: g += " J" + self.FV(self.j)
        if self.k is not None: g += " K" + self.FV(self.k)
        if self.p is not None: g += " P" + self.FV(self.p)
        if self.f is not None: g += " F" + self.FV(self.f)
        if self.c is not None: g += self.CMT(self.c)
        return g


class G03(FORMAT):  # ====================================================
    """Implements the g-code G03, counter clockwise arc"""

    name = "G03"
    description = "Arc counter clockwise"

    def __init__(self, x=None, y=None, z=None, i=None, j=None, k=None, p=None, f=None, c=None):
        self.x = x
        self.y = y
        self.z = z
        self.i = i
        self.j = j
        self.k = k
        self.p = p
        self.f = f
        self.c = c

    def AddOffset(self, o):
        if self.x is not None: self.x += o[0]
        if self.y is not None: self.y += o[1]
        if self.z is not None: self.z += o[2]

    def Rotate(self, c, d):  # p=[x,y,z], d=n°
        if not self.x==None and not self.y==None:
            [self.x, self.y] = mu.PointRotate([self.x, self.y], c, d)
        if not self.i==None and not self.j==None:
            [self.i, self.j] = mu.PointRotate([self.i, self.j], [0,0], d)

    def GetGcode(self):
        """Retuns the g-code as a string"""
        g = "G03"
        if self.x is not None: g += " X" + self.FV(self.x)
        if self.y is not None: g += " Y" + self.FV(self.y)
        if self.z is not None: g += " Z" + self.FV(self.z)
        if self.i is not None: g += " I" + self.FV(self.i)
        if self.j is not None: g += " J" + self.FV(self.j)
        if self.k is not None: g += " K" + self.FV(self.k)
        if self.p is not None: g += " P" + self.FV(self.p)
        if self.f is not None: g += " F" + self.FV(self.f)
        if self.c is not None: g += self.CMT(self.c)
        return g


class G83(FORMAT):  # ====================================================
    """Implements the g-code G83, drilling cycle peck"""

    name = "G83"
    description = "Drilling cycle, Peck"

    def __init__(self, x=None, y=None, z=None, r=None, l=None, q=None, f=None, c=None):
        self.x = x
        self.y = y
        self.z = z
        self.r = r
        self.l = l
        self.q = q
        self.f = f
        self.c = c

    def AddOffset(self, o):
        if self.x is not None: self.x += o[0]
        if self.y is not None: self.y += o[1]
        if self.z is not None: self.z += o[2]

    def Rotate(self, c, d):  # p=[x,y,z], d=n°
        if not self.x==None and not self.y==None:
            [self.x, self.y] = mu.PointRotate([self.x, self.y], c, d)

    def GetGcode(self):
        """Retuns the g-code as a string"""
        g = "G83"
        if self.x is not None: g += " X" + self.FV(self.x)
        if self.y is not None: g += " Y" + self.FV(self.y)
        if self.z is not None: g += " Z" + self.FV(self.z)
        if self.r is not None: g += " R" + self.FV(self.r)
        if self.l is not None: g += " L" + self.FV(self.l)
        if self.q is not None: g += " Q" + self.FV(self.q)
        if self.f is not None: g += " F" + self.FV(self.f)
        if self.c is not None: g += self.CMT(self.c)
        return g
