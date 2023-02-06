#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Provides functions for milling simple shapes.

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
170708    Erik Schuster   First version
"""

import math
from . import mathutils as mu                                                          # import math helper functions
from . import gcode as gc                                                              # import basic g-code classes
from . import utils                                                                    # common utility functions

VERSION = "230206"                                                             # version of this file (jjmmtt)


def CalcRPM(vc,d):  # ==========================================================
    """Calculate the proper spindle speed
    vc = Cutting speed
    d = tool diameter
    """
    return (vc*1000)/(math.pi * d)


def CalcFeed(n, z, fz):  # =====================================================
    """Calculate the proper feed rate
    n = rpm [1/min]
    z = Number of teeth
    fz = Feed per tooth [mm/U]
    """
    return (n * z * fz)


def PocketRectangle(x,y,z,frtd,frso,r=[0,0,0,0], c=False):
    """
        Creates a list of g-code instances
    """
    ol = []

    return ol


def PocketCircle(fn,z0,z1,zi,ri,ra,rd,frtd,frso): # # ==========================
    """
        Creates a list of g-code instances
        fn = reference to gcode function (G02 or G03)
        z0 = z start
        z1 = z end
        zi = z increment
        ri = inner radius
        ra = outer radius
        rd = radius delta
        frtd = feedrate @ tool diameter
        frso = feedrate @ step over
    """
    ol = []
    if ri>=ra:
        turns = math.ceil(abs((z1-z0)/zi))
        ol.append(gc.G01(x=ra, y=0, f=frtd))
        ol.append(gc.G(64))
        ol.append(fn(x=ra, y=0, z=z1, i=-ra, j=0, p=turns, f=frso))
        ol.append(fn(x=ra, y=0, i=-ra, j=0, f=frso))
    else:
        z = z0
        while z > z1:
            z -= zi
            if z < z1: z = z1
            r = ri - rd
            spiralin = True
            while r < ra:
                r += rd
                if r > ra: r = ra
                if spiralin:
                    ol.append(gc.G01(x=r, y=0, f=frtd))
                    ol.append(gc.G(64))
                    ol.append(fn(x=r, y=0, z=z, i=-r, j=0, f=frtd))
                    if r==ri and z==z1: ol.append(fn(x=r, y=0, i=-r, j=0, p=2, f=frso))
                    else: ol.append(fn(x=r, y=0, i=-r, j=0, f=frso))
                    spiralin = False
                if not r==ri:
                    ol.append(gc.G01(x=r, y=0, f=frtd))
                    ol.append(fn(x=r, y=0, i=-r, j=0, f=frso))
            ol.append(fn(x=r, y=0, i=-r, j=0, f=frso))
    return ol
