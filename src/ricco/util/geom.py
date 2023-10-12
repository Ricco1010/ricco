import warnings

from ..geometry.df import auto2shapely as ensure_gdf  # noqa
from ..geometry.df import buffer  # noqa
from ..geometry.df import lnglat2shapely as geom_lnglat2shapely  # noqa
from ..geometry.df import lnglat2wkb as geom_lnglat2wkb  # noqa
from ..geometry.df import lnglat2wkt as geom_lnglat2wkt  # noqa
from ..geometry.df import mark_tags_v2  # noqa
from ..geometry.df import nearest_neighbor  # noqa
from ..geometry.df import projection  # noqa
from ..geometry.df import shapely2lnglat as geom_shapely2lnglat  # noqa
from ..geometry.df import shapely2wkb as geom_shapely2wkb  # noqa
from ..geometry.df import shapely2wkt as geom_shapely2wkt  # noqa
from ..geometry.df import shapely2x as geom_shapely_to  # noqa
from ..geometry.df import spatial_agg  # noqa
from ..geometry.df import wkb2lnglat as geom_wkb2lnglat  # noqa
from ..geometry.df import wkb2shapely as geom_wkb2shapely  # noqa
from ..geometry.df import wkb2wkt as geom_wkb2wkt  # noqa
from ..geometry.df import wkt2lnglat as geom_wkt2lnglat  # noqa
from ..geometry.df import wkt2shapely as geom_wkt2shapely  # noqa
from ..geometry.df import wkt2wkb as geom_wkt2wkb  # noqa
from ..geometry.util import crs_sh2000  # noqa
from ..geometry.util import distance  # noqa
from ..geometry.util import ensure_multi_geom  # noqa
from ..geometry.util import get_epsg  # noqa
from ..geometry.util import get_epsg_by_lng  # noqa
from ..geometry.util import get_inner_point  # noqa
from ..geometry.util import get_lng_by_city  # noqa
from ..geometry.util import infer_geom_format  # noqa
from ..geometry.util import is_geojson  # noqa
from ..geometry.util import is_shapely  # noqa
from ..geometry.util import is_wkb  # noqa
from ..geometry.util import is_wkt  # noqa
from ..geometry.util import multiline2multipolygon  # noqa
from ..geometry.util import projection_lnglat  # noqa
from ..geometry.util import wkb_dumps  # noqa
from ..geometry.util import wkb_loads  # noqa
from ..geometry.util import wkt_dumps  # noqa
from ..geometry.util import wkt_loads  # noqa

warnings.warn(
    'util.geom模块不再更新，请使用"ricco.geometry"中的相关模块',
    DeprecationWarning
)
