"""
Support for GPSLogger.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/gpslogger/
"""
import logging

import voluptuous as vol
from aiohttp import web

import homeassistant.helpers.config_validation as cv
from homeassistant.components.device_tracker import ATTR_BATTERY
from homeassistant.components.device_tracker.tile import ATTR_ALTITUDE
from homeassistant.const import HTTP_UNPROCESSABLE_ENTITY, \
    HTTP_OK, ATTR_LATITUDE, ATTR_LONGITUDE, CONF_WEBHOOK_ID
from homeassistant.helpers import config_entry_flow
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'gpslogger'
DEPENDENCIES = ['webhook']

TRACKER_UPDATE = '{}_tracker_update'.format(DOMAIN)

ATTR_ACCURACY = 'accuracy'
ATTR_ACTIVITY = 'activity'
ATTR_DEVICE = 'device'
ATTR_DIRECTION = 'direction'
ATTR_PROVIDER = 'provider'
ATTR_SPEED = 'speed'

DEFAULT_ACCURACY = 200
DEFAULT_BATTERY = -1


def _id(value: str) -> str:
    """Coerce id by removing '-'."""
    return value.replace('-', '')


WEBHOOK_SCHEMA = vol.Schema({
    vol.Required(ATTR_LATITUDE): cv.latitude,
    vol.Required(ATTR_LONGITUDE): cv.longitude,
    vol.Required(ATTR_DEVICE): _id,
    vol.Optional(ATTR_ACCURACY, default=DEFAULT_ACCURACY): vol.Coerce(float),
    vol.Optional(ATTR_BATTERY, default=DEFAULT_BATTERY): vol.Coerce(float),
    vol.Optional(ATTR_SPEED): vol.Coerce(float),
    vol.Optional(ATTR_DIRECTION): vol.Coerce(float),
    vol.Optional(ATTR_ALTITUDE): vol.Coerce(float),
    vol.Optional(ATTR_PROVIDER): cv.string,
    vol.Optional(ATTR_ACTIVITY): cv.string
})


async def async_setup(hass, hass_config):
    """Set up the GPSLogger component."""
    hass.async_create_task(
        async_load_platform(hass, 'device_tracker', DOMAIN, {}, hass_config)
    )
    return True


async def handle_webhook(hass, webhook_id, request):
    """Handle incoming webhook with GPSLogger request."""
    try:
        data = WEBHOOK_SCHEMA(dict(await request.post()))
    except vol.MultipleInvalid as error:
        return web.Response(
            body=error.error_message,
            status=HTTP_UNPROCESSABLE_ENTITY
        )

    attrs = {
        ATTR_SPEED: data.get(ATTR_SPEED),
        ATTR_DIRECTION: data.get(ATTR_DIRECTION),
        ATTR_ALTITUDE: data.get(ATTR_ALTITUDE),
        ATTR_PROVIDER: data.get(ATTR_PROVIDER),
        ATTR_ACTIVITY: data.get(ATTR_ACTIVITY)
    }

    device = data[ATTR_DEVICE]

    async_dispatcher_send(
        hass,
        TRACKER_UPDATE,
        device,
        (data[ATTR_LATITUDE], data[ATTR_LONGITUDE]),
        data[ATTR_BATTERY],
        data[ATTR_ACCURACY],
        attrs
    )

    return web.Response(
        body='Setting location for {}'.format(device),
        status=HTTP_OK
    )


async def async_setup_entry(hass, entry):
    """Configure based on config entry."""
    hass.components.webhook.async_register(
        DOMAIN, 'GPSLogger', entry.data[CONF_WEBHOOK_ID], handle_webhook)
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    hass.components.webhook.async_unregister(entry.data[CONF_WEBHOOK_ID])
    return True

config_entry_flow.register_webhook_flow(
    DOMAIN,
    'GPSLogger Webhook',
    {
        'docs_url': 'https://www.home-assistant.io/components/gpslogger/'
    }
)
