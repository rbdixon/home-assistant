"""The tests for the Ambient Weather component."""
import re
import unittest
import ambient_api
from unittest.mock import patch
from ambient_api.ambientapi import AmbientAPI

import requests_mock

from homeassistant.components import weather
from homeassistant.util.unit_system import IMPERIAL_SYSTEM
from homeassistant.setup import setup_component

from tests.common import load_fixture, get_test_home_assistant


class TestAmbientWeather(unittest.TestCase):
    """Test the Ambient Weather component."""

    def setUp(self):
        """Set up things to be run when tests are started."""
        self.hass = get_test_home_assistant()
        self.hass.config.units = IMPERIAL_SYSTEM

    def tearDown(self):
        """Stop down everything that was started."""
        self.hass.stop()

    @requests_mock.Mocker()
    def test_setup(self, mock_req):
        """Test for successfully setting up the forecast.io platform."""
        mock_req.get(
            re.compile('https://api.ambientweather.net/v1/devices'),
            text=load_fixture('ambient_get_devices.json'),
        )
        mock_req.get(
            re.compile('https://api.ambientweather.net/v1/devices/XX:XX:XX:XX:XX:XX'),
            text=load_fixture('ambient_get_devices_mac.json'),
        )

        assert setup_component(
            self.hass,
            weather.DOMAIN,
            {
                'weather': {
                    'name': 'test',
                    'platform': 'ambient',
                    'app_key': 'foo',
                    'api_key': 'bar',
                }
            },
        )

        assert mock_req.called

        assert self.hass.states.get('weather.home_indoor') is not None
        assert self.hass.states.get('weather.home_outdoor') is not None
