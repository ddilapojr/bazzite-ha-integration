import asyncio
import json
import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_HOST,
    CONF_PORT,
    WEBSOCKET_CONNECT_TIMEOUT,
    WEBSOCKET_HEARTBEAT,
    WEBSOCKET_RECONNECT_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class BazziteCoordinator:
    """Maintain the WebSocket connection to the Bazzite server."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        self.hass = hass
        self.entry = entry

        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]

        self.data: dict = {}
        self.online = False

        # True after the server announced that the PC is about to sleep or
        # shut down (the connection stays open for a moment longer).
        self.power_down = False

        self.listeners = []

        self._websocket_task: asyncio.Task | None = None
        self._stopping = False

    @property
    def websocket_url(self) -> str:
        """Return the Bazzite WebSocket URL."""
        return f"ws://{self.host}:{self.port}/ws"

    @property
    def is_up(self) -> bool:
        """True while connected and the PC has not announced sleep/shutdown."""
        return self.online and not self.power_down

    async def async_start(self) -> None:
        """Start the coordinator."""
        self._stopping = False

        # Background task: this loop runs for as long as the integration does.
        self._websocket_task = self.hass.async_create_background_task(
            self._websocket_loop(),
            name="bazzite_websocket",
        )

    async def async_stop(self) -> None:
        """Stop the coordinator."""
        self._stopping = True

        if self._websocket_task is not None:
            self._websocket_task.cancel()

            try:
                await self._websocket_task
            except asyncio.CancelledError:
                pass

            self._websocket_task = None

        self._set_online(False)

    @staticmethod
    async def _close(websocket) -> None:
        """Close a WebSocket without waiting on a dead peer."""
        if websocket is None or websocket.closed:
            return

        try:
            async with asyncio.timeout(2):
                await websocket.close()
        except Exception:  # noqa: BLE001
            pass

    async def _websocket_loop(self) -> None:
        """Maintain a persistent WebSocket connection."""

        session = async_get_clientsession(self.hass)

        while not self._stopping:
            websocket = None

            try:
                _LOGGER.debug(
                    "Connecting to Bazzite WebSocket at %s",
                    self.websocket_url,
                )

                # wait_for: connecting to a sleeping or powered-off PC can
                # otherwise hang for a long time.
                websocket = await asyncio.wait_for(
                    session.ws_connect(
                        self.websocket_url,
                        heartbeat=WEBSOCKET_HEARTBEAT,
                        autoping=True,
                    ),
                    WEBSOCKET_CONNECT_TIMEOUT,
                )

                _LOGGER.info(
                    "Bazzite WebSocket connected"
                )

                self._set_online(True)

                async for message in websocket:
                    if self._stopping:
                        break

                    if message.type == aiohttp.WSMsgType.TEXT:
                        self._handle_message(message.data)

                    elif message.type == aiohttp.WSMsgType.ERROR:
                        _LOGGER.debug(
                            "Bazzite WebSocket error: %s",
                            message.data,
                        )
                        break

                    elif message.type in (
                        aiohttp.WSMsgType.CLOSE,
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSING,
                    ):
                        break

            except asyncio.CancelledError:
                await self._close(websocket)
                raise

            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                ConnectionError,
            ) as err:
                _LOGGER.debug(
                    "Bazzite WebSocket disconnected: %s",
                    err,
                )

            except Exception:
                _LOGGER.exception(
                    "Unexpected Bazzite WebSocket error"
                )

            # Go unavailable first: closing a dead connection can take a
            # few seconds.
            self._set_online(False)
            await self._close(websocket)

            if self._stopping:
                break

            await asyncio.sleep(
                WEBSOCKET_RECONNECT_DELAY
            )

    def _handle_message(self, raw_message: str) -> None:
        """Process a WebSocket message."""

        try:
            message = json.loads(raw_message)
        except (TypeError, json.JSONDecodeError):
            _LOGGER.warning(
                "Received invalid JSON from Bazzite: %s",
                raw_message,
            )
            return

        if not isinstance(message, dict):
            return

        _LOGGER.debug(
            "Received Bazzite update: %s",
            message,
        )

        changed = False

        power = message.get("power")

        if power in ("sleep", "shutdown"):
            # The PC announced it is going down: flip to unavailable right
            # away instead of waiting for the connection to time out.
            if not self.power_down:
                self.power_down = True
                changed = True

        elif power == "on" and self.power_down:
            self.power_down = False
            changed = True

        if "status" in message:
            status = message["status"]

            if status is not None:
                status = str(status)

                if self._is_ignored_status(status):
                    if self.data.get("status") != "idle":
                        self.data["status"] = "idle"
                        changed = True

                elif self.data.get("status") != status:
                    self.data["status"] = status
                    changed = True

        if "cpu_temperature" in message:
            temperature = message["cpu_temperature"]

            if temperature is not None:
                if (
                    self.data.get("cpu_temperature")
                    != temperature
                ):
                    self.data["cpu_temperature"] = temperature
                    changed = True

        self._set_online(True)

        if changed:
            self._notify_listeners()

    @staticmethod
    def _is_ignored_status(status: str) -> bool:
        """Return True for known non-game processes."""

        normalized = status.strip().lower()

        return normalized in {
            "jellyfin",
        }

    def _set_online(self, online: bool) -> None:
        """Update online state."""

        if self.online == online:
            return

        self.online = online

        if not online:
            # Forget the last readings (and any announced sleep) so nothing
            # keeps showing stale values while the PC is off.
            self.data = {}
            self.power_down = False

        _LOGGER.debug(
            "Bazzite online state changed to %s",
            online,
        )

        self._notify_listeners()

    def async_add_listener(self, callback) -> None:
        """Add an entity listener."""

        if callback not in self.listeners:
            self.listeners.append(callback)

    def async_remove_listener(self, callback) -> None:
        """Remove an entity listener."""

        if callback in self.listeners:
            self.listeners.remove(callback)

    def _notify_listeners(self) -> None:
        """Notify entities of a state change."""

        for callback in tuple(self.listeners):
            callback()
