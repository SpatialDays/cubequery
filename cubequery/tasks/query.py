import logging
import json
from shapely import wkt
from shapely.geometry import shape, GeometryCollection

def standard_validation(args):
    """
    Validates conditions based upon the combination of the parameters provided.

    Loads conditions set in input_conditions.json
    
    """
    
    #_settings_json = url_for('fetch_form_settings')
    
    _settings_json = None
    
    if not _settings_json:          
        with open('input_conditions.json') as res_json: 
            _settings_json = json.load(res_json)  

    keys = [k for k in _settings_json if k in args]

    errors = []
    
    # Validates AOI
    if 'aoi' in args:
        errors = validate_standard_spatial_query(args['aoi'])
    
    # Validates information against input_conditions.json
    for key in keys:
        for d in _settings_json[key]:
            if d['name'] == args[key]:
                for condition in d['conditions']:

                    # Integer Range Validation
                    if condition['type'] == 'int_range':
                        for c in condition['id']:
                            if c in args:                            
                                if len(condition['value'])==2:
                                    if not (int(args[c]) >= condition['value'][0]) or not(int(args[c]) <= condition['value'][1]):
                                        errors.append(create_error_message(condition))
                                else:
                                    if not (int(args[c]) >= condition['value'][0]):
                                        errors.append(create_error_message(condition))

                    # Date Range Validation
                    if condition['type'] == 'date_range':
                        for c in condition['id']:
                            if c in args:
                                if len(condition['value'])==2:
                                    if not (args[c] >= condition['value'][0]) or not(args[c] <= condition['value'][1]):
                                        errors.append(create_error_message(condition))
                                else:
                                    if not (args[c] >= condition['value'][0]):
                                        errors.append(create_error_message(condition))
    
    return errors


def create_error_message(condition):
    return {'Key':condition['id'], 'Error':condition['error_message'], 'Comment':condition['_comment']}

# TODO: Bounds conversion and sometimes spatial query dependent on product
def validate_standard_spatial_query(value):

    errors = []

    try:
        parsed_polygon = wkt.loads(value)
    except:
        return [create_error_message({'id':'aoi', 'error_message':'Polygon could not be loaded', '_comment':'Polygon could not be loaded'})]

    
    '''
    Returns validity of geometery (bool)
    * Whole of Fiji = True
    * Suva = True
    '''
    valid_geom = parsed_polygon.is_valid
    if not valid_geom:
        errors.append(create_error_message({'id':'aoi', 'error_message':'Geometry not a valid polygon', '_comment':'Geometry not a valid polygon'}))

    '''
    Returns area of polygon - About 1/4 of country ... 0.25 
    * Whole of Fiji = 1.8662849915034905
    * Suva = 0.017204474747948426
    '''
    area = parsed_polygon.area
    if area > 0.25:
        errors.append(create_error_message({'id':'aoi', 'error_message':'AOI area is too large', '_comment':'Size of polygon is too large'}))

    '''
    Returns bool for polygon inside Fiji
    '''
    with open("TM_FIJI_BORDERS.geojson") as f:
        features = json.load(f)["features"]
        fiji_polygon = GeometryCollection([shape(feature["geometry"]).buffer(0) for feature in features])
        
    fiji_polygon = wkt.loads('POLYGON((177.0421658157887 -17.359201951740324,178.9208279251632 -17.359201951740324,178.9208279251632 -18.352613689908015,177.0421658157887 -18.352613689908015,177.0421658157887 -17.359201951740324))')


    contains = fiji_polygon.contains(parsed_polygon)
    if contains == False:
        errors.append(create_error_message({'id':'aoi', 'error_message':'AOI out of Fiji bounds', '_comment':'AOI is either completely or partially out of the Fiji bounds'}))

    return errors
