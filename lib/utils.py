#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Purpose of the file:
Common utility functions.

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
170516    Erik Schuster   First version
"""

import copy

VERSION = "230206"                                                              # version of this file (jjmmtt)


def ListItemsMoveUp(li, indexes):
    """Moves down the given indexes in the list"""
    indexes = list(map(int, indexes))
    if not indexes[0]==0:
        for i in indexes:
            o = li.pop(int(i))
            li.insert(int(i) - 1, o)
        indexes = [i-1 for i in indexes]
    return indexes


def ListItemsMoveDown(li, indexes):
    """Moves down the given indexes in the list"""
    indexes = list(map(int, indexes))
    indexes = sorted(list(indexes), reverse=True)
    if not indexes[0]>=(len(li)-1):
        for i in indexes:
            o = li.pop(int(i))
            li.insert(int(i) + 1, o)
        indexes = [i+1 for i in indexes]
    return indexes


def ListItemsDelete(li, indexes):
    """Deletes the given indexes in the list"""
    try:
        indexes = sorted(list(map(int, indexes)), reverse=True)
    except:
        pass
    for i in indexes:
        if len(li)>=i:
            li.pop(int(i))


def ListItemDublicate(li, index):
    """Dublicate the given index in the list and insert at index+1"""
    li.insert(index + 1, copy.deepcopy(li[index]))
    return (index + 1)
