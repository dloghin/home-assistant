"""Huawei LTE constants."""

DOMAIN = "huawei_lte"

DEFAULT_DEVICE_NAME = "LTE"
DEFAULT_NOTIFY_SERVICE_NAME = DOMAIN

UPDATE_SIGNAL = f"{DOMAIN}_update"
UPDATE_OPTIONS_SIGNAL = f"{DOMAIN}_options_update"

CONNECTION_TIMEOUT = 10
NOTIFY_SUPPRESS_TIMEOUT = 30

SERVICE_CLEAR_TRAFFIC_STATISTICS = "clear_traffic_statistics"
SERVICE_REBOOT = "reboot"
SERVICE_RESUME_INTEGRATION = "resume_integration"
SERVICE_SUSPEND_INTEGRATION = "suspend_integration"

ADMIN_SERVICES = {
    SERVICE_CLEAR_TRAFFIC_STATISTICS,
    SERVICE_REBOOT,
    SERVICE_RESUME_INTEGRATION,
    SERVICE_SUSPEND_INTEGRATION,
}

KEY_DEVICE_BASIC_INFORMATION = "device_basic_information"
KEY_DEVICE_INFORMATION = "device_information"
KEY_DEVICE_SIGNAL = "device_signal"
KEY_DIALUP_MOBILE_DATASWITCH = "dialup_mobile_dataswitch"
KEY_MONITORING_MONTH_STATISTICS = "monitoring_month_statistics"
KEY_MONITORING_STATUS = "monitoring_status"
KEY_MONITORING_TRAFFIC_STATISTICS = "monitoring_traffic_statistics"
KEY_NET_CURRENT_PLMN = "net_current_plmn"
KEY_NET_NET_MODE = "net_net_mode"
KEY_SMS_SMS_COUNT = "sms_sms_count"
KEY_WLAN_HOST_LIST = "wlan_host_list"
KEY_WLAN_WIFI_FEATURE_SWITCH = "wlan_wifi_feature_switch"

BINARY_SENSOR_KEYS = {KEY_MONITORING_STATUS, KEY_WLAN_WIFI_FEATURE_SWITCH}

DEVICE_TRACKER_KEYS = {KEY_WLAN_HOST_LIST}

SENSOR_KEYS = {
    KEY_DEVICE_INFORMATION,
    KEY_DEVICE_SIGNAL,
    KEY_MONITORING_MONTH_STATISTICS,
    KEY_MONITORING_STATUS,
    KEY_MONITORING_TRAFFIC_STATISTICS,
    KEY_NET_CURRENT_PLMN,
    KEY_NET_NET_MODE,
    KEY_SMS_SMS_COUNT,
}

SWITCH_KEYS = {KEY_DIALUP_MOBILE_DATASWITCH}

ALL_KEYS = BINARY_SENSOR_KEYS | DEVICE_TRACKER_KEYS | SENSOR_KEYS | SWITCH_KEYS