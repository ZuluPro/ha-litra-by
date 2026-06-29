import logging
from typing import Any

from litra_driver import LitraBeam  # Assuming this is your package class

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Litra Beam light platform from a config entry."""
    # Retrieve the MAC address stored during the config flow setup
    mac_address = config_entry.data["mac"]
    name = config_entry.title

    # Initialize your driver instance
    # Note: If your driver performs I/O during initialization,
    # it is ideal to wrap it in a hass.async_add_executor_job if it's blocking.
    lamp = LitraBeam(mac_address)

    async_add_entities([LitraBeamLight(lamp, name, mac_address)], update_before_add=True)


class LitraBeamLight(LightEntity):
    """Representation of a Litra Beam light over Bluetooth."""

    def __init__(self, lamp: LitraBeam, name: str, mac_address: str) -> None:
        """Initialize the light."""
        self._lamp = lamp
        self._attr_name = name
        self._attr_unique_id = f"litra_beam_{mac_address.replace(':', '').lower()}"

        # State tracking
        self._attr_is_on = False
        self._attr_brightness = 255

        # Litra Beam physical capabilities (2700K - 6500K)
        self._attr_min_color_temp_kelvin = 2700
        self._attr_max_color_temp_kelvin = 6500
        self._attr_color_temp_kelvin = 4000

        # Supported features
        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}
        self._attr_color_mode = ColorMode.COLOR_TEMP

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on and/or update its parameters."""
        # Check if brightness was requested (HA passes 0-255)
        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]

        # Check if color temperature was requested (HA passes Kelvin)
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._attr_color_temp_kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]

        # Convert HA brightness (0-255) to whatever your driver expects.
        # Assuming your driver might expect percentage (0-100) or 0-255.
        # Here we assume it handles 0-255 or you can map it: int((self._attr_brightness / 255) * 100)

        try:
            # We execute the blocking Bluetooth driver call in HA's thread pool executor
            # to avoid freezing the main Home Assistant event loop.
            await self.hass.async_add_executor_job(
                self._lamp.turn_on,
                self._attr_brightness,
                self._attr_color_temp_kelvin
            )
            self._attr_is_on = True
        except Exception as err:
            _LOGGER.error("Failed to turn on Litra Beam: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self.hass.async_add_executor_job(self._lamp.turn_off)
            self._attr_is_on = False
        except Exception as err:
            _LOGGER.error("Failed to turn off Litra Beam: %s", err)

    async def async_update(self) -> None:
        """Fetch latest state from the Litra Beam."""
        try:
            # If your driver supports reading the state back via Bluetooth:
            state = await self.hass.async_add_executor_job(self._lamp.get_state)
            if state:
                self._attr_is_on = state.get("is_on", False)
                self._attr_brightness = state.get("brightness", self._attr_brightness)
                self._attr_color_temp_kelvin = state.get("temperature", self._attr_color_temp_kelvin)
        except Exception as err:
            _LOGGER.debug("Could not update Litra Beam state (normal if polling is restricted): %s", err)
