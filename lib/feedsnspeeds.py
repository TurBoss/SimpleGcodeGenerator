#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Parses feedsnspeeds csv-files and provieds the data.

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
170725    Erik Schuster   First version
"""

import glob
import configparser
import csv

VERSION = "230206"                                                              # version of this file (jjmmtt)

DIR = ""                                                                        # 
TABLES = []                                                                     # List of instances of <Table>


def Init():  # =================================================================
    """Initialises the module"""
    config = configparser.ConfigParser()
    config.read('sgg.ini')
    global DIR
    DIR = config.get('SIMPLEGCODEGENERATOR', 'SGG_FEEDSNSPEEDS_DIR')
    if not LoadAllTables(""):
        print("Error loading feeds'n'speeds table.")


class Table():  # ==============================================================
    """Instance represents one parsed csv-file"""
    def __init__(self, filename, description, columnheaders, table):
        self.filename = filename
        self.description = description
        self.columnheaders = columnheaders
        self.table = table
        self.table.append(columnheaders)
        self.width = [max(len(str(x)) for x in line) for line in zip(*table)]
        self.table = self.table[0:-1]

    def __repr__(self):
        return "[%s\n%s]" % (self.description, self.table)


def LoadAllTables(path):  # ====================================================
    """Load and parse all .csv files in the given path for counterbore data and store them to <COUNTERBORE_TABLES>"""
    if path=="": path = DIR
    filelist = glob.glob(path + "/*.csv")
    if len(filelist)>0:
        filelist.sort()
        global TABLES
        TABLES = []
        for fn in filelist:
            inst = LoadTable(fn)
            if not inst==None:
                TABLES.append(inst)
        return True
    else:
        return False


def LoadTable(fn):  # ==========================================================
    """Load and parse the given file and return an instance of <Table>"""
    if fn=="": return None
    file = open(fn, 'r')
    reader = csv.reader(file, delimiter=';')
    description = author = data = columnheaders = datatable = None
    table = []
    for row in reader:
        if not description:
            if row[0]=="Description":
                description = row[1]
                continue
        if not author:
            if row[0]=="Author":
                author = row[1]
                continue
        if not data:
            if row[0]=="Data":
                data = True
                continue
        if data and not columnheaders:
            columnheaders = row[0:]
            datatable = True
            continue
        if datatable:
            table.append(row[0:])
    file.close()
    return Table(fn, description, columnheaders, table)

        
