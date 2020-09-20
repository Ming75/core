"""Support for binary sensor using RPi GPIO."""
import logging

import voluptuous as vol

from homeassistant.components import rpi_gpio
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.const import CONF_NAME, DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.reload import setup_reload_service

from . import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONF_BOUNCETIME = "bouncetime"
CONF_INVERT_LOGIC = "invert_logic"
CONF_PORTS = "ports"
CONF_PULL_MODE = "pull_mode"

DEFAULT_BOUNCETIME = 50
DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = "UP"

PORT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): vol.In(["UP", "DOWN"]),
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_PORTS, default={}): vol.Schema({cv.positive_int: PORT_SCHEMA})}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Raspberry PI GPIO devices."""

    setup_reload_service(hass, DOMAIN, PLATFORMS)

    binary_sensors = []
    ports = config[CONF_PORTS]

    for port, params in ports.items():
        binary_sensors.append(RPiGPIOBinarySensor(port, params))
    add_entities(binary_sensors, True)


class RPiGPIOBinarySensor(BinarySensorEntity):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    def __init__(self, port, params):
        """Initialize the RPi binary sensor."""
        self._port = port
        self._name = params[CONF_NAME] or DEVICE_DEFAULT_NAME
        self._bouncetime = params[CONF_BOUNCETIME] or DEFAULT_BOUNCETIME
        self._pull_mode = params[CONF_PULL_MODE] or DEFAULT_PULL_MODE
        self._invert_logic = params[CONF_INVERT_LOGIC] or DEFAULT_INVERT_LOGIC

        rpi_gpio.setup_input(self._port, self._pull_mode)

        def read_gpio(port):
            """Read state from GPIO."""
            self._state = rpi_gpio.read_input(self._port)
            self.schedule_update_ha_state()

        rpi_gpio.edge_detect(self._port, read_gpio, self._bouncetime)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self._state != self._invert_logic

    def update(self):
        """Update the GPIO state."""
        self._state = rpi_gpio.read_input(self._port)
