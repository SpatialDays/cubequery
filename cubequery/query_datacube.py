
from pyproj import Proj, transform

import datacube
from datacube_utilities.createAOI import create_lat_lon


def query(params):
    dc = datacube.Datacube(app=__name__)

    lat_range, lon_range = _map_aoi(params)

    q = {
        "x": lon_range,
        "y": lat_range,
        "time": [0, 0]
    }
    result = dc.find_datasets(**q)
    return _map_result(result)


def _map_result(i):
    result = []
    return result


def _map_aoi(params):
    lat_extents, lon_extents = create_lat_lon(params['aoi'])
    in_proj = Proj("+init=" + params['aoi_crs'])
    out_proj = Proj("+init=" + params['cube_crs']) # TODO: should this come from an env var?

    min_lat, max_lat = lat_extents
    min_lon, max_lon = lon_extents

    x_A, y_A = transform(in_proj, out_proj, min_lon, min_lat)
    x_B, y_B = transform(in_proj, out_proj, max_lon, max_lat)

    lat_range = (y_A, y_B)
    lon_range = (x_A, x_B)

    return lat_range, lon_range


def _map_times(params):
    start_time = params['start_time']
    end_time = params['end_time']
    result = (start_time, end_time)
    return result
