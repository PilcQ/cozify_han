"""Asennusvalikko Cozify HAN -laitteelle."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from .const import DOMAIN

class CozifyHanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Käsittelee asennusvaiheet."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Kysy IP-osoitetta."""
        if user_input is not None:
            return self.async_create_entry(title="Cozify HAN Bridge", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
            }),
        )
