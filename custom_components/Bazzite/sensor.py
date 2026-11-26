from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import BazziteCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bazzite sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            BazziteGameSensor(coordinator),
            BazziteCPUTemperatureSensor(coordinator),
        ]
    )


class BazziteGameSensor(SensorEntity):
    """Current activity (game or app) reported by Bazzite."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BazziteCoordinator,
    ) -> None:
        """Initialize the current game sensor."""

        self.coordinator = coordinator

        self._attr_name = "Activity"

        # Keep the original unique ID so Home Assistant reuses the existing
        # entity (same entity_id, history and automations).
        self._attr_unique_id = "bazzite_current_game"

        self._attr_icon = "mdi:monitor-dashboard"

        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, coordinator.entry.entry_id)
            },
            name=coordinator.entry.data.get(
                "device_name",
                "Bazzite PC",
            ),
            manufacturer="Bazzite",
            model="Bazzite Gaming PC",
        )

        coordinator.async_add_listener(
            self.async_write_ha_state
        )

    @property
    def extra_state_attributes(self):
        """Whether the activity is a game or an app."""

        return {
            "activity_type": self.coordinator.data.get(
                "activity_type"
            )
        }

    @property
    def native_value(self):
        """Return the current game or app, or idle."""

        return self.coordinator.data.get("status")

    @property
    def available(self) -> bool:
        """Unavailable while the PC is off, asleep or unreachable."""

        return (
            self.coordinator.is_up
            and "status" in self.coordinator.data
        )

    async def async_will_remove_from_hass(self) -> None:
        """Remove the coordinator listener."""

        self.coordinator.async_remove_listener(
            self.async_write_ha_state
        )


class BazziteCPUTemperatureSensor(SensorEntity):
    """Bazzite CPU temperature."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BazziteCoordinator,
    ) -> None:
        """Initialize the CPU temperature sensor."""

        self.coordinator = coordinator

        self._attr_name = "CPU Temperature"

        # Keep the original unique ID (see the current game sensor).
        self._attr_unique_id = "bazzite_cpu_temperature"

        self._attr_device_class = (
            SensorDeviceClass.TEMPERATURE
        )

        self._attr_native_unit_of_measurement = "°C"
        self._attr_icon = "mdi:thermometer"

        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, coordinator.entry.entry_id)
            },
            name=coordinator.entry.data.get(
                "device_name",
                "Bazzite PC",
            ),
            manufacturer="Bazzite",
            model="Bazzite Gaming PC",
        )

        coordinator.async_add_listener(
            self.async_write_ha_state
        )

    @property
    def native_value(self):
        """Return the last known CPU temperature."""

        return self.coordinator.data.get(
            "cpu_temperature"
        )

    @property
    def available(self) -> bool:
        """Unavailable while the PC is off, asleep or unreachable."""

        return (
            self.coordinator.is_up
            and "cpu_temperature" in self.coordinator.data
        )

    async def async_will_remove_from_hass(self) -> None:
        """Remove the coordinator listener."""

        self.coordinator.async_remove_listener(
            self.async_write_ha_state
        )