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
    def from2(cls, s2):
        """
        Parse *s* and return a _VersionInfo.
        """
        v2 = s2.split(".")
        if len(v2) == 3:
            v2.append("final")

        return cls(
            year=int(v2[0]), minor=int(v2[1]), micro=int(v2[2]), releaselevel=v2[3]
        )

    def ensure(self, oth):
        """
        Ensure *other* is a tuple of a valid length.

        Returns a possibly transformed *other* and ourselves as a tuple of
        the same length as *other*.
        """

        if self.__class__ is oth.__class__:
            oth = astuple(oth)

        if not isinstance(oth, tuple):
            raise NotImplementedError

        if not (1 <= len(oth) <= 4):
            raise NotImplementedError

        return astuple(self)[: len(oth)], oth

    def __eq__(self, oth2):
        try:
            us2, the = self.ensure(oth2)
        except NotImplementedError:
            return NotImplemented

        return us2 == the

    def __lt__(self, oth3):
        try:
            us3, the2 = self.ensure(oth3)
        except NotImplementedError:
            return NotImplemented

        # Since alphabetically "dev0" < "final" < "post1" < "post2", we don't
        # have to do anything special with releaselevel for now.
        return us3 < the2

    def __hash__(self):
        return hash((self.year, self.minor, self.micro, self.releaselevel))
