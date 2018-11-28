import logging

import voluptuous as vol

from custom_components.moodo import MOODO_DEVICES, MoodoEntity
from homeassistant.components.fan import (SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH,
                                          FanEntity)
from homeassistant.const import (STATE_ON, STATE_OFF)


DEPENDENCIES = ['moodo']

FANS = ['box', 'slots']

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Fans for a MoodoBox device."""
    boxes = hass.data[MOODO_DEVICES]
    _LOGGER.debug("Fans: %s", FANS)

    sensors = []
    for sensor_type in FANS:
        for id in boxes:
            box = boxes[id]
            if sensor_type in ['box']:
                sensors.append(MoodoBoxFan(box, sensor_type))

            else: #slots
                for slot in box.slots:
                    sensors.append(MoodoBoxSlotFan(box, sensor_type, box.slots[slot]))

    add_devices(sensors, True)

class MoodoBoxFan(MoodoEntity, FanEntity):
    """A Fan implementation for MoodoBox device."""

    @property
    def is_on(self):
        """Return true if device is on."""
        return self.state == STATE_ON

    @property
    def state(self):
        """Return true if device is on."""
        return STATE_ON if self.box.status else STATE_OFF

    def turn_on(self, speed: str=None) -> None:
        """Turn on the entity."""
        self.box.turn_on()
        if speed is None:
            speed = SPEED_MEDIUM
        self.set_speed(speed)

    def turn_off(self) -> None:
        """Turn off the entity."""
        self.box.turn_off()
        self._speed = STATE_OFF

    def set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        self._speed = speed
        if speed == STATE_OFF:
            self.box.set_fan_speed(0)
        elif speed == SPEED_LOW:
            self.box.set_fan_speed(33)
        elif speed == SPEED_MEDIUM:
            self.box.set_fan_speed(66)
        elif speed == SPEED_HIGH:
            self.box.set_fan_speed(100)
        self.schedule_update_ha_state()

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return [STATE_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]
    
    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "fan_speed": self.box.fan_speed
        }

class MoodoBoxSlotFan(MoodoEntity, FanEntity):
    """A Fan implementation for every Module(slot) on a MoodoBox device."""
    
    def __init__(self, box, sensor_type, slot=None):
        """Initialize the MoodoBox entity."""
        super().__init__(box, sensor_type)
        self.box = box
        self.slot = slot
        self._sensor_type = sensor_type
        self._name = "{0} Capsule {1}".format(
            self.box.name,
            self.slot.scent)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self.state == STATE_ON

    @property
    def state(self):
        """Return the state of the sensor."""
        return STATE_ON if self.box.slots[self.slot.id].fan_active else STATE_OFF

    def turn_on(self, speed: str=None) -> None:
        """Turn on the entity."""
        self.box.slots[self.slot.id].turn_on()
        if speed is None:
            speed = SPEED_MEDIUM
        self.set_speed(speed)

    def turn_off(self) -> None:
        """Turn off the entity."""
        self.box.slots[self.slot.id].turn_off()
        self._speed = STATE_OFF

    def set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        self._speed = speed
        if speed == STATE_OFF:
            self.box.slots[self.slot.id].set_fan_speed(0)
        elif speed == SPEED_LOW:
            self.box.slots[self.slot.id].set_fan_speed(33)
        elif speed == SPEED_MEDIUM:
            self.box.slots[self.slot.id].set_fan_speed(66)
        elif speed == SPEED_HIGH:
            self.box.slots[self.slot.id].set_fan_speed(100)
        self.schedule_update_ha_state()

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return [STATE_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "fan_speed": self.box.slots[self.slot.id].fan_speed,
            "scent": self.box.slots[self.slot.id].scent
        }