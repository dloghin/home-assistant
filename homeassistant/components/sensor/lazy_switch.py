import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    TEMP_FAHRENHEIT, CONF_NAME, CONF_HOST, CONF_MAC, CONF_PASSWORD)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.util.temperature import celsius_to_fahrenheit

REQUIREMENTS = ['lazy_switch==0.1']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Lazy Switch'
DEFAULT_PASSWORD = '1234'
DEFAULT_USERNAME = 'admin'

CONF_NO_SENSORS = "no_sensors"
CONF_SLOTS = "slots"
CONF_HUMIDITY_OFFSET = 'humidity_offset'
CONF_TEMPERATURE_OFFSET = 'temperature_offset'

# DHT11 is able to deliver data once per second, DHT22 once every two
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

SENSOR_TEMPERATURE = "AM2302_Temperature"
SENSOR_HUMIDITY = "AM2302_Humidity"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
	vol.Required(CONF_HOST): cv.string,
	vol.Required(CONF_MAC): cv.string,
	vol.Optional(CONF_NAME): cv.string,
	vol.Optional(CONF_PASSWORD): cv.string,
	vol.Required(CONF_NO_SENSORS): cv.string,
	vol.Required(CONF_SLOTS): cv.ensure_list,
	vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
	vol.Optional(CONF_TEMPERATURE_OFFSET, default=0):
		vol.All(vol.Coerce(float), vol.Range(min=-100, max=100)),
	vol.Optional(CONF_HUMIDITY_OFFSET, default=0):
		vol.All(vol.Coerce(float), vol.Range(min=-100, max=100))
})


def setup_platform(hass, config, add_devices, discovery_info=None):
	from lazy_switch import lazy_switch
    
	# get configuration parameters
	host = config.get(CONF_HOST)
	mac = config.get(CONF_MAC)
	name = config.get(CONF_NAME)
	pin = config.get(CONF_PASSWORD)
	no_sensors = int(config.get(CONF_NO_SENSORS))
	slots = config.get(CONF_SLOTS)

	# get Lazy Switch Driver Device using the manager
	lsman = lazy_switch.LazySwitchManager()
	lsdev = lsman.get_device(mac, host, pin, name, 0, int(no_sensors))

	if lsdev == None:
		_LOGGER.error("No registered Lazy Sensor Device with MAC " + mac)
		return

	# update number of switches sinc ethe device might have been created by
	# a sensor
	lsdev.update_no_sensors(int(no_sensors))
	lsdev.info()
	sensors = []
	for slot in slots:
		if slot["sensor"] == "AM2302_Humidity":
			offset = 0.0
			if CONF_HUMIDITY_OFFSET in slot:
				offset = float(slot[CONF_HUMIDITY_OFFSET])
			sensors.append(LazySensor(slot["name"], lsdev, int(slot["slot"]), slot["sensor"], "%", offset))
		elif slot["sensor"] == "AM2302_Temperature":
			offset = 0.0
			if CONF_TEMPERATURE_OFFSET in slot:
				offset = float(slot[CONF_TEMPERATURE_OFFSET])
			sensors.append(LazySensor(slot["name"], lsdev, int(slot["slot"]), slot["sensor"], "C", offset))

	add_devices(sensors, True)


class LazySensor(Entity):

	def __init__(self, name, lsdev, slot, sensor_type, unit, offset):
		"""Initialize the sensor."""
		self._name = name
		self._lsdev = lsdev
		self._slot = slot
		self._type = sensor_type
		self._unit = unit
		self._offset = offset
		self._state = None
        
	@property
	def name(self):
		"""Return the name of the sensor."""
		return self._name

	@property
	def state(self):
		"""Return the state of the sensor."""
		return self._state

	@property
	def unit_of_measurement(self):
		"""Return the unit of measurement of this entity, if any."""
		return self._unit

	def update(self):
		print("Lazy Sensor Update " + self._type + " " + str(self._slot))
		val = self._lsdev.get_sensor_value(self._slot)

		if self._type == SENSOR_TEMPERATURE:
			_LOGGER.debug("Temperature %.1f \u00b0C + offset %.1f", val, self._offset)
			temperature = val / 10.0
			if (temperature >= -20) and (temperature < 80):
				temperature = round(temperature + self._offset, 1)
				if self._unit == TEMP_FAHRENHEIT:
					self._state = round(celsius_to_fahrenheit(temperature), 1)
				else:
					self._state = temperature
		elif self._type == SENSOR_HUMIDITY:
			humidity = val / 10.0
			_LOGGER.debug("Humidity %.1f%% + offset %.1f", humidity, self._offset)
			if (humidity >= 0) and (humidity <= 100):
				self._state = round(humidity + self._offset, 1)

		print("Lazy Sensor Value " + str(self._state))

