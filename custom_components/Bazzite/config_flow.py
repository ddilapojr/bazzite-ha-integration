import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_DEFAULT_PORT,
    CONF_DEVICE_NAME,
    CONF_DEFAULT_DEVICE_NAME,
)


class BazziteConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a Bazzite config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input=None,
    ):
        """Handle the initial setup step."""

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_DEVICE_NAME],
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_NAME,
                    default=CONF_DEFAULT_DEVICE_NAME,
                ): str,

                vol.Required(
                    CONF_HOST,
                ): str,

                vol.Optional(
                    CONF_PORT,
                    default=CONF_DEFAULT_PORT,
                ): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )