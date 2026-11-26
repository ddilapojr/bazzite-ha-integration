from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up Bazzite binary sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            BazziteOnlineSensor(coordinator),
            BazziteInGameSensor(coordinator),
        ]
    )


class BazziteOnlineSensor(BinarySensorEntity):
    """Whether the Bazzite PC is online."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BazziteCoordinator,
    ) -> None:
        """Initialize the online sensor."""

        self.coordinator = coordinator

        self._attr_name = "Online"

        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_online"
        )

        self._attr_device_class = (
            BinarySensorDeviceClass.CONNECTIVITY
        )

        self._attr_icon = "mdi:desktop-tower"

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
    def is_on(self) -> bool:
        """Return whether the Bazzite PC is online."""

        return self.coordinator.is_up

    @property
    def available(self) -> bool:
        """Offline is a valid state."""

        return True

    async def async_will_remove_from_hass(self) -> None:
        """Remove the coordinator listener."""

        self.coordinator.async_remove_listener(
            self.async_write_ha_state
        )


class BazziteInGameSensor(BinarySensorEntity):
    """Whether the Bazzite PC is currently in a game."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BazziteCoordinator,
    ) -> None:
        """Initialize the in-game sensor."""

        self.coordinator = coordinator

        self._attr_name = "In Game"

        self._attr_unique_id = (
            f"{coordinator.entry.entry_id}_in_game"
        )

        self._attr_device_class = (
            BinarySensorDeviceClass.RUNNING
        )

        self._attr_icon = "mdi:controller-classic"

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
    def is_on(self) -> bool:
        """Return whether a game (not just an app) is running."""

        if not self.coordinator.online:
            return False

        data = self.coordinator.data

        # Newer servers say whether it is a game or an app; older ones
        # only send the name.
        if "activity_type" in data:
            return data["activity_type"] == "game"

        return data.get("status", "idle") != "idle"

    @property
    def available(self) -> bool:
        """Unavailable while the PC is off, asleep or unreachable."""

        return self.coordinator.is_up

    async def async_will_remove_from_hass(self) -> None:
        """Remove the coordinator listener."""

        self.coordinator.async_remove_listener(
            self.async_write_ha_state
        )