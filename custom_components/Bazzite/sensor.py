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


# Shown in the dropdown from the start; anything else (games, other apps) is
# added the first time it appears.
DEFAULT_ACTIVITY_OPTIONS = [
    "Idle",
    "Jellyfin",
    "Plex",
    "Kodi",
    "VLC",
    "Moonlight",
    "RetroArch",
    "Dolphin",
    "PCSX2",
    "RPCS3",
    "Heroic Games Launcher",
    "Lutris",
    "Spotify",
    "Discord",
    "Firefox",
    "Chrome",
    "Brave",
]


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

        # Enum sensor: Home Assistant shows the known activities as a
        # dropdown in automations and the UI.
        self._attr_device_class = SensorDeviceClass.ENUM
        self._seen_options = list(DEFAULT_ACTIVITY_OPTIONS)

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

        coordinator.async_add_listener(self._handle_update)

    def _handle_update(self) -> None:
        """Add a new activity to the dropdown, then update the state."""

        value = self.native_value

        if value is not None and value not in self._seen_options:
            self._seen_options.append(value)

        self.async_write_ha_state()

    @property
    def options(self) -> list[str]:
        """All activities seen so far (the dropdown choices)."""

        return self._seen_options

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

        status = self.coordinator.data.get("status")

        if status is not None and status.lower() == "idle":
            return "Idle"

        return status

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
            self._handle_update
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