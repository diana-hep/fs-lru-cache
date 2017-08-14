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

import json
import math
import os
import re
import shutil

class Cache(object):
    CONFIG_DIR = "config"
    USER_DIR = re.compile("^user-[0-9]+$")

    def __init__(self, *args, **kwds):
        raise TypeError("use Cache.overwrite or Cache.adopt to create a Cache")
        
    def _init(self, directory, limitbytes, maxperdir=1000, delimiter="."):
        self.directory = directory
        self.limitbytes = limitbytes
        self.maxperdir = maxperdir
        self.delimiter = delimiter
        self._formatter = "{0:0" + str(int(math.ceil(math.log(maxperdir, 10)))) + "d}"

        self.lookup = {}
        self.numbytes = 0
        self.depth = 0
        self.number = 0

        self.users = 0
        
    @staticmethod
    def overwrite(directory, limitbytes, maxperdir=1000, delimiter="."):
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.mkdir(directory)
        os.mkdir(os.path.join(directory, Cache.CONFIG_DIR))

        out = Cache.__new__(Cache)
        out._init(directory, limitbytes, maxperdir, delimiter)
        return out

    @staticmethod
    def adopt(directory, limitbytes, maxperdir=1000, delimiter="."):
        if not os.path.exists(directory):
            os.mkdir(directory)
            os.mkdir(os.path.join(directory, Cache.CONFIG_DIR))

        if not os.path.isdir(directory):
            raise IOError("path {0} is not a directory".format(directory))

        out = Cache.__new__(Cache)
        out._init(directory, limitbytes, maxperdir, delimiter)
        out.depth = None
        out.number = None

        # clear out old user working directories
        for item in os.listdir(directory):
            if Cache.USER_DIR.match(item) is not None:
                shutil.rmtree(os.path.join(directory, item))

        if not os.path.exists(os.path.join(directory, Cache.CONFIG_DIR)):
            raise IOError("cache directory {0} does not contain a \"config\" subdirectory".format(directory))

        digits = re.compile("^[0-9]{" + str(int(math.ceil(math.log(maxperdir, 10)))) + "}$")
        def recurse(d, n, path):
            items = os.listdir(os.path.join(directory, path))
            items.sort()

            # directories should all have numerical names (with the right number of digits)
            if all(os.path.isdir(os.path.join(directory, path, fn)) and digits.match(fn) for fn in items if fn != Cache.CONFIG_DIR):
                for fn in items:
                    if fn != Cache.CONFIG_DIR:
                        recurse(d + 1, (n + int(fn)) * maxperdir, os.path.join(path, fn))

            # a directory of files should all be files; no mixing of files and directories
            elif all(not os.path.isdir(os.path.join(directory, path, fn)) for fn in items if fn != Cache.CONFIG_DIR):
                for fn in items:
                    if fn != Cache.CONFIG_DIR:
                        if delimiter not in fn:
                            raise IOError("file names in {0} are missing delimiter \"{1}\"".format(os.path.join(directory, path), delimiter))
                        i = fn.index(delimiter)
                        name = fn[i + 1:]
                        number = n + int(fn[:i])

                        out.lookup[name] = os.path.join(path, fn)
                        out.numbytes += os.path.getsize(os.path.join(directory, path, fn))

                        if out.depth is None:
                            out.depth = d
                        elif out.depth != d:
                            raise IOError("some files are at depth {0}, others at {1}".format(out.depth, d))

                        if out.number is not None and number <= out.number:
                            raise IOError("cache numbers are not in increasing order")
                        out.number = number

            else:
                raise IOError("directory contents must all be directories (named /{0}/ because maxperdir is {1}) or all be files; failure at {2}".format(digits.pattern, maxperdir, os.path.join(directory, path)))

        recurse(0, 0, "")
        if out.depth is None and out.number is None:
            out.depth = 0
            out.number = 0
        else:
            out.number += 1

        return out

    def clear(self, prefix):
        def recurse(path, item):
            fullpath = os.path.join(path, item)
            if os.path.isdir(fullpath):
                for subitem in os.listdir(fullpath):
                    recurse(fullpath, subitem)
            else:
                name = item[item.index(self.delimiter) + 1:]
                if name.startswith(prefix):
                    del self.lookup[name]
                    os.remove(fullpath)

        for item in os.listdir(self.directory):
            if item != Cache.CONFIG_DIR and Cache.USER_DIR.match(item) is None:
                recurse(self.directory, item)

        if os.path.exists(os.path.join(self.directory, Cache.CONFIG_DIR, prefix)):
            os.remove(os.path.join(self.directory, Cache.CONFIG_DIR, prefix))

    def newuser(self, config):
        for prefix, mnemonic in config.items():
            configfile = os.path.join(self.directory, Cache.CONFIG_DIR, prefix)
            if os.path.exists(configfile):
                if json.load(open(configfile, "r")) != mnemonic:
                    raise ValueError("the meaning of prefix \"{0}\" (in {1}) has changed; explicitly clear it before use".format(prefix, self.directory))
            else:
                json.dump(mnemonic, open(configfile, "w"))

        dirname = os.path.join(self.directory, "user-{0}".format(self.users))
        os.mkdir(dirname)
        self.users += 1
        return dirname

    def newfile(self, name, oldfilename):
        newbytes = os.path.getsize(oldfilename)

        if self.limitbytes is not None:
            bytestofree = self.numbytes + newbytes - self.limitbytes
            if bytestofree > 0:
                self._evict(bytestofree, self.directory)

        newfilename = self._newfilename(name)
        os.rename(oldfilename, os.path.join(self.directory, newfilename))

        self.lookup[name] = newfilename
        self.numbytes += newbytes

    def has(self, name):
        return name in self.lookup

    def get(self, name):
        return self.lookup[name]

    def getfile(self, name):
        return os.path.join(self.directory, self.lookup[name])

    def maybe(self, name):
        return self.lookup.get(name, None)

    def maybefile(self, name):
        if self.has(name):
            return os.path.join(self.directory, self.lookup.get(name, None))
        else:
            return None

    def touch(self, *names):
        cleanup = set()
        for name in names:
            newname = self._newfilename(name)   # _newfilename changes self.lookup
            oldname = self.lookup[name]         # and therefore must be called first

            os.rename(os.path.join(self.directory, oldname), os.path.join(self.directory, newname))
            self.lookup[name] = newname

            cleanup.add(oldname)
            
        # clean up empty directories
        for oldname in cleanup:
            path, fn = os.path.split(oldname)
            while path != "":
                olddir = os.path.join(self.directory, path)
                if os.path.exists(olddir) and len(os.listdir(olddir)) == 0:
                    os.rmdir(olddir)
                path, fn = os.path.split(path)

    def linkfile(self, name, tofilename):
        os.link(os.path.join(self.directory, self.get(name)), tofilename)

    def _evict(self, bytestofree, path):
        # eliminate in sort order
        items = os.listdir(path)
        items.sort()

        for fn in items:
            subpath = os.path.join(path, fn)

            if os.path.isdir(subpath):
                # descend down to the file level
                bytestofree = self._evict(bytestofree, subpath)
            else:
                # delete each file
                numbytes = os.path.getsize(subpath)
                os.remove(subpath)
                bytestofree -= numbytes
                self.numbytes -= numbytes

            # until we're under budget
            if bytestofree <= 0:
                return 0

        # clean up empty directories
        if len(os.listdir(path)) == 0:
            os.rmdir(path)

        return bytestofree
        
    def _newfilename(self, name):
        # increase number
        number = self.number
        self.number += 1

        # maybe increase depth
        while number >= self.maxperdir**(self.depth + 1):
            self.depth += 1

            # move the subdirectories/files into a new directory ("tmp", then prefix)
            tmp = os.path.join(self.directory, "tmp")
            os.mkdir(tmp)
            for fn in os.listdir(self.directory):
                if fn != "tmp" and fn != Cache.CONFIG_DIR and Cache.USER_DIR.match(fn) is None:
                    os.rename(os.path.join(self.directory, fn), os.path.join(tmp, fn))

            prefix = self._formatter.format(0)
            os.rename(tmp, os.path.join(self.directory, prefix))

            # also update the lookup map
            for n, filename in self.lookup.items():
                self.lookup[n] = os.path.join(prefix, filename)

        # create directories in path if necessary
        path = ""
        for d in range(self.depth, 0, -1):
            factor = self.maxperdir**d

            fn = self._formatter.format(number // factor)
            number = number % factor

            path = os.path.join(path, fn)
            if not os.path.exists(os.path.join(self.directory, path)):
                os.mkdir(os.path.join(self.directory, path))

        # return new filename
        fn = self._formatter.format(number)
        return os.path.join(path, fn + self.delimiter + str(name))
