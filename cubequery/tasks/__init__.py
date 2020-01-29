import json
from enum import EnumMeta

from jobtastic import JobtasticTask


class DType(EnumMeta):
    STRING = "str"
    INT = "int"
    FLOAT = "float"
    LAT = "lat"
    LON = "lon"
    DATE = "date"
    TIME = "time"
    WKT = "wkt"


class DTypeEncoder(json.JSONEncoder):
    def default(self, o):
        if type(o) in DType.values():
            return {"__enum__": str(o)}
        return json.JSONEncoder.default(self, o)


class Parameter(object):
    def __init__(self, name, d_type, description):
        self.name = name
        self.d_type = d_type
        self.description = description


class CubeQueryTask(JobtasticTask):

    @classmethod
    def cal_significant_kwargs(cls, parameters):
        result = []
        for p in parameters:
            result += [(p.name, cls.map_d_type_to_jobtastic(p.d_type))]
        cls.significant_kwargs = result
        return result

    @classmethod
    def map_d_type_to_jobtastic(cls, d_type):
        # TODO: add more data types here.
        # special handling for dates, lat lon pairs, bounding boxes, etc.
        if d_type == DType.INT:
            return int
        return str

    def validate_arg(self, name, value):
        # TODO: Make this return a message to be more useful
        if name not in [p.name for p in self.parameters]:
            return False
        # TODO: validate data type of value
        # TODO: check ranges
        return True

    herd_avoidance_timeout = 60
    cache_duration = 60 * 60 * 24  # One day of seconds
