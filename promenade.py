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


def _getfunc(str):
    for f in _filters:
        if f.regex.match(str):
            return (str,f.func)
    else:
        raise Exception("Could not find filter for '{}'".format(str))


def _apply_filters(inputs, filters):
    """ apply the list of filters to list of inputs """
    for args, func in filters:
        inputs = [func(i, args) for i in inputs]  
    return inputs


def _apply_str(input, filter_str):
    parts = [p for p in filter_str.split(delim) if p]
    filters = [_getfunc(p) for p in parts]
    return _apply_filters(input, filters)


def _apply_callable(input, filter_call):
    return _apply(input, [_Filter(None, filter_call)])


def walk(inputs, *steps, **options):
    """ data is the data structure you want to explore
    steps is a list of string, multi-part string, function, list of functions
    options is a list of named args
    """
    delim = options.get('delim', '/')

    for step in steps:
        if isinstance(step, str):
            inputs = _apply_str(inputs, step)

        elif hasattr(step, '__call__'):
            inputs = _apply_callable(inputs, step)

        # A list apply all function in sequence
        elif isinstance(step, list):
            outputs = []
            for i in inputs:
                for s in step:
                     i = walk([i], s, **options)
                outputs += i
            inputs = outputs

        # The set apply all filter to all inputs
        elif isinstance(step, set):
            outputs = []
            for i in inputs:
                for s in step:
                    outputs += walk(i, s, **options)
            inputs = outputs

        # The dict apply on set of filter to 
        elif isinstance(step, dict):
            output = []
            for i in inputs:
                for condition, sub_steps in step.items():
                    passed = walk(i, condition, **options)
                    if passed:
                        input = walk(output, sub_steps, **options)

    return inputs


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
