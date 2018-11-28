import logging
from datetime import timedelta
import asyncio

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect, dispatcher_send)
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_time_interval

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['pymoodo==0.0.2']
from pymoodo import Controller

_LOGGER = logging.getLogger(__name__)

MOODO_DEVICES = 'moodo'
MOODO_CONTROLLER = 'moodo_controller'

DOMAIN = 'moodo'

SCAN_INTERVAL = timedelta(seconds=30)

SIGNAL_UPDATE_MOODO = "moodo_update"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL):
            cv.time_period,
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass, base_config):
    """Setup the Moodo platform."""
    config = base_config[DOMAIN]
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    scan_interval = config.get(CONF_SCAN_INTERVAL)

    _LOGGER.info("Creating new Moodo component")
    if MOODO_DEVICES not in hass.data:
        hass.data[MOODO_DEVICES] = []

    # Setup connection with Moodo API
    controller = Controller(username, password)

    # Verify that passed in configuration works
    if not controller.authenticated:
        _LOGGER.error("Could not connect to Moody API")
        return False

    hass.data[MOODO_CONTROLLER] = controller

    # Add Moodoboxes as devices
    hass.data[MOODO_DEVICES] = controller.boxes

    # Start Moodo devices
    if hass.data[MOODO_DEVICES]:
        _LOGGER.info("Starting sensor components")
        discovery.load_platform(hass, "fan", DOMAIN, {}, config)

    def update_devices(event_time):
        """Call Moodo API to refresh information."""
        _LOGGER.debug("Updating Moodo Devices")
        controller = hass.data[MOODO_CONTROLLER]
        hass.data[MOODO_DEVICES] = controller.update_boxes()
        dispatcher_send(hass, SIGNAL_UPDATE_MOODO)

    # Call the Moodo API to refresh devices
    track_time_interval(hass, update_devices, scan_interval)

    return True

class MoodoEntity(Entity):
    """Entity class for Moodo devices."""

    def __init__(self, box, sensor_type, slot=None):
        """Initialize the Moodo entity."""
        self.box = box
        self.slot = slot
        self._sensor_type = sensor_type
        self._name = "{0} {1}".format(
            self.box.name,
            self._sensor_type)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    def update(self):
        """Get the latest data and updates the states."""
        _LOGGER.debug("Updating entity: %s", self._name)
        if self.hass.data[MOODO_DEVICES][self.box.id]:
            self.box = self.hass.data[MOODO_DEVICES][self.box.id]

    @asyncio.coroutine
    def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(
            self.hass, SIGNAL_UPDATE_MOODO, self._update_callback)

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_ha_state(True)