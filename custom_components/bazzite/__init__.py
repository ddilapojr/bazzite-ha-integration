import asyncio

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import BazziteCoordinator


PLATFORMS = [
    "sensor",
    "binary_sensor",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Bazzite."""

    hass.data.setdefault(DOMAIN, {})

    coordinator = BazziteCoordinator(
        hass,
        entry,
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_start()

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    async def handle_send_command(call):
        command = call.data.get("command")

        await send_command_to_bazzite(
            hass,
            entry.data,
            command,
        )

    hass.services.async_register(
        DOMAIN,
        "send_command",
        handle_send_command,
    )

    return True


async def send_command_to_bazzite(
    hass: HomeAssistant,
    config: dict,
    command: str,
):
    """Send a command to the Bazzite server."""

    session = async_get_clientsession(hass)

    url = (
        f"http://{config['host']}:"
        f"{config['port']}/command"
    )

    try:
        async with session.post(
            url,
            json={"command": command},
            timeout=aiohttp.ClientTimeout(total=5),
        ) as response:
            return await response.text()

    except (
        aiohttp.ClientError,
        asyncio.TimeoutError,
    ):
        return None


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload Bazzite."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if not unload_ok:
        return False

    coordinator = hass.data[DOMAIN].get(
        entry.entry_id
    )

    if coordinator:
        await coordinator.async_stop()

    hass.data[DOMAIN].pop(
        entry.entry_id,
        None,
    )

    return True