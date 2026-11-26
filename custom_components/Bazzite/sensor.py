import logging
import asyncio
import aiohttp
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

HEARTBEAT = 4        # seconds between pings; a silently dead PC is noticed in ~6 s
CONNECT_TIMEOUT = 5  # seconds to wait for one connection attempt
RETRY_DELAY = 3      # seconds between reconnect attempts

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    coordinator = BazziteWebSocketCoordinator(hass, entry)
    await coordinator.start()

    async_add_entities([
        BazziteGameSensor(coordinator),
        BazziteCPUTemperatureSensor(coordinator)
    ])

class BazziteWebSocketCoordinator:
    def __init__(self, hass, entry):
        self.hass = hass
        self.config = entry.data
        self.data = {}
        self.listeners = []
        self.ws_task = None
        self.power_down = False  # server announced sleep/shutdown

    async def start(self):
        self.ws_task = asyncio.create_task(self._connect_websocket())

    async def _connect_websocket(self):
        session = async_get_clientsession(self.hass)
        url = f"ws://{self.config['host']}:{self.config['port']}/ws"
        while True:
            ws = None
            try:
                _LOGGER.debug(f"Connecting to Bazzite WebSocket at {url}")
                # wait_for: connecting to a sleeping PC can otherwise hang for minutes
                ws = await asyncio.wait_for(
                    session.ws_connect(url, heartbeat=HEARTBEAT), CONNECT_TIMEOUT
                )
                _LOGGER.info("Bazzite WebSocket connected!")
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        new_data = msg.json()
                        _LOGGER.debug("WebSocket message received: %s", new_data)
                        self._handle_message(new_data)
                    elif msg.type in (
                        aiohttp.WSMsgType.ERROR,
                        aiohttp.WSMsgType.CLOSE,
                        aiohttp.WSMsgType.CLOSING,
                        aiohttp.WSMsgType.CLOSED,
                    ):
                        break
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _LOGGER.debug("WebSocket connection error: %s", e)

            # Connection is gone (PC asleep, off or unreachable): go unavailable now,
            # then close, since closing a dead peer can take a few seconds.
            self._mark_offline()
            if ws is not None and not ws.closed:
                try:
                    async with asyncio.timeout(2):
                        await ws.close()
                except Exception:
                    pass
            await asyncio.sleep(RETRY_DELAY)

    def _handle_message(self, new_data):
        power = new_data.pop("power", None)
        if power in ("sleep", "shutdown"):
            # Server is about to go down: flip to unavailable immediately
            self.power_down = True
            self._notify_listeners()
            return
        if power == "on":
            self.power_down = False
        if new_data or power == "on":
            self.data.update(new_data)
            self._notify_listeners()

    def _mark_offline(self):
        if not self.data and not self.power_down:
            return  # already offline; don't rewrite state every retry
        self.data = {}
        self.power_down = False
        self._notify_listeners()

    def _notify_listeners(self):
        for update_callback in self.listeners:
            update_callback()

    def async_add_listener(self, update_callback):
        self.listeners.append(update_callback)

class BazziteGameSensor(Entity):
    def __init__(self, coordinator: BazziteWebSocketCoordinator):
        self.coordinator = coordinator
        self._attr_name = "Bazzite Current Game"
        self._attr_unique_id = "bazzite_current_game"
        
        coordinator.async_add_listener(self.async_write_ha_state)

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        return self.coordinator.data.get("status", None)
        
    @property
    def available(self):
        return "status" in self.coordinator.data and not self.coordinator.power_down

    @property
    def icon(self):
        state = self.state
        if state == "idle":
            return "mdi:power-standby"
        if state == "unavailable":
            return "mdi:alert-circle-outline"
        return "mdi:controller-classic"

class BazziteCPUTemperatureSensor(Entity):
    def __init__(self, coordinator: BazziteWebSocketCoordinator):
        self.coordinator = coordinator
        self._attr_name = "Bazzite CPU Temperature"
        self._attr_unique_id = "bazzite_cpu_temperature"
        self._attr_device_class = "temperature"
        self._attr_unit_of_measurement = "°C"
        self._attr_icon = "mdi:thermometer"

        coordinator.async_add_listener(self.async_write_ha_state)

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        return self.coordinator.data.get("cpu_temperature", None)
        
    @property
    def available(self):
        return "cpu_temperature" in self.coordinator.data and not self.coordinator.power_down
