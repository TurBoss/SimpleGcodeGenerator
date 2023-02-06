#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Parses ngc-subroutines and provides a list of parameters

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
170531    Erik Schuster   First version
170708    Erik Schuster   The path to the subroutines is now read from the ini file.

ToDo
- Autoselect the LinuxCNC subroutines directory
"""

import re
import glob
import configparser

VERSION = "230206"                                                              # version of this file (jjmmtt)

PATH = ""                                                                       # path where to find the subroutines
SUBROUTINES = []                                                                # list of instances of <Sub>


def Init():  # =================================================================
    """Initialises the module"""
    config = configparser.ConfigParser()
    config.read('sgg.ini')
    global PATH
    PATH = config.get('SIMPLEGCODEGENERATOR', 'SGG_SUBROUTINES_DIR')
    if not LoadAllSubroutines(""):
        print("Error loading subroutines. Check path in the file <sgg.ini>.")


class Param(object):  # ========================================================
    """Holds a parameter name, paremeter number (1-30) and comment if available"""
    def __init__(self, name, number, comment=None):
        self.name = name                                                        # name of the parameter
        self.number = number                                                    # number of the parameter
        self.comment = comment                                                  # comment for the parameter

    def __repr__(self):
        return "Parameters([%s, %s, %s])" % (self.name, self.number, self.comment)


class Sub(object):  # ==========================================================
    """Represents a complete parsed subroutine"""
    def __init__(self, name, code, parameterlist):
        self.name = name                                                        # name of the subroutine
        self.code = code                                                        # g-code of the subroutine
        self.parlist = parameterlist                                            # list of parameters (instances of <Param>)

    def __repr__(self):
        return "Sub([%s, %s])" % (self.name, self.parlist)


def LoadAllSubroutines(path):  # ===============================================
    """Load and parse all .ngc files in the given path for a subroutine and store them to <SUBROUTINES>"""
    if path=="" : path=PATH
    filelist = glob.glob(path + "/*.ngc")
    if len(filelist)>0:
        filelist.sort()
        global SUBROUTINES
        SUBROUTINES = []
        for fn in filelist:
            inst = ParseNgcSub(fn)
            if not inst==None:
                SUBROUTINES.append(inst)
        return True
    else:
        return False


def ParseNgcSub(fn):  # ========================================================
    """Parse the given file and return an instance of <Sub>"""
    if fn=="": return None
    name = None
    parameters = []
    code = ""
    try:
        file = open(fn, 'r')
        for line in file:
            code += line
            if not name:                                                        # get name of subroutine
                t = re.match("o<(.*)>.*sub", line)
                if t: name = t.group(1)
            t = re.match(r".*?#<(.*)>.*=.*#(\d+)[^\(]*(?:\((.*)\))?", line)     # get all parameters up to #30
            if t and not t.group(2)=="" and int(t.group(2))<31:
                if t.group(3)==None: comment = ""
                else: comment = t.group(3)
                parameters.append(Param(t.group(1),t.group(2),comment))
        file.close()
        if not name: return None
        return Sub(name,code,parameters)
    except Exception as e:
        print(e)
        return None

