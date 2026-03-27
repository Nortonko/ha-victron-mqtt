"""Support for Victron GX switches."""

import logging
from typing import Any

from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    MetricKind,
    VictronEnum,
    WritableMetric as VictronVenusWritableMetric,
)

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .binary_sensor import VictronBinarySensor
from .const import SWITCH_OFF, SWITCH_ON
from .entity import VictronBaseEntity
from .hub import VictronGxConfigEntry

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0  # There is no I/O in the entity itself.


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VictronGxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Victron GX switches from a config entry."""
    hub = config_entry.runtime_data

    def on_new_metric(
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
    ) -> None:
        """Handle new switch metric discovery."""
        assert isinstance(metric, VictronVenusWritableMetric)
        assert hub._hub.installation_id is not None
        async_add_entities(
            [
                VictronSwitch(
                    device,
                    metric,
                    device_info,
                    hub.simple_naming,
                    hub._hub.installation_id,
                )
            ]
        )

    hub.register_new_metric_callback(MetricKind.SWITCH, on_new_metric)


class VictronSwitch(VictronBaseEntity, SwitchEntity):
    """Implementation of a Victron GX switch."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusWritableMetric,
        device_info: DeviceInfo,
        simple_naming: bool,
        installation_id: str,
    ) -> None:
        """Initialize the switch."""
        self._attr_is_on = VictronBinarySensor._is_on(metric.value)  # noqa: SLF001
        super().__init__(
            device,
            metric,
            device_info,
            "switch",
            simple_naming,
            installation_id,
        )

    @callback
    def _on_update_cb(self, value: Any) -> None:
        self._attr_is_on = VictronBinarySensor._is_on(value)  # noqa: SLF001
        self.async_write_ha_state()

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        _LOGGER.debug("Turning on switch: %s", self._attr_unique_id)
        self._metric.set(SWITCH_ON)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        _LOGGER.debug("Turning off switch: %s", self._attr_unique_id)
        self._metric.set(SWITCH_OFF)
