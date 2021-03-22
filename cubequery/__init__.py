
# init the config here so it is available in many places.
import configparser
import logging
from os import environ
import json

__author__ = """Emily Selwood"""
__email__ = 'emily.selwood@sa.catapult.org.uk'
__version__ = '0.1.0'

import logstash

_config = configparser.ConfigParser()
_config.read("config.cfg")

settings_json = ""

with open('input_conditions.json') as res_json:
    settings_json = json.load(res_json)
        
def get_config(section, key):
    """
    Get a configuration value from the environment if it is available if not fall back to the config file.

    Environment version of the values from the config file are the {section}_{key} upper cased.

    :param section: The configuration section to look in.
    :param key: The config key to return the value of.
    :return: the value of the config key.
    """
    env_result = environ.get(f"{section}_{key}".upper())
    if env_result:
        return env_result

    return _config.get(section, key)

def fetch_form_settings():
    """
    Gets dynamic form settings loaded from a JSON file
    """
    global settings_json
    return settings_json

# also configure the console logging just in case
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(
    logging.Formatter('%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)s -- %(message)s')
)

# configure the root logger.
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)

logging.getLogger("packages").setLevel(logging.INFO)
logging.getLogger("matplotlib").setLevel(logging.INFO)
logging.getLogger("rasterio").setLevel(logging.INFO)
logging.getLogger("fiona").setLevel(logging.INFO)
logging.getLogger("shapely").setLevel(logging.INFO)

logging.getLogger('flask_cors').setLevel(logging.DEBUG)

logger.addHandler(console)

# For later as we will likely one day want better logging.
if get_config("Log_Stash", "enabled").lower() == "true":
    log_stash_host = get_config('Log_Stash', 'host')
    log_stash_port = int(get_config('Log_Stash', 'port'))

    log_stash = logstash.TCPLogstashHandler(
        log_stash_host,
        log_stash_port,
        version=1,
        tags=['s1_ard']
    )
    log_stash.setLevel(logging.DEBUG)
    logger.addHandler(log_stash)
