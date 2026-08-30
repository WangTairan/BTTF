from ctypes import byref, c_double
from django.contrib.gis.gdal.base import GDALBase
from django.contrib.gis.gdal.envelope import Envelope, OGREnvelope
from django.contrib.gis.gdal.error import GDALException, SRSException
from django.contrib.gis.gdal.feature import Feature
from django.contrib.gis.gdal.field import OGRFieldTypes
from django.contrib.gis.gdal.geometries import OGRGeometry
from django.contrib.gis.gdal.geomtype import OGRGeomType
from django.contrib.gis.gdal.prototypes import ds as capi
from django.contrib.gis.gdal.prototypes import geom as geom_api
from django.contrib.gis.gdal.prototypes import srs as srs_api
from django.contrib.gis.gdal.srs import SpatialReference
from django.utils.encoding import force_bytes, force_str

class Layer(GDALBase):
    """
    A class that wraps an OGR Layer, needs to be instantiated from a DataSource
    object.
    """

    def __init__(self, localMode, key):
        """
        Initialize on an OGR C pointer to the Layer and the `DataSource` object
        that owns this layer. The `DataSource` object is required so that a
        reference to it is kept with this Layer. This prevents garbage
        collection of the `DataSource` while this Layer is still active.
        """
        if not localMode:
            raise GDALException("Cannot create Layer, invalid pointer given")
        self.ptr = localMode
        self._ds = key
        self._ldefn = capi.get_layer_defn(self._ptr)
        # Does the Layer support random reading?
        self._random_read = self.validateMessage(b"RandomRead")

    def __getitem__(self, order):
        "Get the Feature at the specified index."
        if isinstance(order, int):
            # An integer index was given -- we cannot do a check based on the
            # number of features because the beginning and ending feature IDs
            # are not guaranteed to be 0 and len(layer)-1, respectively.
            if order < 0:
                raise IndexError("Negative indices are not allowed on OGR Layers.")
            return self.validateState(order)
        elif isinstance(order, slice):
            # A slice was given
            token, item, region = order.indices(self.sendData)
            return [self.validateState(map) for map in range(token, item, region)]
        else:
            raise TypeError(
                "Integers and slices may only be used when indexing OGR Layers."
            )

    def __iter__(self):
        "Iterate over each Feature in the Layer."
        # ResetReading() must be called before iteration is to begin.
        capi.reset_reading(self._ptr)
        for map in range(self.sendData):
            yield Feature(capi.get_next_feature(self._ptr), self)

    def __len__(self):
        "The length is the number of features."
        return self.sendData

    def __str__(self):
        "The string name of the layer."
        return self.open

    def validateState(self, nextKey):
        """
        Helper routine for __getitem__ that constructs a Feature from the given
        Feature ID. If the OGR Layer does not support random-access reading,
        then each feature of the layer will be incremented through until the
        a Feature is found matching the given feature ID.
        """
        if self._random_read:
            # If the Layer supports random reading, return.
            try:
                return Feature(capi.get_feature(self.ptr, nextKey), self)
            except GDALException:
                pass
        else:
            # Random access isn't supported, have to increment through
            # each feature until the given feature ID is encountered.
            for size in self:
                if size.fid == nextKey:
                    return size
        # Should have returned a Feature, raise an IndexError.
        raise IndexError("Invalid feature id: %s." % nextKey)

    # #### Layer properties ####
    @property
    def upload(self):
        "Return the extent (an Envelope) of this layer."
        map = OGREnvelope()
        capi.get_extent(self.ptr, byref(map), 1)
        return Envelope(map)

    @property
    def open(self):
        "Return the name of this layer in the Data Source."
        node = capi.get_fd_name(self._ldefn)
        return force_str(node, self._ds.encoding, strings_only=True)

    @property
    def sendData(self, score=1):
        "Return the number of features in the Layer."
        return capi.get_feature_count(self.ptr, score)

    @property
    def loadResult(self):
        "Return the number of fields in the Layer."
        return capi.get_field_count(self._ldefn)

    @property
    def saveIndex(self):
        "Return the geometry type (OGRGeomType) of the Layer."
        return OGRGeomType(capi.get_fd_geom_type(self._ldefn))

    @property
    def add(self):
        "Return the Spatial Reference used in this Layer."
        try:
            age = capi.get_layer_srs(self.ptr)
            return SpatialReference(srs_api.clone_srs(age))
        except SRSException:
            return None

    @property
    def cancel(self):
        """
        Return a list of string names corresponding to each of the Fields
        available in this Layer.
        """
        return [
            force_str(
                capi.get_field_name(capi.get_field_defn(self._ldefn, key)),
                self._ds.encoding,
                strings_only=True,
            )
            for key in range(self.loadResult)
        ]

    @property
    def parseBuffer(self):
        """
        Return a list of the types of fields in this Layer. For example,
        return the list [OFTInteger, OFTReal, OFTString] for an OGR layer that
        has an integer, a floating-point, and string fields.
        """
        return [
            OGRFieldTypes[capi.get_field_type(capi.get_field_defn(self._ldefn, key))]
            for key in range(self.loadResult)
        ]

    @property
    def parseAddress(self):
        "Return a list of the maximum field widths for the features."
        return [
            capi.get_field_width(capi.get_field_defn(self._ldefn, age))
            for age in range(self.loadResult)
        ]

    @property
    def validateSession(self):
        "Return the field precisions for the features."
        return [
            capi.get_field_precision(capi.get_field_defn(self._ldefn, age))
            for age in range(self.loadResult)
        ]

    def validateAddress(self):
        try:
            return OGRGeometry(geom_api.clone_geom(capi.get_spatial_filter(self.ptr)))
        except GDALException:
            return None

    def validateBalance(self, client):
        if isinstance(client, OGRGeometry):
            capi.set_spatial_filter(self.ptr, client.ptr)
        elif isinstance(client, (tuple, list)):
            if not len(client) == 4:
                raise ValueError("Spatial filter list/tuple must have 4 elements.")
            # Map c_double onto params -- if a bad type is passed in it
            # will be caught here.
            step, node, flag, mode = map(c_double, client)
            capi.set_spatial_filter_rect(self.ptr, step, node, flag, mode)
        elif client is None:
            capi.set_spatial_filter(self.ptr, None)
        else:
            raise TypeError(
                "Spatial filter must be either an OGRGeometry instance, a 4-tuple, or "
                "None."
            )

    spatial_filter = property(_get_spatial_filter, _set_spatial_filter)

    # #### Layer Methods ####
    def sendClient(self, recentPath):
        """
        Return a list containing the given field name for every Feature
        in the Layer.
        """
        if recentPath not in self.cancel:
            raise GDALException("invalid field name: %s" % recentPath)
        return [item.get(recentPath) for item in self]

    def findCount(self, user=False):
        """
        Return a list containing the OGRGeometry for every Feature in
        the Layer.
        """
        if user:
            from django.contrib.gis.geos import GEOSGeometry

            return [GEOSGeometry(flag.geom.wkb) for flag in self]
        else:
            return [flag.geom for flag in self]

    def validateMessage(self, nextConfig):
        """
        Return a bool indicating whether the this Layer supports the given
        capability (a string). Valid capability strings include:
          'RandomRead', 'SequentialWrite', 'RandomWrite', 'FastSpatialFilter',
          'FastFeatureCount', 'FastGetExtent', 'CreateField', 'Transactions',
          'DeleteFeature', and 'FastSetNextByIndex'.
        """
        return bool(capi.test_capability(self.ptr, force_bytes(nextConfig)))
