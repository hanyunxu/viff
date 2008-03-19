# Copyright 2008 VIFF Development Team.
#
# This file is part of VIFF, the Virtual Ideal Functionality Framework.
#
# VIFF is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# VIFF is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with VIFF in the file COPYING; if not, write to the Free
# Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301 USA

"""Tests of comparison protocols."""

import operator

from viff.runtime import Runtime
from viff.test.util import RuntimeTestCase, BinaryOperatorTestCase

class GreaterThanTest(BinaryOperatorTestCase, RuntimeTestCase):
    operator = operator.gt

class GreaterThanEqualTest(BinaryOperatorTestCase, RuntimeTestCase):
    operator = operator.ge

class LessThanTest(BinaryOperatorTestCase, RuntimeTestCase):
    operator = operator.lt

class LessThanEqualTest(BinaryOperatorTestCase, RuntimeTestCase):
    operator = operator.le

class GreaterThanEqualIITest(BinaryOperatorTestCase, RuntimeTestCase):
    def operator(self, x, y):
        # TODO: This method can be replaced with operator.ge when we
        # have split the Runtime into smaller parts as described in
        # Issue 2.
        runtime = getattr(x, "runtime", getattr(y, "runtime", None))
        if runtime is not None:
            return runtime.greater_than_equalII(x, y)
        else:
            return x >= y
