"""Allows to configure a switch using RPi GPIO."""
import logging

import voluptuous as vol

from homeassistant.components import rpi_gpio
from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.reload import setup_reload_service

from . import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONF_PULL_MODE = "pull_mode"
CONF_PORTS = "ports"
CONF_INVERT_LOGIC = "invert_logic"

DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = "UP"

_SWITCHES_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PORTS, default={}): vol.Schema(
            {cv.positive_int: _SWITCHES_SCHEMA}
        )
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Raspberry PI GPIO devices."""

    setup_reload_service(hass, DOMAIN, PLATFORMS)

    switches = []
    ports = config.get(CONF_PORTS)

    for port, params in ports.items():
        switches.append(RPiGPIOSwitch(port, params))
    add_entities(switches)


class RPiGPIOSwitch(ToggleEntity):
    """Representation of a  Raspberry Pi GPIO."""

    def __init__(self, port, params):
        """Initialize the RPi binary sensor."""
        self._port = port
        self._name = params[CONF_NAME] or DEVICE_DEFAULT_NAME
        self._invert_logic = params[CONF_INVERT_LOGIC] or DEFAULT_INVERT_LOGIC

        self._state = False
        rpi_gpio.setup_output(self._port)
        rpi_gpio.write_output(self._port, 1 if self._invert_logic else 0)

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the device on."""
        rpi_gpio.write_output(self._port, 0 if self._invert_logic else 1)
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        rpi_gpio.write_output(self._port, 1 if self._invert_logic else 0)
        self._state = False
        self.schedule_update_ha_state()
