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

    def __init__(self, r, s):
        """
        Initialize on an OGR C pointer to the Layer and the `DataSource` object
        that owns this layer. The `DataSource` object is required so that a
        reference to it is kept with this Layer. This prevents garbage
        collection of the `DataSource` while this Layer is still active.
        """
        if not r:
            raise GDALException("Cannot create Layer, invalid pointer given")
        self.ptr = r
        self._ds = s
        self._ldefn = capi.get_layer_defn(self._ptr)
        # Does the Layer support random reading?
        self._random_read = self.q(b"RandomRead")

    def __getitem__(self, t):
        "Get the Feature at the specified index."
        if isinstance(t, int):
            # An integer index was given -- we cannot do a check based on the
            # number of features because the beginning and ending feature IDs
            # are not guaranteed to be 0 and len(layer)-1, respectively.
            if t < 0:
                raise IndexError("Negative indices are not allowed on OGR Layers.")
            return self.a(t)
        elif isinstance(t, slice):
            # A slice was given
            u, v, w = t.indices(self.d)
            return [self.a(x) for x in range(u, v, w)]
        else:
            raise TypeError(
                "Integers and slices may only be used when indexing OGR Layers."
            )

    def __iter__(self):
        "Iterate over each Feature in the Layer."
        # ResetReading() must be called before iteration is to begin.
        capi.reset_reading(self._ptr)
        for y in range(self.d):
            yield Feature(capi.get_next_feature(self._ptr), self)

    def __len__(self):
        "The length is the number of features."
        return self.d

    def __str__(self):
        "The string name of the layer."
        return self.c

    def a(self, z):
        """
        Helper routine for __getitem__ that constructs a Feature from the given
        Feature ID. If the OGR Layer does not support random-access reading,
        then each feature of the layer will be incremented through until the
        a Feature is found matching the given feature ID.
        """
        if self._random_read:
            # If the Layer supports random reading, return.
            try:
                return Feature(capi.get_feature(self.ptr, z), self)
            except GDALException:
                pass
        else:
            # Random access isn't supported, have to increment through
            # each feature until the given feature ID is encountered.
            for A in self:
                if A.fid == z:
                    return A
        # Should have returned a Feature, raise an IndexError.
        raise IndexError("Invalid feature id: %s." % z)

    # #### Layer properties ####
    @property
    def b(self):
        "Return the extent (an Envelope) of this layer."
        B = OGREnvelope()
        capi.get_extent(self.ptr, byref(B), 1)
        return Envelope(B)

    @property
    def c(self):
        "Return the name of this layer in the Data Source."
        C = capi.get_fd_name(self._ldefn)
        return force_str(C, self._ds.encoding, strings_only=True)

    @property
    def d(self, D=1):
        "Return the number of features in the Layer."
        return capi.get_feature_count(self.ptr, D)

    @property
    def e(self):
        "Return the number of fields in the Layer."
        return capi.get_field_count(self._ldefn)

    @property
    def f(self):
        "Return the geometry type (OGRGeomType) of the Layer."
        return OGRGeomType(capi.get_fd_geom_type(self._ldefn))

    @property
    def g(self):
        "Return the Spatial Reference used in this Layer."
        try:
            E = capi.get_layer_srs(self.ptr)
            return SpatialReference(srs_api.clone_srs(E))
        except SRSException:
            return None

    @property
    def h(self):
        """
        Return a list of string names corresponding to each of the Fields
        available in this Layer.
        """
        return [
            force_str(
                capi.get_field_name(capi.get_field_defn(self._ldefn, F)),
                self._ds.encoding,
                strings_only=True,
            )
            for F in range(self.e)
        ]

    @property
    def j(self):
        """
        Return a list of the types of fields in this Layer. For example,
        return the list [OFTInteger, OFTReal, OFTString] for an OGR layer that
        has an integer, a floating-point, and string fields.
        """
        return [
            OGRFieldTypes[capi.get_field_type(capi.get_field_defn(self._ldefn, G))]
            for G in range(self.e)
        ]

    @property
    def k(self):
        "Return a list of the maximum field widths for the features."
        return [
            capi.get_field_width(capi.get_field_defn(self._ldefn, H))
            for H in range(self.e)
        ]

    @property
    def l(self):
        "Return the field precisions for the features."
        return [
            capi.get_field_precision(capi.get_field_defn(self._ldefn, I))
            for I in range(self.e)
        ]

    def m(self):
        try:
            return OGRGeometry(geom_api.clone_geom(capi.get_spatial_filter(self.ptr)))
        except GDALException:
            return None

    def n(self, J):
        if isinstance(J, OGRGeometry):
            capi.set_spatial_filter(self.ptr, J.ptr)
        elif isinstance(J, (tuple, list)):
            if not len(J) == 4:
                raise ValueError("Spatial filter list/tuple must have 4 elements.")
            # Map c_double onto params -- if a bad type is passed in it
            # will be caught here.
            K, L, M, N = map(c_double, J)
            capi.set_spatial_filter_rect(self.ptr, K, L, M, N)
        elif J is None:
            capi.set_spatial_filter(self.ptr, None)
        else:
            raise TypeError(
                "Spatial filter must be either an OGRGeometry instance, a 4-tuple, or "
                "None."
            )

    spatial_filter = property(_get_spatial_filter, _set_spatial_filter)

    # #### Layer Methods ####
    def o(self, O):
        """
        Return a list containing the given field name for every Feature
        in the Layer.
        """
        if O not in self.h:
            raise GDALException("invalid field name: %s" % O)
        return [P.get(O) for P in self]

    def p(self, Q=False):
        """
        Return a list containing the OGRGeometry for every Feature in
        the Layer.
        """
        if Q:
            from django.contrib.gis.geos import GEOSGeometry

            return [GEOSGeometry(R.geom.wkb) for R in self]
        else:
            return [R.geom for R in self]

    def q(self, S):
        """
        Return a bool indicating whether the this Layer supports the given
        capability (a string). Valid capability strings include:
          'RandomRead', 'SequentialWrite', 'RandomWrite', 'FastSpatialFilter',
          'FastFeatureCount', 'FastGetExtent', 'CreateField', 'Transactions',
          'DeleteFeature', and 'FastSetNextByIndex'.
        """
        return bool(capi.test_capability(self.ptr, force_bytes(S)))
