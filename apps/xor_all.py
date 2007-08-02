#!/usr/bin/python

# Copyright 2007 Martin Geisler
#
# This file is part of PySMPC
#
# PySMPC is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PySMPC is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PySMPC in the file COPYING; if not, write to the Free
# Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301 USA

import sys

from pysmpc.field import GF256Element
from pysmpc.runtime import Runtime
from pysmpc.generate_config import load_config

def output(x, format="output: %s"):
    print format % x
    return x

id, players = load_config(sys.argv[1])
input = GF256Element(int(sys.argv[2]))

print "I am player %d and will input %s" % (id, input)

rt = Runtime(players, id, 1)

print "-" * 64
print "Program started"
print

shares = rt.prss_share(input)

while len(shares) > 1:
    a = shares.pop(0)
    b = shares.pop(0)
    shares.append(rt.xor_bit(a,b))

xor = shares[0]

rt.open(xor)

xor.addCallback(output, "result: %s")
    
rt.wait_for(xor)
