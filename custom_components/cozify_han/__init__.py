from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Asetetaan integraatio config entryn perusteella."""
    
    # Rekisteröidään kuuntelija asetusten muutoksille
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Välitetään asennus sensor-alustalle
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Päivittää integraation kun asetuksia (Options) muutetaan."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Poistetaan integraatio."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
