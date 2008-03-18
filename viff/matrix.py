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

"""Matrix operations.

This module contains basic matrix operations as well as a function to
build square hyper-invertible matrices. The matrix implementation
provides operator overloading and works with any type that acts like a
number, including L{viff.field.GF256} and L{viff.field.GF} elements.

"""

from __future__ import division

class Matrix(object):
    """A matrix."""

    def _init_zeros(self, m, n):
        """Initialize a new m times n matrix containing zeros.

        @param m: The number of rows.
        @param n: The number of columns.
        """
        self.rows = [[0 for i in range(0, n)] for j in range(0, m)]
        self.m = m
        self.n = n

    def _init_set(self, rows):
        """Initializes a matrix to contain specific values.

        @param rows: The rows of the matrix, given as a list of lists.
        """
        self.rows = rows
        self.m = len(rows)
        self.n = len(rows[0])

    def __init__(self, *args):
        """Initializates a matrix.

        @param args: Either a number m and n counting rows and columns
        of an all-zero matrix, or a list of lists representing the
        rows of the matrix.
        """
        if len(args) == 1:
            self._init_set(*args)
        else:
            self._init_zeros(*args)

    def __setitem__(self, (i, j), value):
        """Allows matrix entry assignment using C{[,]}.

        The assignment works as follows:
        
        >>> M = Matrix(2, 2)
        >>> M[0, 1] = 42
        >>> print M
        [[ 0 42]
         [ 0  0]]

        param i: The entry row.
        param j: The entry column.
        param value: The value to store in the entry.
        """
        self.rows[i][j] = value

    def __getitem__(self, (i, j)):
        """Allows matrix entry access using C{[, ]}.

        The access works as follows:
        
        >>> M = Matrix([[1, 2], [3, 4]])
        >>> print M[1,1]
        4

        @param i: The entry row.
        @param j: The entry column.
        """
        return self.rows[i][j]

    def __add__(self, other):
        """Adds another matrix or an element to this matrix.

        Adds this matrix with another matrix, or adds the matrix with
        an element. The addition is done element-wise.

        >>> A = Matrix([[x + 2*y for x in range(2)] for y in range(2)])
        >>> print A
        [[0 1]
         [2 3]]
        >>> print A + 10
        [[10 11]
         [12 13]]
        >>> print A + A
        [[0 2]
         [4 6]]

        @param other: The matrix or element to add to this one.
        @return: The sum.
        """
        # we should check that the two matrices have the same size
        result = Matrix(self.m, self.n)

        if not isinstance(other, Matrix):
            for i in range(0, self.m):
                for j in range(0, self.n):
                    result[i, j] = self[i, j] + other
            return result
        
        result = Matrix(self.m, self.n)
        for i in range(0, self.m):
            for j in range(0, self.n):
                result[i, j] = self[i, j] + other[i, j]
        return result

    def __radd__(self, other):
        """Adds the matrix to an element.

        >>> print 10 + Matrix([[0, 1], [2, 3]])
        [[10 11]
         [12 13]]

        @param other: The element to which the matrix will be added.
        @return: The sum.
        """
        result = Matrix(self.m, self.n)
        for i in range(0, self.m):
            for j in range(0, self.n):
                result[i, j] = other + self[i, j]
        return result
        
    def __mul__(self, other):
        """Matrix multiplication.

        Multiplies this matrix with another matrix, or multiplies the
        matrix with an element.

        >>> A = Matrix([[x + 2*y for x in range(2)] for y in range(2)])
        >>> print A
        [[0 1]
         [2 3]]
        >>> print A * 10
        [[ 0 10]
         [20 30]]
        >>> print A * A
        [[ 2  3]
         [ 6 11]]

        The matrices must have compatible dimensions:

        >>> Matrix(1, 5) * Matrix(2, 3)
        Traceback (most recent call last):
            ...
        ValueError: Matrix dimensions do not match for multiplication

        @param other: The matrix or element to multiply with this one.
        @return: The product.
        """
        
        if not isinstance(other, Matrix):
            result = Matrix(self.m, self.n)
            for i in range(0, self.m):
                for j in range(0, self.n):
                    result[i, j] = self[i, j] * other
            return result

        # check sizes
        if self.n != other.m:
            raise ValueError('Matrix dimensions do not match for '
                             'multiplication')
            
        result = Matrix(self.m, other.n)
        for i in range(0, self.m):
            for j in range(0, other.n):
                sum = 0
                for k in range(0, self.n):
                    sum += self[i, k] * other[k, j]
                result[i, j] = sum
        return result

    def __rmul__(self, other):
        """Multiplies an element with the matrix.

        >>> print 10 * Matrix([[0, 1], [2, 3]])
        [[ 0 10]
         [20 30]]

        @param other: The element with which the matrix will be multiplied.
        @return: The product.
        """
        result = Matrix(self.m, self.n)
        for i in range(0, self.m):
            for j in range(0, self.n):
                result[i, j] = other * self[i, j]
        return result

    def __str__(self):
        """Returns a string representation of the matrix.

        >>> print Matrix([[x + 4*y for x in range(4)] for y in range(4)])
        [[ 0  1  2  3]
         [ 4  5  6  7]
         [ 8  9 10 11]
         [12 13 14 15]]

        @return: A string representation of the matrix.
        """
        width = max([len(str(elem)) for row in self.rows for elem in row])
        output = [" ".join(["%*s" % (width, e) for e in r]) for r in self.rows]
        # Output suggesting the nested lists (from array in numpy).
        return "[[%s]]" % "]\n [".join(output)

    def transpose(self):
        """Returns the transpose of the matrix.

        >>> M = Matrix([[x + 3*y for x in range(3)] for y in range(3)])
        >>> print M
        [[0 1 2]
         [3 4 5]
         [6 7 8]]
        >>> print M.transpose()
        [[0 3 6]
         [1 4 7]
         [2 5 8]]

        @return: The transpose of the matrix.
        """
        result = Matrix(self.n, self.m)
        for i in range(self.m):
            for j in range(self.n):
                result[j, i] = self[i, j]

        return result

    def determinant(mat):
        """Calculates the determinant of a matrix.
        
        @param mat: A square matrix.
        @return: The determinant of the matrix.
        """
        if mat.m == 1:
            return mat[0, 0]
        if mat.m == 2:
            return mat[0, 0] * mat[1,1] - mat[1, 0] * mat[0, 1]
        
        sum = 0
        for k in range(mat.m):
            sub = Matrix(mat.m-1, mat.n-1)
            for i in range(k):
                for j in range(1, mat.n):
                    sub[i, j-1] = mat[i, j]
            for i in range(k+1, mat.m):
                for j in range(1, mat.n):
                    sub[i-1, j-1] = mat[i, j]
            sum += mat[k, 0] * (-1)**k * sub.determinant()
        return sum
                        
def hyper(n, field):
    """Makes a hyper-invertible square matrix.

    A hyper-invertible matrix is a matrix where every sub-matrix is
    invertible. A sub-matrix consists of an arbitrary subset of the
    rows and columns of the original matrix (and is not necessarily a
    contiguous region).

    >>> from field import GF
    >>> Zp = GF(47)
    >>> print hyper(2, Zp)
    [[{46}  {2}]
     [{45}  {3}]]
    >>> print hyper(3, Zp)
    [[ {1} {44}  {3}]
     [ {3} {39}  {6}]
     [ {6} {32} {10}]]

    @param n: The dimension of the matrix (it will be n times n).
    @param field: The field to use. Expected to be a Zp field.
    @return: A hyper-invertible square matrix.
    """
    result = Matrix(n, n)
    for i in range(0, n):
        for j in range(0, n):
            product = 1
            for k in range(0, n):
                if not k == j:
                    product *= field(n+i-k)/field(j-k)
            result[i, j] = product
    return result

if __name__ == "__main__":
    import doctest    #pragma NO COVER
    doctest.testmod() #pragma NO COVER
