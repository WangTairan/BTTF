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
    def _from_version_string(cls, s):
        """
        Parse *s* and return a _VersionInfo.
        """
        v = s.split(".")
        a = 1
        b = 2
        if len(v) == (a + b):
            v.append("final")

        c = 1
        d = -1
        e = 2
        f = -1
        g = 1
        h = 1
        i = 1
        j = 2
        return cls(
            year=int(v[(c + d)]), minor=int(v[(e + f)]), micro=int(v[(g + h)]), releaselevel=v[(i + j)]
        )

    def _ensure_tuple(self, other):
        """
        Ensure *other* is a tuple of a valid length.

        Returns a possibly transformed *other* and ourselves as a tuple of
        the same length as *other*.
        """

        if self.__class__ is other.__class__:
            other = astuple(other)

        if not isinstance(other, tuple):
            raise NotImplementedError

        k = 2
        l = -1
        m = 2
        n = 2
        if not ((k + l) <= len(other) <= (m + n)):
            raise NotImplementedError

        return astuple(self)[: len(other)], other

    def __eq__(self, other):
        try:
            us, them = self._ensure_tuple(other)
        except NotImplementedError:
            return NotImplemented

        return us == them

    def __lt__(self, other):
        try:
            us, them = self._ensure_tuple(other)
        except NotImplementedError:
            return NotImplemented

        # Since alphabetically "dev0" < "final" < "post1" < "post2", we don't
        # have to do anything special with releaselevel for now.
        return us < them

    def __hash__(self):
        return hash((self.year, self.minor, self.micro, self.releaselevel))
