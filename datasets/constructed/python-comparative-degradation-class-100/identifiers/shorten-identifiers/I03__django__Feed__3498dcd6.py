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

    def feed(self, obj2):
        return {"geometry": self._get_dynamic_attr("geometry", obj2)}

    def item2(self, ite):
        return {"geometry": self._get_dynamic_attr("item_geometry", ite)}
