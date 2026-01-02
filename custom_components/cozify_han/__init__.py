from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "cozify_han"
PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Aseta integraatio käyttöliittymästä lisätylle merkinnälle."""
    hass.data.setdefault(DOMAIN, {})
    
    # Tallennetaan asennustiedot muistiin
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Käynnistetään sensorit
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Poista integraatio (esim. kun käyttäjä poistaa sen UI:sta)."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
