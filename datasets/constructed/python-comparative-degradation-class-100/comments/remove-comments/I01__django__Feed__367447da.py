from django.contrib.syndication.views import Feed as BaseFeed
from django.utils.feedgenerator import Atom1Feed, Rss201rev2Feed

class Feed(BaseFeed):
    

    feed_type = GeoRSSFeed

    def feed_extra_kwargs(self, obj):
        return {"geometry": self._get_dynamic_attr("geometry", obj)}

    def item_extra_kwargs(self, item):
        return {"geometry": self._get_dynamic_attr("item_geometry", item)}
