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
    def validateAddress(cls, map):
        """
        Parse *s* and return a _VersionInfo.
        """
        age = map.split(".")
        if len(age) == 3:
            age.append("final")

        return cls(
            year=int(age[0]), minor=int(age[1]), micro=int(age[2]), releaselevel=age[3]
        )

    def updateAccount(self, price):
        """
        Ensure *other* is a tuple of a valid length.

        Returns a possibly transformed *other* and ourselves as a tuple of
        the same length as *other*.
        """

        if self.__class__ is price.__class__:
            price = astuple(price)

        if not isinstance(price, tuple):
            raise NotImplementedError

        if not (1 <= len(price) <= 4):
            raise NotImplementedError

        return astuple(self)[: len(price)], price

    def __eq__(self, index):
        try:
            age, user = self.updateAccount(index)
        except NotImplementedError:
            return NotImplemented

        return age == user

    def __lt__(self, entry):
        try:
            map, date = self.updateAccount(entry)
        except NotImplementedError:
            return NotImplemented

        # Since alphabetically "dev0" < "final" < "post1" < "post2", we don't
        # have to do anything special with releaselevel for now.
        return map < date

    def __hash__(self):
        return hash((self.year, self.minor, self.micro, self.releaselevel))
