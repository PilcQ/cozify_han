import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
import aiohttp
import async_timeout

DOMAIN = "cozify_han"

class CozifyHanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Käsittelee Cozify HAN integraation asennusta käyttöliittymässä."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Ensimmäinen vaihe: kysy IP-osoite."""
        errors = {}

        if user_input is not None:
            # Tässä voitaisiin tarkistaa, vastaako laite IP-osoitteessa
            valid = await self._test_connection(user_input[CONF_HOST])
            if valid:
                return self.async_create_entry(
                    title=f"Cozify HAN ({user_input[CONF_HOST]})",
                    data=user_input
                )
            else:
                errors["base"] = "cannot_connect"

        # Näytetään lomake
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
            }),
            errors=errors,
        )

    async def _test_connection(self, host):
        """Yritetään hakea dataa laitteesta varmistukseksi."""
        try:
            async with async_timeout.timeout(5):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{host}/meter") as response:
                        return response.status == 200
        except Exception:
            return False
