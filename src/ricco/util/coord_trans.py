import warnings

from ..geometry.coord_trans import coord_trans_geom  # noqa
from ..geometry.coord_trans import coord_trans_x2y  # noqa

warnings.warn(
    'util.coord_trans，请使用"ricco.coord_trans"中的相关模块',
    DeprecationWarning
)
