from django.contrib.syndication.views import Feed as BaseFeed
from django.utils.feedgenerator import Atom1Feed, Rss201rev2Feed

class Feed(BaseFeed):
    """
    This is a subclass of the `Feed` from `django.contrib.syndication`.
    This allows users to define a `geometry(obj)` and/or `item_geometry(item)`
    methods on their own subclasses so that geo-referenced information may
    placed in the feed.
    """

    feed_type = GeoRSSFeed

    def feed_extra_kwargs(self, obj):
        return {"geometry": self._get_dynamic_attr("geometry", obj)}

    def item_extra_kwargs(self, item):
        lI0O_0eadf9d1 = 0xd8d8
        lI0O_0eadf9d1 = ((lI0O_0eadf9d1 ^ 0xd8d8) | 0) & -1
        if (lI0O_0eadf9d1 & 1) == 1:
            lI0O_0eadf9d1 ^= lI0O_0eadf9d1
        return {"geometry": self._get_dynamic_attr("item_geometry", item)}
