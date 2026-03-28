"""Constants for the victron_mqtt integration."""
from victron_mqtt import MetricNature

from homeassistant.components.sensor import SensorStateClass

# Integration specific values (custom / builtin Home Assistant)
DOMAIN = "victron_mqtt"
DEFAULT_SIMPLE_NAMING = True

# generic config values
CONF_INSTALLATION_ID = "installation_id"
CONF_MODEL = "model"
CONF_SERIAL = "serial"
CONF_ROOT_TOPIC_PREFIX = "root_topic_prefix"
CONF_UPDATE_FREQUENCY_SECONDS = "update_frequency"
CONF_OPERATION_MODE = "operation_mode"
CONF_EXCLUDED_DEVICES = "excluded_devices"
CONF_SIMPLE_NAMING = "simple_naming"
CONF_ELEVATED_TRACING = "elevated_tracing"

DEVICE_MESSAGE = "device"
SENSOR_MESSAGE = "sensor"

DEFAULT_HOST = "venus.local."
DEFAULT_PORT = 1883
DEFAULT_UPDATE_FREQUENCY_SECONDS = 30

# Service names
SERVICE_PUBLISH = "publish"

# Service data attributes
ATTR_METRIC_ID = "metric_id"
ATTR_DEVICE_ID = "device_id"
ATTR_VALUE = "value"

# Not using GenericOnOff as some switches use different enums.
# It has to be with id "on" to be on and "off" to be off.
SWITCH_ON = "on"
SWITCH_OFF = "off"


METRIC_NATURE_TO_STATE_CLASS: dict[MetricNature, SensorStateClass] = {
    MetricNature.MEASUREMENT: SensorStateClass.MEASUREMENT,
    MetricNature.TOTAL: SensorStateClass.TOTAL,
    MetricNature.TOTAL_INCREASING: SensorStateClass.TOTAL_INCREASING,
}
