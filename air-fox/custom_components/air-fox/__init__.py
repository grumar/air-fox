"""
Fetch information from Air-Fox.pl
"""

import asyncio
import logging
from datetime import timedelta

import aiohttp
import async_timeout
import homeassistant.helpers.config_validation as cv
import homeassistant.util as util
import voluptuous as vol
from bs4 import BeautifulSoup
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

AIR_FOX_ROOT_URL = 'http://air-fox.pl'

TIMEOUT = 10
MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=5)
CONF_STATION_TYPE = 'FOXYTECH'
CONF_INPUT_ID = 'testId'
CONF_STATION_ID = '1392'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
  vol.Required(CONF_STATION_ID): cv.Number,
  vol.Required(CONF_NAME): cv.string
})

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
  station_id = config.get(CONF_STATION_ID)
  station_type = config.get(CONF_STATION_TYPE)
  name = config.get(CONF_NAME)

  _LOGGER.info("Initializing sensor for: {0} type: {1}".format(station_id, station_type))
  add_devices([AirFoxSensor(hass, name, station_id, station_type)])

class AirFoxSensor(Entity):
  """Representation of a Sensor."""

  def __init__(self, hass, name, station_id, station_type):
    """Initialize the sensor."""
    self.hass = hass
    self.websession = async_get_clientsession(hass)
    self._name = name
    self.station_id = station_id
    self.station_type = station_type
    self.input_id = CONF_STATION_TYPE
    self.data = {
        'addressStreet': '...',
        'city': '...',
        'gegrLat': '...',
        'gegrLon': '...',
        'id': '',
        'qualityIndex': {},
        'sensors': {},
        'stationName': '...',
        'type': '...'
    }

  @property
  def name(self):
    """Return the name of the sensor."""
    return self._name

  @property
  def state_attributes(self):
    return {
        "input_id": self.input_id,
        "station_name": self.station_name,
        "address": self.address,
        "qualityIndex": self.qualityIndex,
        "lastUpdateDate": self.lastUpdateDate,
        "pm25": self.pm25,
    }

  @property
  def station_name(self):
    return self.data['stationName']

  @property
  def address(self):
    return self.data['addressStreet'] + ' ' + self.data['city']

  @property
  def qualityIndex(self):
      return self.data['qualityIndex.indexLevelName']

  @property
  def lastUpdateDate(self):
      return self.data['qualityIndex.stSourceDataDate']

  @property
  def pm25(self):
      return self.data['sensors.0.valueOfLastMeasurement']
  def query_url(self):
    return 'http://{base_url}/api/station/{station_id},{station_type}'.format(base_url=AIR_FOX_ROOT_URL, station_id=self.station_id, station_type=self.station_type)

  def token_url(self):
    return AIR_FOX_ROOT_URL

  @util.Throttle(MIN_TIME_BETWEEN_SCANS, MIN_TIME_BETWEEN_FORCED_SCANS)
  async def async_update(self):
    _LOGGER.info("Updating".format(self.query_url()))
    try:
      with async_timeout.timeout(TIMEOUT, loop=self.hass.loop):
        token_response = await self.websession.get(self.token_url())

        soup = BeautifulSoup(token_response)
        inp = soup.find("input", {"id": CONF_INPUT_ID})['value']

        headers = {
            "Authorization": f"Bearer {inp}",
        }
        response = await self.websession.get(self.query_url(), headers=headers)
        self.data = await response.json()
        _LOGGER.debug("Updating sensor: {}".format(self.data))
    except (asyncio.TimeoutError, aiohttp.ClientError, IndexError) as error:
      _LOGGER.error("Failed getting devices: %s", error)