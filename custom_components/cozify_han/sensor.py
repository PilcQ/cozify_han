import logging
from datetime import timedelta, datetime
import async_timeout
import aiohttp

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfPower,
    UnitOfEnergy,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    CONF_HOST,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Asetetaan sensorit entryn perusteella."""
    host = entry.data[CONF_HOST]
    url = f"http://{host}/meter"

    async def async_update_data():
        """Haetaan data laitteelta."""
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status != 200:
                            return None
                        return await response.json()
        except Exception as err:
            _LOGGER.error("Virhe haettaessa dataa: %s", err)
            return None

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="cozify_han_data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5),
    )

    await coordinator.async_config_entry_first_refresh()

    # Määritellään sensorit
    sensors = [
        CozifyEnergySensor(coordinator, entry, "ic", "Total Power Imported", UnitOfEnergy.KILO_WATT_HOUR),
        CozifyEnergySensor(coordinator, entry, "ec", "Total Power Exported", UnitOfEnergy.KILO_WATT_HOUR),
        CozifyArraySensor(coordinator, entry, "p", 0, "Power Total", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, entry, "p", 1, "Power L1", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, entry, "p", 2, "Power L2", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, entry, "p", 3, "Power L3", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, entry, "u", 0, "Voltage L1", UnitOfElectricPotential.VOLT),
        CozifyArraySensor(coordinator, entry, "u", 1, "Voltage L2", UnitOfElectricPotential.VOLT),
        CozifyArraySensor(coordinator, entry, "u", 2, "Voltage L3", UnitOfElectricPotential.VOLT),
        CozifyArraySensor(coordinator, entry, "i", 0, "Current L1", UnitOfElectricCurrent.AMPERE),
        CozifyArraySensor(coordinator, entry, "i", 1, "Current L2", UnitOfElectricCurrent.AMPERE),
        CozifyArraySensor(coordinator, entry, "i", 2, "Current L3", UnitOfElectricCurrent.AMPERE),
        CozifyArraySensor(coordinator, entry, "r", 0, "Reactive Power Total", "var"),
        CozifyArraySensor(coordinator, entry, "r", 1, "Reactive Power L1", "var"),
        CozifyArraySensor(coordinator, entry, "r", 2, "Reactive Power L2", "var"),
        CozifyArraySensor(coordinator, entry, "r", 3, "Reactive Power L3", "var"),
        CozifyPeakPowerSensor(coordinator, entry)
    ]
    
    async_add_entities(sensors)

class CozifyBaseEntity(CoordinatorEntity):
    """Yhteinen pohja kaikille Cozify-sensoreille laitehallintaa varten."""
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        """Linkittää sensorit samaan laitteeseen Device Registryssä."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Cozify HAN",
            "manufacturer": "Cozify",
            "model": "HAN-P1",
            "configuration_url": f"http://{self._entry.data[CONF_HOST]/meter}",
        }

class CozifyEnergySensor(CozifyBaseEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, name, unit):
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        if self.coordinator.data is None: return None
        return float(self.coordinator.data.get(self._key, 0))

class CozifyArraySensor(CozifyBaseEntity, SensorEntity):
    def __init__(self, coordinator, entry, key, index, name, unit):
        super().__init__(coordinator, entry)
        self._key = key
        self._index = index
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}_{index}"
        self._attr_native_unit_of_measurement = unit
        
        if unit == UnitOfPower.WATT:
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == UnitOfElectricPotential.VOLT:
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        elif unit == UnitOfElectricCurrent.AMPERE:
            self._attr_device_class = SensorDeviceClass.CURRENT
        elif unit == "var":
            self._attr_device_class = SensorDeviceClass.REACTIVE_POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        if self.coordinator.data is None: return None
        arr = self.coordinator.data.get(self._key, [])
        if isinstance(arr, list) and len(arr) > self._index:
            return float(arr[self._index])
        return 0

class CozifyPeakPowerSensor(CozifyBaseEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name = "Cozify HAN Peak Power Today"
        self._attr_unique_id = f"{entry.entry_id}_peak_power_today"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._peak_value = 0
        self._last_reset_day = datetime.now().day

    @property
    def native_value(self):
        if self.coordinator.data is None: return self._peak_value
        p_data = self.coordinator.data.get('p', [])
        if not p_data: return self._peak_value
            
        current_power = float(p_data[0])
        current_day = datetime.now().day

        if current_day != self._last_reset_day:
            self._peak_value = 0
            self._last_reset_day = current_day

        if current_power > self._peak_value:
            self._peak_value = current_power

        return self._peak_value
