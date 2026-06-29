import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN


class LitraBeamConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Litra Beam BT."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input["mac"].lower())
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get("name", "Litra Beam"),
                data=user_input
            )

        # Schéma du formulaire
        data_schema = vol.Schema({
            vol.Required("mac"): str,
            vol.Optional("name", default="Litra Beam"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
