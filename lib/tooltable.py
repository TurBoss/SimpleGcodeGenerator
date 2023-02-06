#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Parses the LinuxCNC tooltable.

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
170514    Erik Schuster   First version
170708    Erik Schuster   Now Paths to the tool table are read from the sgg.ini file.
"""

import re
import configparser

VERSION = "230206"                                                              # version of this file (jjmmtt)

PATH = ""                                                                       # Path to the default LinuxCNC tool table
DIR = ""                                                                        # Directory of tool tables
TOOLTABLE = []                                                                  # List of instances of <Tool>


def Init():  # =================================================================
    """Initialises the module"""
    config = configparser.ConfigParser()
    config.read('sgg.ini')
    global PATH
    PATH = config.get('LINUXCNC', 'LCNC_TOOLTABLE')
    global DIR
    DIR = config.get('LINUXCNC', 'LCNC_TOOLTABLE_DIR')
    if not LcncLoadToolTable(""):
        print("Error loading tool table. Check path in the file <sgg.ini>.")


class Tool(object):  # =========================================================
    """Represents a single tool"""
    def __init__(self, number, diameter, description=None):
        self.number = int(number)
        self.diameter = float(diameter)
        self.description = description


def LcncLoadToolTable(fn):  # ==================================================
    """Load the LinucCNC tool table and create a list of <Tool> instances in the global variable TOOLTABLE"""
    try:
        if fn=="": fn=PATH
        file = open(fn, 'r')
        global TOOLTABLE
        TOOLTABLE = []
        for line in file:
            t = re.match("T(\d+).*\sD([0-9.]+).*\s;(.*)", line)
            if t:  TOOLTABLE.append(Tool(t.group(1),t.group(2),t.group(3)))
        file.close()
        return True
    except:
        return False
