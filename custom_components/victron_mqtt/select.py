"""Support for Victron GX select entities."""

import logging
from typing import Any

from victron_mqtt import (
    Device as VictronVenusDevice,
    Metric as VictronVenusMetric,
    MetricKind,
    VictronEnum,
    WritableMetric as VictronVenusWritableMetric,
)

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import VictronBaseEntity
from .hub import VictronGxConfigEntry

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0  # There is no I/O in the entity itself.


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: VictronGxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Victron GX select entities from a config entry."""
    hub = config_entry.runtime_data

    def on_new_metric(
        device: VictronVenusDevice,
        metric: VictronVenusMetric,
        device_info: DeviceInfo,
    ) -> None:
        """Handle new select metric discovery."""
        assert isinstance(metric, VictronVenusWritableMetric)
        assert hub._hub.installation_id is not None
        async_add_entities(
            [
                VictronSelect(
                    device,
                    metric,
                    device_info,
                    hub.simple_naming,
                    hub._hub.installation_id,
                )
            ]
        )

    hub.register_new_metric_callback(MetricKind.SELECT, on_new_metric)


class VictronSelect(VictronBaseEntity, SelectEntity):
    """Implementation of a Victron GX select entity."""

    def __init__(
        self,
        device: VictronVenusDevice,
        metric: VictronVenusWritableMetric,
        device_info: DeviceInfo,
        simple_naming: bool,
        installation_id: str,
    ) -> None:
        """Initialize the select entity."""
        assert metric.enum_values is not None
        self._attr_options = metric.enum_values
        self._attr_current_option = VictronSelect._map_value_to_state(metric.value)
        super().__init__(
            device,
            metric,
            device_info,
            "select",
            simple_naming,
            installation_id,
        )

    @callback
    def _on_update_cb(self, value: Any) -> None:
        self._attr_current_option = self._map_value_to_state(value)
        self.async_write_ha_state()

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        assert isinstance(self._metric, VictronVenusWritableMetric)
        assert self._metric.enum_values is not None
        if option not in self._metric.enum_values:
            _LOGGER.info(
                "Setting switch %s to %s failed as option not supported. supported options are: %s",
                self._attr_unique_id,
                option,
                self._metric.enum_values,
            )
            return
        _LOGGER.info("Setting switch %s to %s", self._attr_unique_id, option)
        assert isinstance(self._metric, VictronVenusWritableMetric)
        self._metric.set(option)

    @staticmethod
    def _map_value_to_state(value: Any) -> Any:
        """Normalize Victron enum values to their enum code."""
        return value.id if isinstance(value, VictronEnum) else value
