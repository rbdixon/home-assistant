"""
Platform for retrieving meteorological data from Ambient Weather.

For more details about this platform, please refer to the documentation
TODO: https://home-assistant.io/components/weather.darksky/
"""
from datetime import datetime, timedelta
import logging

from requests.exceptions import ConnectionError as ConnectError, HTTPError, Timeout
import voluptuous as vol

from homeassistant.components.weather import (
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_PRESSURE,
    PLATFORM_SCHEMA,
    WeatherEntity,
)
from homeassistant.const import CONF_API_KEY, CONF_URL, TEMP_FAHRENHEIT
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

REQUIREMENTS = ['ambient-api==1.5.2']

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Ambient Weather"

INDOOR = True
OUTDOOR = False

MAP_MODE_STRING = {INDOOR: 'Indoor', OUTDOOR: 'Outdoor'}

# https://github.com/ambient-weather/api-docs/wiki/Device-Data-Specs
MAP_FIELD = {
    INDOOR: {ATTR_WEATHER_HUMIDITY: 'humidityin', ATTR_WEATHER_TEMPERATURE: 'tempinf'},
    OUTDOOR: {
        ATTR_WEATHER_WIND_BEARING: 'winddir',
        ATTR_WEATHER_WIND_SPEED: 'windspeedmph',
        # ATTR_: 'windgustmph',
        # ATTR_: 'maxdailygust',
        # ATTR_: 'windgustdir',
        # ATTR_: 'windspdmph_avg2m',
        # ATTR_: 'winddir_avg2m',
        # ATTR_: 'windspdmph_avg10m',
        # ATTR_: 'winddir_avg10m',
        ATTR_WEATHER_HUMIDITY: 'humidity',
        # ATTR_: 'humidity1',
        # ATTR_: 'humidity2',
        # ATTR_: 'humidity3',
        # ATTR_: 'humidity4',
        # ATTR_: 'humidity5',
        # ATTR_: 'humidity6',
        # ATTR_: 'humidity7',
        # ATTR_: 'humidity8',
        # ATTR_: 'humidity9',
        # ATTR_: 'humidity10',
        ATTR_WEATHER_TEMPERATURE: 'tempf',
        # ATTR_: 'temp1f',
        # ATTR_: 'temp2f',
        # ATTR_: 'temp3f',
        # ATTR_: 'temp4f',
        # ATTR_: 'temp5f',
        # ATTR_: 'temp6f',
        # ATTR_: 'temp7f',
        # ATTR_: 'temp8f',
        # ATTR_: 'temp9f',
        # ATTR_: 'temp10f',
        # ATTR_: 'battout',
        # ATTR_: 'batt1',
        # ATTR_: 'batt2',
        # ATTR_: 'batt3',
        # ATTR_: 'batt4',
        # ATTR_: 'batt5',
        # ATTR_: 'batt6',
        # ATTR_: 'batt7',
        # ATTR_: 'batt8',
        # ATTR_: 'batt9',
        # ATTR_: 'batt10',
        # ATTR_: 'hourlyrainin',
        # ATTR_FORECAST_PRECIPITATION: 'dailyrainin',
        # ATTR_: '24hourrainin',
        # ATTR_: 'weeklyrainin',
        # ATTR_: 'monthlyrainin',
        # ATTR_: 'yearlyrainin',
        # ATTR_: 'eventrainin',
        # ATTR_: 'totalrainin',
        ATTR_WEATHER_PRESSURE: 'baromrelin',
        # ATTR_: 'baromabsin',
        # ATTR_: 'uv',
        # ATTR_: 'solarradiation',
        # ATTR_: 'co2',
        # ATTR_: 'relay1',
        # ATTR_: 'relay2',
        # ATTR_: 'relay3',
        # ATTR_: 'relay4',
        # ATTR_: 'relay5',
        # ATTR_: 'relay6',
        # ATTR_: 'relay7',
        # ATTR_: 'relay8',
        # ATTR_: 'relay9',
        # ATTR_: 'relay10',
        # ATTR_: 'lastRain',
        # ATTR_: 'dewPoint',
        # ATTR_: 'feelsLike',
        # ATTR_FORECAST_TIME: 'dateutc',
    },
}

CONF_APP_KEY = 'app_key'
CONF_UNITS = 'units'
DEFAULT_NAME = 'Ambient Weather'
DEFAULT_URL = 'https://api.ambientweather.net/v1'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_APP_KEY): cv.string,
        vol.Optional(CONF_URL, default=DEFAULT_URL): cv.string,
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=3)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Ambient Weather."""

    from ambient_api.ambientapi import AmbientAPI

    api_key = config.get(CONF_API_KEY)
    app_key = config.get(CONF_APP_KEY)
    url = config.get(CONF_URL)

    api = AmbientAPI(
        AMBIENT_ENDPOINT=url, AMBIENT_API_KEY=api_key, AMBIENT_APPLICATION_KEY=app_key
    )

    devices = []
    for device in api.get_devices():
        # Add outdoor weather
        devices.append(AmbientWeatherDevice(device, mode=OUTDOOR))
        if device.last_data.get('tempinf', None) is not None:
            # Add indoor weather
            devices.append(AmbientWeatherDevice(device, mode=INDOOR))

    if len(devices) > 0:
        add_entities(devices, True)


class AmbientWeatherDevice(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, dev, mode=False):
        """Initialize an Ambient Weather monitored device."""
        self._dev = dev
        self._mode = mode
        self._data = self._dev.last_data
        self._name = '{location}: {mode}'.format(
            location=self._dev.info['location'], mode=MAP_MODE_STRING[self._mode]
        )

    def _get(self, attr):
        field = MAP_FIELD[self._mode].get(attr, None)
        value = self._data.get(field, None)
        _LOGGER.debug(
            '{name}: {attr} = {value}'.format(name=self._name, attr=attr, value=value)
        )
        return value

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def temperature(self):
        """Return the temperature."""
        return self._get(ATTR_WEATHER_TEMPERATURE)

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_FAHRENHEIT

    @property
    def humidity(self):
        """Return the humidity."""
        return self._get(ATTR_WEATHER_HUMIDITY)

    @property
    def wind_speed(self):
        """Return the wind speed."""
        return self._get(ATTR_WEATHER_WIND_SPEED)

    @property
    def wind_bearing(self):
        """Return the wind bearing."""
        return self._get(ATTR_WEATHER_WIND_BEARING)

    @property
    def pressure(self):
        """Return the pressure."""
        return self._get(ATTR_WEATHER_PRESSURE)

    @property
    def condition(self):
        """Return the weather condition."""
        return None

    def update(self):
        """Get the latest data from Ambient Weather."""
        res = self._dev.get_data(limit=1)

        if len(res) != 0:
            _LOGGER.info(
                'Updated Ambient Weather data for {name}.'.format(name=self._name)
            )
            self._data = res[0]

