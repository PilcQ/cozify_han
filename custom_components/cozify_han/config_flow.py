import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from .const import DOMAIN

class CozifyHanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Cozify HAN asennusvalikko."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Pyydetään käyttäjältä IP-osoite."""
        if user_input is not None:
            # Luodaan entry. Title on se, mikä näkyy integraatiolistassa.
            return self.async_create_entry(
                title=f"Cozify HAN ({user_input[CONF_HOST]})", 
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
            }),
        )
