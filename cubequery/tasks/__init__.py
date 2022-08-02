import json
import ast
import logging
import os
import zipfile
from datetime import datetime
from enum import EnumMeta
from os import path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import datacube
from jobtastic import JobtasticTask
from shapely import wkt
from shapely.geometry import shape, GeometryCollection

from cubequery import get_config, fetch_form_settings
from libcatapult.storage.s3_tools import S3Utils

_http_headers = {"Content-Type": "application/json", "User-Agent": "cubequery-result"}


class DType(EnumMeta):
    STRING = "str"
    INT = "int"
    FLOAT = "float"
    LAT = "lat"
    LON = "lon"
    DATE = "date"
    TIME = "time"
    WKT = "wkt"
    MULTI = "multi"
    YEAR = "year"


def map_to_dtype(input):
    lower = input.lower()
    if lower == "string":
        return DType.STRING
    if lower == "int":
        return DType.INT
    if lower == "float":
        return DType.FLOAT
    if lower == "lat":
        return DType.LAT
    if lower == "lon":
        return DType.LON
    if lower == "date":
        return DType.DATE
    if lower == "time":
        return DType.TIME
    if lower == "wkt":
        return DType.WKT
    if lower == "multi":
        return DType.MULTI
    if lower == "year":
        return DType.YEAR


def map_from_dtype(input):
    if input == DType.STRING:
        return "DType.STRING"
    if input == DType.INT:
        return "DType.INT"
    if input == DType.FLOAT:
        return "DType.FLOAT"
    if input == DType.LAT:
        return "DType.LAT"
    if input == DType.LON:
        return "DType.LON"
    if input == DType.DATE:
        return "DType.DATE"
    if input == DType.TIME:
        return "DType.TIME"
    if input == DType.WKT:
        return "DType.WKT"
    if input == DType.MULTI:
        return "DType.MULTI"
    if input == DType.YEAR:
        return "DType.YEAR"
    raise IndexError()


class Parameter(object):
    def __init__(self, name, display_name, d_type, description, valid=None, default=None, example_value=None):
        if valid is None:
            valid = []
        self.name = name
        self.display_name = display_name
        self.d_type = d_type
        self.description = description
        self.valid = valid
        self.default = default
        self.example_value = example_value

    def __eq__(self, o: object) -> bool:
        if not super().__eq__(o):
            return False
        if self.name != o.name:
            return False
        return True

    def __ne__(self, o: object) -> bool:
        return super().__ne__(o)


class CubeQueryTask(JobtasticTask):

    @classmethod
    def cal_significant_kwargs(cls, parameters):
        cls.significant_kwargs = [("params", str)]
        return cls.significant_kwargs

    @classmethod
    def map_d_type_to_jobtastic(cls, d_type):
        # TODO: add more data types here.
        # special handling for dates, lat lon pairs, bounding boxes, etc.
        if d_type == DType.INT:
            return str
        if d_type in (DType.FLOAT, DType.LAT, DType.LON):
            return str
        return str

    def map_kwargs(self, **kwargs):
        result = {}
        logging.info("decoding args")
        for k, v in json.loads(kwargs['params']).items():
            logging.info(f"decoding {k} with value {v}")
            args = [p for p in self.parameters if p.name == k]
            if len(args) > 0:
                arg = args[0]
                logging.info(f"found arg for {k} with type {arg.d_type}")
                if arg.d_type == DType.INT:
                    result[k] = int(v)
                elif arg.d_type in (DType.FLOAT, DType.LAT, DType.LON):
                    result[k] = float(v)
                elif arg.d_type == DType.MULTI:
                    result[k] = v
                else:
                    result[k] = v
            else:
                logging.warning(f"Not found a parameter entry for {k}")
                result[k] = v
        return result

    def validate_arg(self, name, value):
        search = [p for p in self.parameters if p.name == name]
        if len(search) == 0:
            return False, f"parameter {name} not found"

        param = search[0]
        if not validate_d_type(param, value):
            return False, f"parameter {name} value did not validate"

        if len(param.valid) > 0 and param.d_type == DType.STRING:
            if isinstance(param.valid[0], dict):
                if not [v for v in param.valid if value in v.values()]:
                    return False, f"value {value} not found in valid values"
            else:
                if not [v for v in param.valid if value in v]:
                    return False, f"value {value} not found in valid values"

        return True, ""

    def calculate_result(self, publish_to_esri, **kwargs):
        """
        This is the entry point for a task run. Will be called by celery.

        :param kwargs: arguments to the tasks.
        :return:
        """

        # connect to the datacube and pass that in to the users function.
        # Everything should be talking to the datacube here so makes sense to pull it out and make things
        # easier for the users.
        result_dir = get_config("App", "result_dir")
        path_prefix = path.join(result_dir, self.request.id)

        os.makedirs(path_prefix, exist_ok=True)

        args = self.map_kwargs(**kwargs)

        dc = datacube.Datacube(app=self.name)
        outputs = self.generate_product(dc, path_prefix, **args)
        logging.info(f"got result of {outputs}")
        self.log_query(path_prefix)
        self.zip_outputs(path_prefix, outputs)

        output_url = self.upload_results(path_prefix)
        if publish_to_esri:
            self.ping_results(output_url, args)

    def log_query(self, path_prefix):
        output = path.join(path_prefix, "query.json")
        with open(output, 'w') as f:
            json.dump(self.request.__dict__, f, skipkeys=True)

    def zip_outputs(self, path_prefix, results):
        output = os.path.join(path_prefix, self.request.id + "_output.zip")
        with zipfile.ZipFile(output, 'w') as zf:
            zf.write(path.join(path_prefix, "query.json"), arcname="query.json")
            for f in results:
                zf.write(f, arcname=path.basename(f))

    def upload_results(self, path_prefix):
        source_file_path = os.path.join(path_prefix, self.request.id + "_output.zip")
        dest_file_path = os.path.join(get_config("AWS", "path_prefix"), self.request.id + "_output.zip")

        access_key = get_config("AWS", "access_key_id")
        secret_key = get_config("AWS", "secret_access_key")
        bucket = get_config("AWS", "bucket")

        s3_tools = S3Utils(access_key, secret_key, bucket, get_config("AWS", "s3_endpoint"),
                           get_config("AWS", "region"))

        s3_tools.put_file(source_file_path, dest_file_path)

        return dest_file_path

    def ping_results(self, output_url, results):
        result_url = get_config("App", "result_url")
        if result_url:

            # step one get log in token
            # token = login_to_publisher()

            # step two send payload
            url = f"{get_config('App', 'result_url')}/submit"
            result_url = f"http://{get_config('AWS', 's3_endpoint')}/{get_config('AWS', 'bucket')}/{output_url}"
            if get_config('AWS', 's3_endpoint').startswith("http://"):
                result_url = result_url[7:]
            payload = {
                "url": result_url,
                "name": results['user']
            }
            logging.info(f"payload: {payload}")

            req = Request(url, json.dumps(payload).encode(), headers=_http_headers)
            try:
                resp = urlopen(req)
                if resp == "ok":
                    logging.info("request completed")
            except HTTPError as e:
                logging.error(f"could not log into publish server {e}")
                raise e
            except Exception as e:
                logging.error(f"Could not send results message {e}")
                # intentionally swallowing error as the data has still been generated at this point.

    herd_avoidance_timeout = 60
    cache_duration = 60 * 60 * 24  # One day of seconds

    def standard_validation(self, args):
        """
        Validates conditions based upon the combination of the parameters provided.

        Loads conditions set in input_conditions.json
        
        """

        _settings_json = fetch_form_settings()

        if not _settings_json:
            with open('input_conditions.json') as res_json:
                _settings_json = json.load(res_json)

        keys = [k for k in _settings_json if k in args]

        errors = []

        # Validates AOI
        wkt_fields = [p.name for p in self.parameters if p.d_type == DType.WKT]
        countries = ast.literal_eval(get_config("Boundaries", "projects")).keys()

        for s in wkt_fields:
            errors = validate_standard_spatial_query(args[s], countries)

        # Validates information against input_conditions.json
        # Parameters to be validated e.g. platform
        for key in keys:
            # The value of the parameter
            for d in _settings_json[key]:
                # If the param is included in arguments
                if d['name'] == args[key]:
                    for condition in d['conditions']:
                        # Check for process specific condition
                        if "processes" in condition and self.name not in condition['processes']:
                            continue

                        # Integer Range Validation
                        if condition['type'] == 'int_range':
                            for c in condition['id']:
                                if c in args:
                                    if len(condition['value']) == 2:
                                        if not (int(args[c]) >= condition['value'][0]) or not (
                                                int(args[c]) <= condition['value'][1]):
                                            errors.append(create_error_message(condition))
                                    else:
                                        if not (int(args[c]) >= condition['value'][0]):
                                            errors.append(create_error_message(condition))

                        # Date Range Validation
                        if condition['type'] == 'date_range':
                            for c in condition['id']:
                                if c in args:
                                    if len(condition['value']) == 2:
                                        if not (args[c] >= condition['value'][0]) or not (
                                                args[c] <= condition['value'][1]):
                                            errors.append(create_error_message(condition))
                                    else:
                                        if not (args[c] >= condition['value'][0]):
                                            errors.append(create_error_message(condition))

        return errors


def validate_standard_spatial_query(aoi, countries):
    
    errors = []

    try:
        parsed_polygon = wkt.loads(aoi)
    except:
        return [create_error_message({'id': 'aoi', 'error_message': 'Polygon could not be loaded',
                                        '_comment': 'Polygon could not be loaded'})]

    '''
    Returns validity of geometery (bool)
    * Whole of Fiji = True
    * Suva = True
    '''
    valid_geom = parsed_polygon.is_valid
    if not valid_geom:
        errors.append(create_error_message({'id': 'aoi', 'error_message': 'Geometry not a valid polygon',
                                            '_comment': 'Geometry not a valid polygon'}))

    '''
    Returns area of polygon - About 1/4 of country ... 0.25 
    * Whole of Fiji = 1.8662849915034905
    * Suva = 0.017204474747948426
    '''
    area = parsed_polygon.area
    if area > 0.25:
        errors.append(create_error_message(
            {'id': 'aoi', 'error_message': 'AOI area is too large', '_comment': 'Size of polygon is too large'}))

    '''
    Returns bool for polygon inside Fiji
    
    For when antimeridian problem is resolved:
    with open("TM_FIJI_BORDERS.geojson") as f:
        features = json.load(f)["features"]
        fiji_polygon = GeometryCollection([shape(feature["geometry"]).buffer(0) for feature in features])
    '''
    projects=get_config("Boundaries", "projects")
    available_countries = {k: v for k, v in ast.literal_eval(projects).items() if k in countries}

    valid_geom = False       
    for country in available_countries.keys():
        if parsed_polygon.within(wkt.loads(available_countries[country]['bounds'])):
            valid_geom = True
    
    if not valid_geom:
        errors.append(create_error_message({'id': 'aoi', 'error_message': 'AOI is not within your available countries',
                                            '_comment': 'AOI is not within the available country'}))

    return errors


def login_to_publisher():
    url = f"{get_config('App', 'result_url')}/token"
    login_payload = {
        'name': get_config("App", "result_login_user"),
        'pass': get_config("App", "result_login_pass")
    }
    req = Request(url, json.dumps(login_payload).encode(), headers=_http_headers)
    try:
        resp = urlopen(req)
        return json.load(resp)['token']
    except HTTPError as e:
        logging.error(f"could not log into publish server {e}")
        raise e


def validate_d_type(param, value):
    if param.d_type == DType.INT:
        return check_int(value)
    if param.d_type == DType.FLOAT:
        return check_float(param, value)
    if param.d_type == DType.MULTI:
        return True
    if param.d_type == DType.LAT:
        if check_float(value):
            v = float(value)
            return -90.0 <= v <= 90.0
        return False
    if param.d_type == DType.LON:
        if check_float(value):
            v = float(value)
            return -180.0 <= v <= 180.0
        return False
    if param.d_type == DType.WKT:
        # try and parse it and see what happens
        try:
            wkt.loads(value)
            return True
        except Exception:
            return False
    if param.d_type == DType.DATE:
        # try and parse it and see what happens
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    # if it is not one of the above types we can just check it is a string for now.
    return isinstance(value, str)


def check_multi(s):
    if isinstance(s, list):
        return True
    return False


def check_int(s):
    if isinstance(s, int):
        return True
    if isinstance(s, str):
        if len(s) == 0:
            return False
        if s[0] in ('-', '+'):
            return s[1:].isdigit()

        return s.isdigit()
    return False


def check_float(param, s):
    if isinstance(s, float):
        return check_float_range(param, s)
    try:
        return check_float_range(param, s)
    except ValueError:
        return False


def check_float_range(param, s):
    if not param.valid:
        return True

    if not isinstance(param.valid, list):
        return True

    try:
        v = float(s)

        if len(param.valid) == 2:
            return param.valid[0] <= v <= param.valid[1]
        else:
            return v in param.valid

    except ValueError:
        return False


def create_error_message(condition):
    return {'Key': condition['id'], 'Error': condition['error_message'], 'Comment': condition['_comment']}
