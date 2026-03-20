"""Unit tests for Victron GX MQTT entities."""

from unittest.mock import MagicMock, patch

import pytest
from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    MetricKind,
    MetricNature,
    MetricType,
)
from victron_mqtt.constants import VictronEnum

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from custom_components.victron_mqtt.binary_sensor import VictronBinarySensor
from custom_components.victron_mqtt.sensor import VictronSensor
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo


@pytest.fixture
def mock_device() -> VictronVenusDevice:
    """Return a mocked Victron device."""
    device = MagicMock(spec=VictronVenusDevice)
    device.name = "Test Device"
    return device


@pytest.fixture
def base_metric() -> VictronVenusMetric:
    """Return a mocked Victron metric with common defaults."""
    metric = MagicMock(spec=VictronVenusMetric)
    metric.metric_kind = MetricKind.SENSOR
    metric.unique_id = "metric_1"
    metric.short_id = "metric.short"
    metric.generic_short_id = "{phase}_voltage"
    metric.key_values = {"phase": "L1"}
    metric.precision = 2
    metric.unit_of_measurement = "V"
    metric.metric_type = MetricType.VOLTAGE
    metric.metric_nature = MetricNature.INSTANTANEOUS
    metric.value = 12.34
    return metric



async def test_sensor_update_task_triggers_state_update(
    hass: HomeAssistant, mock_device, base_metric
) -> None:
    """_on_update_task should schedule update on value change and not on same value."""
    device_info: DeviceInfo = {"identifiers": {("victron_mqtt", "dev_1")}}
    sensor = VictronSensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )

    with patch.object(sensor, "async_write_ha_state") as mock_sched:
        # Change value
        sensor._on_update_task(56.78)
        assert sensor.native_value == 56.78
        mock_sched.assert_called_once()

        # Same value -> no schedule
        sensor._on_update_task(56.78)
        mock_sched.assert_called_once()


async def test_binary_sensor_update_task_transitions(
    hass: HomeAssistant, mock_device, base_metric
) -> None:
    """Binary sensor should toggle based on On/Off strings and schedule when changed."""
    # Start with empty value to result in is_on False
    base_metric.value = ""
    device_info: DeviceInfo = {"identifiers": {("victron_mqtt", "dev_1")}}
    bin_entity = VictronBinarySensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )

    assert bin_entity.is_on is False

    with patch.object(bin_entity, "async_write_ha_state") as mock_sched:
        bin_entity._on_update_task("On")
        assert bin_entity.is_on is True
        mock_sched.assert_called_once()

        bin_entity._on_update_task("On")
        mock_sched.assert_called_once()


async def test_metric_mappings(hass: HomeAssistant, mock_device, base_metric) -> None:
    """Verify device_class, state_class, and unit mappings across all cases."""
    device_info: DeviceInfo = {"identifiers": {("victron_mqtt", "dev_1")}}

    # Device class mapping for all MetricType values we support
    device_class_cases = [
        (MetricType.POWER, SensorDeviceClass.POWER),
        (MetricType.APPARENT_POWER, SensorDeviceClass.APPARENT_POWER),
        (MetricType.ENERGY, SensorDeviceClass.ENERGY),
        (MetricType.VOLTAGE, SensorDeviceClass.VOLTAGE),
        (MetricType.CURRENT, SensorDeviceClass.CURRENT),
        (MetricType.FREQUENCY, SensorDeviceClass.FREQUENCY),
        (MetricType.ELECTRIC_STORAGE_PERCENTAGE, SensorDeviceClass.BATTERY),
        (MetricType.TEMPERATURE, SensorDeviceClass.TEMPERATURE),
        (MetricType.SPEED, SensorDeviceClass.SPEED),
        (MetricType.LIQUID_VOLUME, SensorDeviceClass.VOLUME_STORAGE),
        (MetricType.DURATION, SensorDeviceClass.DURATION),
        (MetricType.TIME, None),
    ]

    for metric_type, expected_device_class in device_class_cases:
        base_metric.metric_type = metric_type
        sensor = VictronSensor(
            mock_device,
            base_metric,
            device_info,
            simple_naming=True,
            installation_id="x",
        )
        assert sensor.device_class == expected_device_class

    # Unknown/unsupported device class should map to None
    base_metric.metric_type = MagicMock()
    sensor = VictronSensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )
    assert sensor.device_class is None

    # State class mapping
    base_metric.metric_nature = MetricNature.INSTANTANEOUS
    sensor = VictronSensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )
    assert sensor.state_class == SensorStateClass.MEASUREMENT

    base_metric.metric_nature = MetricNature.CUMULATIVE
    sensor = VictronSensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )
    assert sensor.state_class == SensorStateClass.TOTAL

    base_metric.metric_nature = MagicMock()
    sensor = VictronSensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )
    assert sensor.state_class is None

    # Unit of measurement: set natively only when device_class is present
    base_metric.metric_type = MetricType.VOLTAGE  # has device_class
    base_metric.unit_of_measurement = "V"
    sensor = VictronSensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )
    assert sensor.native_unit_of_measurement == "V"

    # Without device_class, native_unit should be None (translation handles display)
    base_metric.metric_type = MetricType.NONE  # no device_class
    base_metric.unit_of_measurement = "modules"
    sensor = VictronSensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )
    assert sensor.native_unit_of_measurement is None


async def test_translation_fields(
    hass: HomeAssistant, mock_device, base_metric
) -> None:
    """Translation key is normalized and placeholders passed through."""
    device_info: DeviceInfo = {"identifiers": {("victron_mqtt", "dev_1")}}
    sensor = VictronSensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )

    assert sensor.translation_key == "phase_voltage"
    assert sensor.translation_placeholders == {"phase": "L1"}


async def test_sensor_enum_value_is_normalized_for_state_translation(
    hass: HomeAssistant, mock_device, base_metric
) -> None:
    """VictronEnum sensor values should map to enum codes for translations."""

    class AirQuality(VictronEnum):
        GOOD = (100, "good", "Good")
        SLIGHTLY_UNHEALTHY = (200, "slightly_unhealthy", "Slightly unhealthy")

    device_info: DeviceInfo = {"identifiers": {("victron_mqtt", "dev_1")}}
    sensor = VictronSensor(
        mock_device, base_metric, device_info, simple_naming=True, installation_id="x"
    )

    with patch.object(sensor, "async_write_ha_state") as mock_sched:
        sensor._on_update_task(AirQuality.SLIGHTLY_UNHEALTHY)
        assert sensor.native_value == "slightly_unhealthy"
        mock_sched.assert_called_once()
