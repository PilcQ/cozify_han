"""Cozify HAN -integraatio."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Aseta integraatio käyttöliittymästä."""
    # Tämä rivi käskee HA:ta lataamaan sensor.py:n
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Poista integraatio."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
