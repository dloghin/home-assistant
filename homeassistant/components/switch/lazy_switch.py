import logging

import voluptuous as vol

from homeassistant.components.switch import (SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME, CONF_MAC)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['lazy_switch==0.1']

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Lazy Switch'
DEFAULT_PASSWORD = '1234'
DEFAULT_USERNAME = 'admin'

CONF_NO_SW = "no_switches"
CONF_SLOTS = "slots"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
	vol.Required(CONF_HOST): cv.string,
	vol.Required(CONF_MAC): cv.string,
	vol.Required(CONF_NO_SW): cv.string,
	vol.Required(CONF_SLOTS): cv.ensure_list,
	vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
	vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): cv.string,
	vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
	from lazy_switch import lazy_switch

	# get configuration parameters
	host = config.get(CONF_HOST)
	mac = config.get(CONF_MAC)
	name = config.get(CONF_NAME)
	pin = config.get(CONF_PASSWORD)
	no_sw = config.get(CONF_NO_SW)
	slots = config.get(CONF_SLOTS)

	# get Lazy Switch Driver Device using the manager
	lsman = lazy_switch.LazySwitchManager()
	lsdev = lsman.get_device(mac, host, pin, name, int(no_sw), 0)

	if lsdev == None:
		_LOGGER.error("No registered Lazy Switch Device with MAC " + mac)
		return

	# update number of switches sinc ethe device might have been created by
	# a sensor 
	lsdev.update_no_switches(int(no_sw))
	lsdev.info()
	switches = []
	for slot in slots:
		switches.append(LazySwitch(slot["name"], lsdev, int(slot["slot"])))
	add_devices(switches)

class LazySwitch(SwitchDevice):

	def __init__(self, name, device, slot):
		self._dev = device
		self._slot = slot
		self._name = name
		self._state = False
		self._now_power = 0.0
		self._now_energy_day = 0.0

	@property
	def name(self):
		"""Return the name of the Smart Plug, if any."""
		return self._name

	@property
	def current_power_w(self):
		"""Return the current power usage in W."""
		return self._now_power

	@property
	def today_energy_kwh(self):
		"""Return the today total energy usage in kWh."""
		return self._now_energy_day

	@property
	def is_on(self):
		"""Return true if switch is on."""
		return self._state

	def turn_on(self, **kwargs):
		"""Turn the switch on."""
		self._dev.on_switch(self._slot)

	def turn_off(self):
		"""Turn the switch off."""
		self._dev.off_switch(self._slot)

	def update(self):		
		self._state = self._dev.get_switch_state(self._slot)
		print("Lazy Switch Update slot " + str(self._slot) + " value " + str(self._state))
