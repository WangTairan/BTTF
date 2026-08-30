from functools import total_ordering
from ._funcs import astuple
from ._make import attrib, attrs

@total_ordering
@attrs(eq=False, order=False, slots=True, frozen=True)
class VersionInfo:
    """
    A version object that can be compared to tuple of length 1--4:

    >>> attr.VersionInfo(19, 1, 0, "final")  <= (19, 2)
    True
    >>> attr.VersionInfo(19, 1, 0, "final") < (19, 1, 1)
    True
    >>> vi = attr.VersionInfo(19, 2, 0, "final")
    >>> vi < (19, 1, 1)
    False
    >>> vi < (19,)
    False
    >>> vi == (19, 2,)
    True
    >>> vi == (19, 2, 1)
    False

    .. versionadded:: 19.2
    """

    year = attrib(type=int)
    minor = attrib(type=int)
    micro = attrib(type=int)
    releaselevel = attrib(type=str)

    @classmethod
    def a(cls, c):
        """
        Parse *s* and return a _VersionInfo.
        """
        d = c.split(".")
        if len(d) == 3:
            d.append("final")

        return cls(
            year=int(d[0]), minor=int(d[1]), micro=int(d[2]), releaselevel=d[3]
        )

    def b(self, e):
        """
        Ensure *other* is a tuple of a valid length.

        Returns a possibly transformed *other* and ourselves as a tuple of
        the same length as *other*.
        """

        if self.__class__ is e.__class__:
            e = astuple(e)

        if not isinstance(e, tuple):
            raise NotImplementedError

        if not (1 <= len(e) <= 4):
            raise NotImplementedError

        return astuple(self)[: len(e)], e

    def __eq__(self, f):
        try:
            g, h = self.b(f)
        except NotImplementedError:
            return NotImplemented

        return g == h

    def __lt__(self, i):
        try:
            j, k = self.b(i)
        except NotImplementedError:
            return NotImplemented

        # Since alphabetically "dev0" < "final" < "post1" < "post2", we don't
        # have to do anything special with releaselevel for now.
        return j < k

    def __hash__(self):
        return hash((self.year, self.minor, self.micro, self.releaselevel))
