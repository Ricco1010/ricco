import warnings

from ..geometry.df import auto2shapely as ensure_gdf
from ..geometry.df import buffer
from ..geometry.df import lnglat2shapely as geom_lnglat2shapely
from ..geometry.df import lnglat2wkb as geom_lnglat2wkb
from ..geometry.df import lnglat2wkt as geom_lnglat2wkt
from ..geometry.df import mark_tags_v2
from ..geometry.df import nearest_neighbor
from ..geometry.df import projection
from ..geometry.df import shapely2lnglat as geom_shapely2lnglat
from ..geometry.df import shapely2wkb as geom_shapely2wkb
from ..geometry.df import shapely2wkt as geom_shapely2wkt
from ..geometry.df import shapely2x as geom_shapely_to
from ..geometry.df import spatial_agg
from ..geometry.df import wkb2lnglat as geom_wkb2lnglat
from ..geometry.df import wkb2shapely as geom_wkb2shapely
from ..geometry.df import wkb2wkt as geom_wkb2wkt
from ..geometry.df import wkt2lnglat as geom_wkt2lnglat
from ..geometry.df import wkt2shapely as geom_wkt2shapely
from ..geometry.df import wkt2wkb as geom_wkt2wkb
from ..geometry.util import crs_sh2000
from ..geometry.util import distance
from ..geometry.util import ensure_multi_geom
from ..geometry.util import get_epsg
from ..geometry.util import get_epsg_by_lng
from ..geometry.util import get_inner_point
from ..geometry.util import get_lng_by_city
from ..geometry.util import infer_geom_format
from ..geometry.util import is_geojson
from ..geometry.util import is_shapely
from ..geometry.util import is_wkb
from ..geometry.util import is_wkt
from ..geometry.util import multiline2multipolygon
from ..geometry.util import projection_lnglat
from ..geometry.util import wkb_dumps
from ..geometry.util import wkb_loads
from ..geometry.util import wkt_dumps
from ..geometry.util import wkt_loads

warnings.warn(
    'util.geom模块不再更新，请使用"ricco.geometry"中的相关模块',
    DeprecationWarning
)
