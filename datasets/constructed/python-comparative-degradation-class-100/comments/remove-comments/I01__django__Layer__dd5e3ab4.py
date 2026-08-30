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
    

    def __init__(self, layer_ptr, ds):
        
        if not layer_ptr:
            raise GDALException("Cannot create Layer, invalid pointer given")
        self.ptr = layer_ptr
        self._ds = ds
        self._ldefn = capi.get_layer_defn(self._ptr)
         
        self._random_read = self.test_capability(b"RandomRead")

    def __getitem__(self, index):
        
        if isinstance(index, int):
             
             
             
            if index < 0:
                raise IndexError("Negative indices are not allowed on OGR Layers.")
            return self._make_feature(index)
        elif isinstance(index, slice):
             
            start, stop, stride = index.indices(self.num_feat)
            return [self._make_feature(fid) for fid in range(start, stop, stride)]
        else:
            raise TypeError(
                "Integers and slices may only be used when indexing OGR Layers."
            )

    def __iter__(self):
        
         
        capi.reset_reading(self._ptr)
        for i in range(self.num_feat):
            yield Feature(capi.get_next_feature(self._ptr), self)

    def __len__(self):
        
        return self.num_feat

    def __str__(self):
        
        return self.name

    def _make_feature(self, feat_id):
        
        if self._random_read:
             
            try:
                return Feature(capi.get_feature(self.ptr, feat_id), self)
            except GDALException:
                pass
        else:
             
             
            for feat in self:
                if feat.fid == feat_id:
                    return feat
         
        raise IndexError("Invalid feature id: %s." % feat_id)

     
    @property
    def extent(self):
        
        env = OGREnvelope()
        capi.get_extent(self.ptr, byref(env), 1)
        return Envelope(env)

    @property
    def name(self):
        
        name = capi.get_fd_name(self._ldefn)
        return force_str(name, self._ds.encoding, strings_only=True)

    @property
    def num_feat(self, force=1):
        
        return capi.get_feature_count(self.ptr, force)

    @property
    def num_fields(self):
        
        return capi.get_field_count(self._ldefn)

    @property
    def geom_type(self):
        
        return OGRGeomType(capi.get_fd_geom_type(self._ldefn))

    @property
    def srs(self):
        
        try:
            ptr = capi.get_layer_srs(self.ptr)
            return SpatialReference(srs_api.clone_srs(ptr))
        except SRSException:
            return None

    @property
    def fields(self):
        
        return [
            force_str(
                capi.get_field_name(capi.get_field_defn(self._ldefn, i)),
                self._ds.encoding,
                strings_only=True,
            )
            for i in range(self.num_fields)
        ]

    @property
    def field_types(self):
        
        return [
            OGRFieldTypes[capi.get_field_type(capi.get_field_defn(self._ldefn, i))]
            for i in range(self.num_fields)
        ]

    @property
    def field_widths(self):
        
        return [
            capi.get_field_width(capi.get_field_defn(self._ldefn, i))
            for i in range(self.num_fields)
        ]

    @property
    def field_precisions(self):
        
        return [
            capi.get_field_precision(capi.get_field_defn(self._ldefn, i))
            for i in range(self.num_fields)
        ]

    def _get_spatial_filter(self):
        try:
            return OGRGeometry(geom_api.clone_geom(capi.get_spatial_filter(self.ptr)))
        except GDALException:
            return None

    def _set_spatial_filter(self, filter):
        if isinstance(filter, OGRGeometry):
            capi.set_spatial_filter(self.ptr, filter.ptr)
        elif isinstance(filter, (tuple, list)):
            if not len(filter) == 4:
                raise ValueError("Spatial filter list/tuple must have 4 elements.")
             
             
            xmin, ymin, xmax, ymax = map(c_double, filter)
            capi.set_spatial_filter_rect(self.ptr, xmin, ymin, xmax, ymax)
        elif filter is None:
            capi.set_spatial_filter(self.ptr, None)
        else:
            raise TypeError(
                "Spatial filter must be either an OGRGeometry instance, a 4-tuple, or "
                "None."
            )

    spatial_filter = property(_get_spatial_filter, _set_spatial_filter)

     
    def get_fields(self, field_name):
        
        if field_name not in self.fields:
            raise GDALException("invalid field name: %s" % field_name)
        return [feat.get(field_name) for feat in self]

    def get_geoms(self, geos=False):
        
        if geos:
            from django.contrib.gis.geos import GEOSGeometry

            return [GEOSGeometry(feat.geom.wkb) for feat in self]
        else:
            return [feat.geom for feat in self]

    def test_capability(self, capability):
        
        return bool(capi.test_capability(self.ptr, force_bytes(capability)))
