from shapely.geometry import LinearRing
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from shapely.geometry import MultiPoint
from shapely.geometry import MultiPolygon
from shapely.geometry import Point
from shapely.geometry import Polygon

GeomTypeSet = (
  Point, MultiPoint,
  Polygon, MultiPolygon,
  LineString, MultiLineString,
  LinearRing
)
