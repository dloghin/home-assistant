import logging
from homeassistant.helpers.discovery import load_platform
from homeassistant.const import (CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME, CONF_MAC)

REQUIREMENTS = ['lazy_switch==0.1']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'lazy_switch'

DEFAULT_NAME = 'Lazy Switch'
DEFAULT_PASSWORD = '1234'
DEFAULT_USERNAME = 'admin'

CONF_NO_SW = "no_switches"

def setup(hass, config):
	"""Lazy Switch Manager"""
	from lazy_switch import lazy_switch

	"""Config"""
	config = config.get(DOMAIN)
	if config is None:
		config = {}

	if DOMAIN not in hass.data:
		hass.data[DOMAIN] = {}

	"""Mandatory"""
	host = config.get(CONF_HOST)
	mac = config.get(CONF_MAC)
	no_sw = config.get(CONF_NO_SW)

	"""Optional"""
	username = config.get(CONF_USERNAME)
	pin = config.get(CONF_PASSWORD)
	name = config.get(CONF_NAME)

	if host == None or mac == None or no_sw == None:
		_LOGGER.error("Host, MAC and number of switches (no_switches) are mandatory!")
		return False

	lsman = lazy_switch.LazySwitchManager()
	lsdev = lsman.get_device(mac)
	if lsdev == None:
		lsdev = None
		if host == None or host == "bluetooth":
			lsdev = lazy_switch.LazySwitchBluetooth(name, no_sw, mac, pin)
			lsdev.connect()
		lsman.add_device(mac, lsdev)

	print("Obj " + str(lsman))

#	load_platform(hass, 'light', DOMAIN)
	load_platform(hass, 'switch', DOMAIN)

	return True
