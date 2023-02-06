#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Basic geometric/mathematical helper functions

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
170408    Erik Schuster   First version
170506    Erik Schuster   Bugifx: <ArcAngle>, catch division by zero.
"""

import math
import numpy

VERSION = "230206"                                                              # version of this file (jjmmtt)

def PointRotate(p, r, d):
    """Rotates a point around another point"""
    try:
        sin = math.sin(d * math.pi / 180.0)
        cos = math.cos(d * math.pi / 180.0)
        x = r[0] + (p[0] - r[0]) * cos - (p[1] - r[1]) * sin
        y = r[1] + (p[0] - r[0]) * sin + (p[1] - r[1]) * cos
    except Exception as e:
        #print e
        x = y = 0
    return [x, y]

def ArcAngle(l, r):
    """Calculate the angle of an arc with a given length and radius"""
    try:    return (l * 180.0) / (math.pi * r)
    except: return 0                                                            # catch division by zero

def ArcLength(a, r):
    """Calculates an arc length with a given angle an radius"""
    return (math.pi * r * a) / (180.0)

def PointsDistance(p1, p2):
    """Calulate the distance between two points"""
    d = numpy.array(p2) - numpy.array(p1)
    return numpy.sqrt((d * d).sum())

def GetPointOnLine(p0, p1, d):
    """Calculate the coordinates of a point on a line with a given distance from first point"""
    v = numpy.array(p1) - numpy.array(p0)
    v_abs = numpy.sqrt((v * v).sum())
    v1 = numpy.array(v) * 1/v_abs
    p2 = numpy.array(v1) * d + numpy.array(p0)
    return p2

def PointEllipse(a, b, t):
    """Calculates the coordinates for an ellipse"""
    t = t * 2 * math.pi / 360.0
    phi = 0
    x = a * math.cos(t) * math.cos(phi) - b * math.sin(t) * math.sin(phi)
    y = a * math.cos(t) * math.sin(phi) + b * math.sin(t) * math.cos(phi)
    return [x, y]
