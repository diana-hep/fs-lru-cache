#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import tempfile
import unittest

from hepquery.cache import *

def lstree(base, path=""):
    for item in sorted(os.listdir(os.path.join(base, path))):
        if os.path.isdir(os.path.join(base, path, item)):
            yield os.path.join(path, item) + os.sep
            for x in lstree(base, os.path.join(path, item)):
                yield x
        else:
            yield os.path.join(path, item)

class TestCache(unittest.TestCase):
    def runTest(self):
        pass
    
    def test_directory_structure(self):
        expected = [
            ["0.a"],
            ["0.a", "1.b"],
            ["0.a", "1.b", "2.c"],
            ["0/", "0/0.a", "0/1.b", "0/2.c", "1/", "1/0.d"],
            ["0/", "0/0.a", "0/1.b", "0/2.c", "1/", "1/0.d", "1/1.e"],
            ["0/", "0/0.a", "0/1.b", "0/2.c", "1/", "1/0.d", "1/1.e", "1/2.f"],
            ["0/", "0/0.a", "0/1.b", "0/2.c", "1/", "1/0.d", "1/1.e", "1/2.f", "2/", "2/0.g"],
            ["0/", "0/0.a", "0/1.b", "0/2.c", "1/", "1/0.d", "1/1.e", "1/2.f", "2/", "2/0.g", "2/1.h"],
            ["0/", "0/0.a", "0/1.b", "0/2.c", "1/", "1/0.d", "1/1.e", "1/2.f", "2/", "2/0.g", "2/1.h", "2/2.i"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q", "1/2/2.r"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q", "1/2/2.r", "2/", "2/0/", "2/0/0.s"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q", "1/2/2.r", "2/", "2/0/", "2/0/0.s", "2/0/1.t"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q", "1/2/2.r", "2/", "2/0/", "2/0/0.s", "2/0/1.t", "2/0/2.u"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q", "1/2/2.r", "2/", "2/0/", "2/0/0.s", "2/0/1.t", "2/0/2.u", "2/1/", "2/1/0.v"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q", "1/2/2.r", "2/", "2/0/", "2/0/0.s", "2/0/1.t", "2/0/2.u", "2/1/", "2/1/0.v", "2/1/1.w"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q", "1/2/2.r", "2/", "2/0/", "2/0/0.s", "2/0/1.t", "2/0/2.u", "2/1/", "2/1/0.v", "2/1/1.w", "2/1/2.x"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q", "1/2/2.r", "2/", "2/0/", "2/0/0.s", "2/0/1.t", "2/0/2.u", "2/1/", "2/1/0.v", "2/1/1.w", "2/1/2.x", "2/2/", "2/2/0.y"],
            ["0/", "0/0/", "0/0/0.a", "0/0/1.b", "0/0/2.c", "0/1/", "0/1/0.d", "0/1/1.e", "0/1/2.f", "0/2/", "0/2/0.g", "0/2/1.h", "0/2/2.i", "1/", "1/0/", "1/0/0.j", "1/0/1.k", "1/0/2.l", "1/1/", "1/1/0.m", "1/1/1.n", "1/1/2.o", "1/2/", "1/2/0.p", "1/2/1.q", "1/2/2.r", "2/", "2/0/", "2/0/0.s", "2/0/1.t", "2/0/2.u", "2/1/", "2/1/0.v", "2/1/1.w", "2/1/2.x", "2/2/", "2/2/0.y", "2/2/1.z"],
        ]

        directory = tempfile.mkdtemp()
        working = tempfile.mkdtemp()

        try:
            c = Cache(directory, 1024, maxperdir=3)

            for i in range(26):
                filename = os.path.join(working, "file{:02d}".format(i))
                open(filename, "w").write("hi")

                c.newfile(chr(i + ord("a")), filename)

                self.assertEqual(expected[i], list(lstree(directory)))

            c2 = Cache.adopt(directory, 1024, maxperdir=3)
            self.assertEqual(c.lookup, c2.lookup)
            self.assertEqual(c.numbytes, c2.numbytes)
            self.assertEqual(c.depth, c2.depth)
            self.assertEqual(c.number, c2.number)

        finally:
            shutil.rmtree(directory)
            shutil.rmtree(working)
