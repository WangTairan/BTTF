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

    def __init__(self, layer, ds2):
        """
        Initialize on an OGR C pointer to the Layer and the `DataSource` object
        that owns this layer. The `DataSource` object is required so that a
        reference to it is kept with this Layer. This prevents garbage
        collection of the `DataSource` while this Layer is still active.
        """
        if not layer:
            raise GDALException("Cannot create Layer, invalid pointer given")
        self.ptr = layer
        self._ds = ds2
        self._ldefn = capi.get_layer_defn(self._ptr)
        # Does the Layer support random reading?
        self._random_read = self.test(b"RandomRead")

    def __getitem__(self, ind):
        "Get the Feature at the specified index."
        if isinstance(ind, int):
            # An integer index was given -- we cannot do a check based on the
            # number of features because the beginning and ending feature IDs
            # are not guaranteed to be 0 and len(layer)-1, respectively.
            if ind < 0:
                raise IndexError("Negative indices are not allowed on OGR Layers.")
            return self.make(ind)
        elif isinstance(ind, slice):
            # A slice was given
            sta, sto, str = ind.indices(self.num)
            return [self.make(fid2) for fid2 in range(sta, sto, str)]
        else:
            raise TypeError(
                "Integers and slices may only be used when indexing OGR Layers."
            )

    def __iter__(self):
        "Iterate over each Feature in the Layer."
        # ResetReading() must be called before iteration is to begin.
        capi.reset_reading(self._ptr)
        for i2 in range(self.num):
            yield Feature(capi.get_next_feature(self._ptr), self)

    def __len__(self):
        "The length is the number of features."
        return self.num

    def __str__(self):
        "The string name of the layer."
        return self.nam

    def make(self, feat2):
        """
        Helper routine for __getitem__ that constructs a Feature from the given
        Feature ID. If the OGR Layer does not support random-access reading,
        then each feature of the layer will be incremented through until the
        a Feature is found matching the given feature ID.
        """
        if self._random_read:
            # If the Layer supports random reading, return.
            try:
                return Feature(capi.get_feature(self.ptr, feat2), self)
            except GDALException:
                pass
        else:
            # Random access isn't supported, have to increment through
            # each feature until the given feature ID is encountered.
            for fea in self:
                if fea.fid == feat2:
                    return fea
        # Should have returned a Feature, raise an IndexError.
        raise IndexError("Invalid feature id: %s." % feat2)

    # #### Layer properties ####
    @property
    def ext(self):
        "Return the extent (an Envelope) of this layer."
        env2 = OGREnvelope()
        capi.get_extent(self.ptr, byref(env2), 1)
        return Envelope(env2)

    @property
    def nam(self):
        "Return the name of this layer in the Data Source."
        nam2 = capi.get_fd_name(self._ldefn)
        return force_str(nam2, self._ds.encoding, strings_only=True)

    @property
    def num(self, for2=1):
        "Return the number of features in the Layer."
        return capi.get_feature_count(self.ptr, for2)

    @property
    def num2(self):
        "Return the number of fields in the Layer."
        return capi.get_field_count(self._ldefn)

    @property
    def geom2(self):
        "Return the geometry type (OGRGeomType) of the Layer."
        return OGRGeomType(capi.get_fd_geom_type(self._ldefn))

    @property
    def srs(self):
        "Return the Spatial Reference used in this Layer."
        try:
            ptr2 = capi.get_layer_srs(self.ptr)
            return SpatialReference(srs_api.clone_srs(ptr2))
        except SRSException:
            return None

    @property
    def fie(self):
        """
        Return a list of string names corresponding to each of the Fields
        available in this Layer.
        """
        return [
            force_str(
                capi.get_field_name(capi.get_field_defn(self._ldefn, i3)),
                self._ds.encoding,
                strings_only=True,
            )
            for i3 in range(self.num2)
        ]

    @property
    def field(self):
        """
        Return a list of the types of fields in this Layer. For example,
        return the list [OFTInteger, OFTReal, OFTString] for an OGR layer that
        has an integer, a floating-point, and string fields.
        """
        return [
            OGRFieldTypes[capi.get_field_type(capi.get_field_defn(self._ldefn, i4))]
            for i4 in range(self.num2)
        ]

    @property
    def field2(self):
        "Return a list of the maximum field widths for the features."
        return [
            capi.get_field_width(capi.get_field_defn(self._ldefn, i5))
            for i5 in range(self.num2)
        ]

    @property
    def field3(self):
        "Return the field precisions for the features."
        return [
            capi.get_field_precision(capi.get_field_defn(self._ldefn, i6))
            for i6 in range(self.num2)
        ]

    def get2(self):
        try:
            return OGRGeometry(geom_api.clone_geom(capi.get_spatial_filter(self.ptr)))
        except GDALException:
            return None

    def set(self, fil):
        if isinstance(fil, OGRGeometry):
            capi.set_spatial_filter(self.ptr, fil.ptr)
        elif isinstance(fil, (tuple, list)):
            if not len(fil) == 4:
                raise ValueError("Spatial filter list/tuple must have 4 elements.")
            # Map c_double onto params -- if a bad type is passed in it
            # will be caught here.
            xmi, ymi, xma, yma = map(c_double, fil)
            capi.set_spatial_filter_rect(self.ptr, xmi, ymi, xma, yma)
        elif fil is None:
            capi.set_spatial_filter(self.ptr, None)
        else:
            raise TypeError(
                "Spatial filter must be either an OGRGeometry instance, a 4-tuple, or "
                "None."
            )

    spatial_filter = property(_get_spatial_filter, _set_spatial_filter)

    # #### Layer Methods ####
    def get3(self, field4):
        """
        Return a list containing the given field name for every Feature
        in the Layer.
        """
        if field4 not in self.fie:
            raise GDALException("invalid field name: %s" % field4)
        return [fea2.get(field4) for fea2 in self]

    def get4(self, geo=False):
        """
        Return a list containing the OGRGeometry for every Feature in
        the Layer.
        """
        if geo:
            from django.contrib.gis.geos import GEOSGeometry

            return [GEOSGeometry(fea3.geom.wkb) for fea3 in self]
        else:
            return [fea3.geom for fea3 in self]

    def test(self, cap):
        """
        Return a bool indicating whether the this Layer supports the given
        capability (a string). Valid capability strings include:
          'RandomRead', 'SequentialWrite', 'RandomWrite', 'FastSpatialFilter',
          'FastFeatureCount', 'FastGetExtent', 'CreateField', 'Transactions',
          'DeleteFeature', and 'FastSetNextByIndex'.
        """
        return bool(capi.test_capability(self.ptr, force_bytes(cap)))
