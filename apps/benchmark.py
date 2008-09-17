#!/usr/bin/python

# Copyright 2007, 2008 VIFF Development Team.
#
# This file is part of VIFF, the Virtual Ideal Functionality Framework.
#
# VIFF is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License (LGPL) as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# VIFF is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with VIFF. If not, see <http://www.gnu.org/licenses/>.

# This example benchmarks multiplications and comparisons. Run it with
# '--help' on the command line to see the available options.
#
# Two lists of shares are created and the numbers are multiplied or
# compared pair-wise. This can be scheduled in two ways: parallel or
# sequentially. Parallel execution looks like this:
#
#      *        *             *
#     / \      / \    ...    / \
#   a1   b1  a2   b2       an   bn
#
# Given sufficient bandwidth and computational power all operations
# should be executed in parallel.
#
# Sequential execution looks like this:
#
#      *
#     / \
#   a1   b1
#
#      *
#     / \
#   a2   b2
#
#     ...
#
#      *
#     / \
#   an   bn
#
# Here the next operation is only started when the previous has
# finished.
#
# In all cases the time reported is measured from the moment when the
# operands are ready until all the results are ready.

import sys
import time
from optparse import OptionParser
import operator
from pprint import pprint

from twisted.internet import reactor

from viff.field import GF, GF256
from viff.runtime import Runtime, create_runtime, gather_shares, \
    make_runtime_class
from viff.active import BasicActiveRuntime, \
    TriplesHyperinvertibleMatricesMixin, TriplesPRSSMixin
from viff.comparison import ComparisonToft05Mixin, ComparisonToft07Mixin
from viff.equality import ProbabilisticEqualityMixin
from viff.paillier import PaillierRuntime
from viff.config import load_config
from viff.util import find_prime

last_timestamp = time.time()
start = 0


def record_start(what):
    global start
    start = time.time()
    print "*" * 64
    print "Started", what


def record_stop(_, what):
    stop = time.time()
    print
    print "Total time used: %.3f sec" % (stop-start)
    print "Time per %s operation: %.0f ms" % (what, 1000*(stop-start) / count)
    print "*" * 6


operations = ["mul", "compToft05", "compToft07", "eq"]

parser = OptionParser()
parser.add_option("-m", "--modulus",
                  help="lower limit for modulus (can be an expression)")
parser.add_option("-a", "--active", action="store_true",
                  help="use actively secure runtime")
parser.add_option("-2", "--twoplayer", action="store_true",
                  help="use twoplayer runtime")
parser.add_option("--prss", action="store_true",
                  help="use PRSS for preprocessing")
parser.add_option("--hyper", action="store_false", dest="prss",
                  help="use hyperinvertible matrices for preprocessing")
parser.add_option("-c", "--count", type="int",
                  help="number of operations")
parser.add_option("-o", "--operation", type="choice", choices=operations,
                  help="operation to benchmark")
parser.add_option("-p", "--parallel", action="store_true",
                  help="execute operations in parallel")
parser.add_option("-s", "--sequential", action="store_false", dest="parallel",
                  help="execute operations in sequence")

parser.set_defaults(modulus="30916444023318367583", count=10,
                    active=False, twoplayer=False, prss=True,
                    operation=operations[0], parallel=True)

# Add standard VIFF options.
Runtime.add_options(parser)

(options, args) = parser.parse_args()

if len(args) == 0:
    parser.error("you must specify a config file")

id, players = load_config(args[0])

Zp = GF(find_prime(options.modulus))
count = options.count
print "I am player %d, will %s %d numbers" % (id, options.operation, count)

# Defining the protocol as a class makes it easier to write the
# callbacks in the order they are called. This class is a base class
# that executes the protocol by calling the run_test method.
class Benchmark:

    def __init__(self, rt, operation):
        self.rt = rt
        self.operation = operation

        if isinstance(self.rt, BasicActiveRuntime):
            # TODO: Make this optional and maybe automatic. The
            # program descriptions below were found by carefully
            # studying the output reported when the benchmarks were
            # run with no preprocessing. So they are quite brittle.
            print "Starting preprocessing"
            if self.operation == operator.mul:
                program_desc = {
                    ("generate_triples", (Zp,)):
                        [(i, 1, 0) for i in range(3 + 2*count, 3 + 3*count)]
                    }
            elif isinstance(self.rt, ComparisonToft05Mixin):
                program_desc = {
                    ("generate_triples", (GF256,)):
                    sum([[(c, 64, i, 1, 1, 0) for i in range(2, 33)] +
                         [(c, 64, i, 3, 1, 0) for i in range(17, 33)]
                         for c in range(3 + 2*count, 3 + 3*count)],
                        [])
                    }
            elif isinstance(self.rt, ComparisonToft07Mixin):
                program_desc = {
                    ("generate_triples", (Zp,)):
                    sum([[(c, 2, 4, i, 2, 1, 0) for i in range(1, 33)] +
                         [(c, 2, 4, 99, 2, 1, 0)] +
                         [(c, 2, 4, i, 1, 0) for i in range(65, 98)]
                         for c in range(3 + 2*count, 3 + 3*count)],
                        [])
                    }

            record_start("preprocessing")
            preproc = rt.preprocess(program_desc)
            preproc.addCallback(record_stop, "preprocessing")
            preproc.addCallback(self.begin)
        else:
            print "Need no preprocessing"
            self.begin(None)

    def begin(self, _):
        print "Runtime ready, starting protocol"
        self.a_shares = [self.rt.prss_share_random(Zp) for _ in range(count)]
        self.b_shares = [self.rt.prss_share_random(Zp) for _ in range(count)]
        shares_ready = gather_shares(self.a_shares + self.b_shares)
        shares_ready.addCallback(self.sync_test)

    def sync_test(self, _):
        print "Synchronizing test start."
        sys.stdout.flush()
        sync = self.rt.synchronize()
        sync.addCallback(self.countdown, 3)

    def countdown(self, _, seconds):
        if seconds > 0:
            print "Starting test in %d" % seconds
            sys.stdout.flush()
            reactor.callLater(1, self.countdown, None, seconds - 1)
        else:
            print "Starting test now"
            sys.stdout.flush()
            self.run_test(None)

    def run_test(self, _):
        raise NotImplemented("Override this abstract method in a sub class.")

    def finished(self, _):
        sys.stdout.flush()

        if self.rt._needed_data:
            print "Missing pre-processed data:"
            pprint(self.rt._needed_data)

        self.rt.shutdown()

# This class implements a benchmark where run_test executes all
# operations in parallel.
class ParallelBenchmark(Benchmark):

    def run_test(self, _):
        c_shares = []
        record_start("parallel test")
        while self.a_shares and self.b_shares:
            a = self.a_shares.pop()
            b = self.b_shares.pop()
            c_shares.append(self.operation(a, b))

        done = gather_shares(c_shares)
        done.addCallback(record_stop, "parallel test")
        done.addCallback(self.finished)

# A benchmark where the operations are executed one after each other.
class SequentialBenchmark(Benchmark):

    def run_test(self, _):
        record_start("sequential test")
        self.single_operation(None)

    def single_operation(self, _):
        if self.a_shares and self.b_shares:
            a = self.a_shares.pop()
            b = self.b_shares.pop()
            c = self.operation(a, b)
            c.addCallback(self.single_operation)
        else:
            record_stop(None, "sequential test")
            self.finished(None)

mixins = []
if options.twoplayer:
    # Then there is just one possible runtime:
    operation = operator.mul
    base_runtime_class = PaillierRuntime
else:
    # There are several options for a multiplayer runtime:
    if options.active:
        base_runtime_class = BasicActiveRuntime
        if options.prss:
            mixins.append(TriplesPRSSMixin)
        else:
            mixins.append(TriplesHyperinvertibleMatricesMixin)
    else:
        base_runtime_class = Runtime

    if options.operation == "mul":
        operation = operator.mul
    elif options.operation == "compToft05":
        operation = operator.ge
        mixins.append(ComparisonToft05Mixin)
    elif options.operation == "compToft07":
        operation = operator.ge
        mixins.append(ComparisonToft07Mixin)
    elif options.operation == "eq":
        operation = operator.eq
        mixins.append(ProbabilisticEqualityMixin)

print "Using the base runtime: %s." % base_runtime_class
print "With the following mixins:"
for mixin in mixins:
    print "- %s" % mixin

runtime_class = make_runtime_class(base_runtime_class, mixins)

if options.parallel:
    benchmark = ParallelBenchmark
else:
    benchmark = SequentialBenchmark

pre_runtime = create_runtime(id, players, max((len(players) -1)//3, 1),
                             options, runtime_class)
pre_runtime.addCallback(benchmark, operation)

print "#### Starting reactor ###"
reactor.run()
