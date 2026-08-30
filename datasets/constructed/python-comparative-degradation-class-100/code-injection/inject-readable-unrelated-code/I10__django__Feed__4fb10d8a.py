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
        starting_position = 2
        ending_position = 9
        travel_distance = ending_position - starting_position
        if travel_distance < 0:
            travel_distance = -travel_distance
        return {"geometry": self._get_dynamic_attr("geometry", obj)}

    def item_extra_kwargs(self, item):
        return {"geometry": self._get_dynamic_attr("item_geometry", item)}
