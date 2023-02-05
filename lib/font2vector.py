#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
CXF-Font to Vectors.

Copyright (C) 2017  Erik Schuster  erik at muenchen - ist - toll dot de
The sourcecode is based on engrave-11.py from <Lawrence Glaister>.

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
170426    Erik Schuster   First version
170501    Erik Schuster   Added support for CXF-Version 2.x
                          Added support for clockwise arcs (AR)
170708    Erik Schuster   The font directory is now read from the sgg.ini file.

ToDo:
Optimise the path for each character.
Implement correct version recognition.
Implement parsing chinese, etc. Does not work yet.
"""

import math
import re
import ConfigParser

VERSION = "170501"                                                              # version of this file (jjmmtt)
DIR = ""                                                                        # path to cxf-fonts
DEBUG = False


def Init():  # =================================================================
    """Initialises the module"""
    config = ConfigParser.ConfigParser()
    config.read('sgg.ini')
    global DIR
    DIR = config.get('SIMPLEGCODEGENERATOR', 'SGG_CXF_FONTS_DIR', 0)


class Stroke(object):  # =======================================================
    """Defines a line"""

    def __init__(self, coords):
        self.x0, self.y0, self.x1, self.y1 = coords
        self.xmax = max(self.x0, self.x1)
        self.xmin = min(self.x0, self.x1)
        self.ymax = max(self.y0, self.y1)
        self.ymin = min(self.y0, self.y1)
        
    def __repr__(self):
        return "Line[%s, %s, %s, %s]" % (self.x0, self.y0, self.x1, self.y1)
 

class Character(object):  # ====================================================
    """Defines a character made of strokes(lines)"""

    def __init__(self, key, strokelist=[]):
        self.key = key
        self.stroke_list = strokelist                                           # list of instances of <Stroke>
        self.xmin = self.get_xmin()
        self.xmax = self.get_xmax()
        self.ymin = self.get_ymin()
        self.ymax = self.get_ymax()
        self.width = self.xmax # - self.xmin
        self.height = self.ymax - self.ymin

    def get_xmax(self):
        try: return max([s.xmax for s in self.stroke_list[:]])
        except ValueError: return 0

    def get_xmin(self):
        try: return min([s.xmin for s in self.stroke_list[:]])
        except ValueError: return 0

    def get_ymax(self):
        try: return max([s.ymax for s in self.stroke_list[:]])
        except ValueError: return 0
        
    def get_ymin(self):
        try: return min([s.ymin for s in self.stroke_list[:]])
        except ValueError: return 0
        
    def __repr__(self):
        return "Character([%s, %s, %s, %s, %s, %s])" % (self.xmin, self.ymin, self.xmax, self.xmax, self.width, self.height)


class Font(object):  # =========================================================
    """Defines a complete font made of a dictionary of Characters"""

    def __init__(self, chars={}, name=None, ls=None, ws=None, lsf=None):
        self.chars = chars                                                      # dictionary of instances of <Character>
        self.xmin =  min([self.chars[key].xmin for key in self.chars])
        self.xmax =  max([self.chars[key].xmax for key in self.chars])
        self.ymin =  min([self.chars[key].ymin for key in self.chars])
        self.ymax =  max([self.chars[key].ymax for key in self.chars])
        self.hmax = self.ymax - self.ymin
        self.wmax = self.xmax - self.xmin
        
        self.name = name            # font name
        self.ls = ls                # letter spacing
        self.ws = ws                # word spacing
        self.lsf = lsf              # line spacing factor
        
    def HasChar(self, key):
        if key in self.chars:   return True
        else:                   return False


def CharToKey(c):  # ===========================================================
    """Translates a character to integer (the keys in the font dictionary are integers)"""
    if len(c)==1: c = ord(c)
    else: c = int(c, 16)
    return c


def LoadFont(fn, arcres):  # ===================================================
    """Load and parse the file and return an instance of <Font>"""
    try:
        file = open(fn, 'r')
        font = ParseCXF(file, arcres)
        file.close()
        return font
    except:
        if DEBUG: print("<LoadFont> : Error loading and/or parsing font file.")
        return None


def ParseCXF(file, arcres):  # =================================================
    """Parse the given file and create a font set"""
    chars = {}
    key = version = ws = ls = lsf = name = None
    xmax = 0                      # maximum x-value of all parsed characters
    n_lines = nc = cnt = 0        # for debuggung only
    new_cmd = False
    for line in file:
        n_lines += 1
        
        if not name:                                                            # determine font name
            name = re.match("^#\sName:\s*(.*)", line)
            if name:
                name =  name.group(1)
                if DEBUG: print("Font name:", name)
        
        if not version:                                                         # determine cxf-version
            version = re.match("^#\sVersion:\s*(.*)", line)
            if version:
                version = version.group(1)
                if len(version)<6:  version = 1                                 # bad workaround!!!!
                else:               version = 2                                 # xcf-version 1+2 are different to 2.0.1.3
                if DEBUG: print("CXF-version:", version)
        
        if not ws:                                                              # determine word spacing
            ws = re.match("^#\sWordSpacing:\s*(.*)", line)
            if ws:
                ws = float(ws.group(1))
                if DEBUG: print("Word spacing:", ws)
                
        if not ls:                                                              # determine letter spacing
            ls = re.match("^#\sLetterSpacing:\s*(.*)", line)
            if ls:
                ls = float(ls.group(1))
                if DEBUG: print("Letter spacing:", ls)
                
        if not lsf:                                                             # determine line spacing factor
            lsf = re.match("^#\sLineSpacingFactor:\s*(.*)", line)
            if lsf:
                lsf = float(lsf.group(1))
                if DEBUG: print("Line spacing factor:", lsf)
        
        end_char = re.match('^$', line)                                         # blank line
        
        if end_char and key:                                                    # parsing of one character completed
            if not key in chars:                                                # save the character to our dictionary
                chars[key] = Character(key, stroke_list)                        # add character to dictionary
                cnt += 1
                if DEBUG: print(u"Line:%3d #%3d <%s> %s %s" % (nc, cnt, key, type(key), unichr(key)))
            
        if version==1:
            new_cmd = re.match('^\[(.*)\]\s(\d+)', line)
        elif version==2:
            new_cmd = re.match('^\[(.*)\]\s(.*)', line)
        else:
            new_cmd = False
        
        if new_cmd:                                                             # new character
            nc = n_lines
            if version==1:
                key = new_cmd.group(1)
            elif version==2:
                key = new_cmd.group(2)
            try:
                if len(key)==1:     key = ord(key)
                elif len(key)==2:   key = ord(key[1])
                elif len(key)==4:   key = int(key, 16)
                elif len(key)==5:   key = int(key[1:], 16)
                else: raise
            except:
                new_cmd = False
                key = None
                if DEBUG: print("Character ignored")
            stroke_list = []
        
        line_cmd = re.match('^L (.*)', line)
        
        if line_cmd:                                                            # new line
            coords = line_cmd.group(1)
            coords = [float(n) for n in coords.split(',')]
            xmax = max(xmax,coords[0],coords[2])
            stroke_list += [Stroke(coords)]
        
        arc_cmd = re.match('^(A.*) (.*)', line)
        
        if arc_cmd:                                                             # new arc
            coords = arc_cmd.group(2)
            coords = [float(n) for n in coords.split(',')]
            xcenter, ycenter, radius, start_angle, end_angle = coords
            if arc_cmd.group(1)=="A":                                           # arc counter clockwise
                if start_angle > end_angle: degs = 360 + end_angle - start_angle
                else:                       degs = end_angle - start_angle
            else:                                                               # arc clockwise
                if start_angle > end_angle: degs = start_angle - end_angle
                else:                       degs = 360 - end_angle + start_angle
            segs = int(degs/arcres)+1
            angleincr = degs/segs
            xstart = math.cos(start_angle * math.pi/180) * radius + xcenter
            ystart = math.sin(start_angle * math.pi/180) * radius + ycenter
            angle = start_angle
            xmax = max(xmax,xstart)
            for i in range(segs):
                if arc_cmd.group(1)=="A": angle += angleincr
                else:                     angle -= angleincr
                xend = math.cos(angle * math.pi/180) * radius + xcenter
                yend = math.sin(angle * math.pi/180) * radius + ycenter
                coords = [xstart,ystart,xend,yend]
                stroke_list += [Stroke(coords)]
                xmax = max(xmax,xend)
                xstart = xend
                ystart = yend
    
    if not ws: ws = xmax                                                        # Add a "Space"-Character
    c = Character(ord(" "), [])
    c.width = ws
    chars[ord(" ")] = c
    chars[ord(" ")].xmax = ws
    chars[ord(" ")].wmax = ws
    if DEBUG: print("Font <%s> parsed (%d lines)." % (name,n_lines))
    return Font(chars, name=name, ls=ls, ws=ws, lsf=lsf)
