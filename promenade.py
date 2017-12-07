# -*- coding: utf-8 -*-
#
# promenade - a flexible filter for JSON
#
# Copyright 2017 Floran Francois
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import re
import collections
import unittest

# The func field is a function that takes one item and return a list of item.
_Filter = collections.namedtuple('_Filter', ['regex', 'func'])

#  list of all registered filters
_filters = []


def filter(regex, **options):
    """ A decorator factory to register a filter in the filters table. """
    def deco(func):
        _filters.append(_Filter(re.compile(regex),func))
        return func
    return deco


@filter(r'^[*]')
def _all(item, expr):
    """ Get all items. From dict is return items() """
    if 'items' in dir(item):
        return list(item.items())
    if '__iter__' in dir(item):
        return [i for i in item]
    return []


@filter(r'^\[.*\]$')
def _byeval(item, expr):
    """ Apply expr to item."""
    return [eval('item{}'.format(expr),{'item':item})]


@filter(r'^~.*')
def _byregex(item, regex):
    """ Return all value with key matching regex.
    The ~ is removed before compiling the regex.
    """
    if 'items' not in dir(item):
        return []

    r = re.compile(regex[1:])
    return [value for key,value in item.items() if r.match(key)]


# @filter(r'^(-?\d+)?\s*:\s*(-?\d+)?$')
# def _byslice(item, key):
#     if '__getitem__' in item:
#         return item[key]
#     return []


@filter(r'^[0-9]+$')
def _byindex(item, arg):
    if '__getitem__' in dir(item):
        i = int(arg)
        return [item[i]]
    return []


@filter(r'.*')
def _bykey(item, key):
    if '__getitem__' in dir(item):
        return [item[key]]
    return []


def _apply(item, filters):
    """ apply the list of function to item """
    input = [item]
    for args, func in filters:
        output = []
        for i in input:
            output += func(i, args)
        input = output  
    return input


def _getfunc(str):
    for f in _filters:
        if f.regex.match(str):
            return (str,f.func)
    else:
        raise Exception("Could not find filter for '{}'".format(str))


def walk(data, *steps, **options):
    """ data is the data structure you want to explore
    steps is a list of string, multi-part string, function, list of functions
    options is a list of named args
    """
    delim = options.get('delim', '/')
    path = []
    for step in steps:
        if isinstance(step, str):
            steps = [p for p in step.split(delim) if p]
            path += [_getfunc(p) for p in steps]

        elif hasattr(step, '__call__'):
            path.append((None, step))

        elif isinstance(step, list):
            for i in step:
                if isinstance(i, str):
                    path.append(_getfunc(i))

                elif hasattr(i, '__call__'):
                    path.append((None, i))
    return _apply(data, path)

def reset():
    _filters = []


_test_data = { 
    "clients" : [
        {
            "name": "Paul",
            "age" : 28,
            "hair" : "brown",
            "eyes" : "green",
            "likes" : ["bacon", "egg", "coffee"]
        },
        {
            "name": "Louis",
            "age" : 18,
            "hair" : "black",
            "eyes" : "blue",
            "likes" : ["toast", "jam", "juice"]
        },
        {
            "name": "Suzane",
            "age" : 35,
            "hair" : "red",
            "eyes" : "blue",
            "likes" : ["bacon", "pancake", "tea"]
        }
    ] 
}


class TestPromenade(unittest.TestCase):
    def test_00(self):
        s = walk(_test_data, 'clients', '0', 'likes/1')
        self.assertEqual(s[0],'egg')

    def test_01(self):
        def getit(data, *args):
            return [data[0]]
        s = walk(_test_data, 'clients', getit, 'likes/1')
        self.assertEqual(s[0],'egg')
'''
    def test_02(self):
        def getit(data, *args):
            return data[0]
        s = walk(_test_data, ['clients', getit], 'likes/1')
        self.assertEqual(s,'egg')

    def test_03(self):
        def getit(data, *args):
            return data[0]
        s = walk(_test_data, 'clients', getit, 'likes','1')
        self.assertEqual(s,'egg')'''

if __name__ == '__main__':
    unittest.main()
