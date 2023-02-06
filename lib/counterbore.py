#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Parses counterbore csv-files and provieds the data.

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
170625    Erik Schuster   First version
170708    Erik Schuster   Now path to the csv-table is read from the sgg.ini file.
                          Uses csv module instead of re now.

ToDo
Handling of different number formats in <DrillTable> needs improvement.
"""

import csv
import glob
import configparser

VERSION = "230206"                                                              # version of this file (jjmmtt)

DIR = ""                                                                        # Directory of the counterbore tables
TABLES = []                                                                     # List of instances of <Table>


def Init():  # =================================================================
    """Initialises the module"""
    config = configparser.ConfigParser()
    config.read('sgg.ini')
    global DIR
    DIR = config.get('SIMPLEGCODEGENERATOR', 'SGG_COUNTERBORE_DIR')
    if not LoadAllTables(""):
        print("Error loading counter bore table. Check path in the file <sgg.ini>.")


class Data():  # ===============================================================
    """Simplified counterbore data for one type (e.g. M3 or 1/8")
    d = Throughhole diameter
    d1 = Head sinkhole diameter
    d2 = 90° Phase for compensation of head reinforcement. From M12 on.
    T = Sinkhole depth
    """
    def __init__(self, name, d, d1, d2, T):
        self.name = name
        try:    self.d = float(d.replace(",","."))
        except: self.d = 0
        try:    self.d1 = float(d1.replace(",","."))
        except: self.d1 = 0
        try:    self.d2 = float(d2.replace(",","."))
        except: self.d2 = 0
        try:    self.T = float(T.replace(",","."))
        except: self.T = 0

    def GetHeaders(self):
        return ["Name","d","d1","d2","T"]

    def __repr__(self):
        return "%s %s %s %s %s\n" % (self.name, self.d, self.d1, self.d2, self.T)


class Table():  # ==============================================================
    """Instance represents one parsed csv-file"""
    def __init__(self, filename, description, table):
        self.filename = filename
        self.description = description
        self.table = table                      # List of instances of <Data>

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


def LoadTable(fn):  # =====================================================
    """Load and parse the given file and return an instance of <Table>"""
    if fn=="": return None
    file = open(fn, 'r')
    reader = csv.reader(file, delimiter=';')
    description = None
    author = None
    headers = None
    remarks = None
    datatable = False
    table = []
    for row in reader:
        if not description:
            if row[0]=="Description":
                description = row[1]
                continue
        if not datatable:
            if row[0]=="name":
                datatable = True
                continue
        if datatable:
            table.append(Data(row[0],row[1],row[2],row[3],row[4]))
    file.close()
    return Table(fn, description, table)


