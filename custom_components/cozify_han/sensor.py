import logging
import async_timeout
from datetime import timedelta
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

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Aseta sensorit käyttöliittymästä tehdyn asennuksen perusteella."""
    host = entry.data[CONF_HOST]
    url = f"http://{host}/meter"

    async def async_update_data():
        """Hae data Cozify HAN -laitteesta."""
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status != 200:
                            _LOGGER.error("Virhe haettaessa dataa: %s", response.status)
                            return None
                        return await response.json()
        except Exception as err:
            _LOGGER.error("Yhteysvirhe Cozify HAN -laitteeseen: %s", err)
            return None

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="cozify_han_data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5),
    )

    await coordinator.async_config_entry_first_refresh()

    sensors = [
        CozifyEnergySensor(coordinator, "ic", "Total Power Imported", UnitOfEnergy.KILO_WATT_HOUR),
        CozifyEnergySensor(coordinator, "ec", "Total Power Exported", UnitOfEnergy.KILO_WATT_HOUR),
        CozifyArraySensor(coordinator, "p", 0, "Power Total", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, "p", 1, "Power L1", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, "p", 2, "Power L2", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, "p", 3, "Power L3", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, "u", 0, "Voltage L1", UnitOfElectricPotential.VOLT),
        CozifyArraySensor(coordinator, "u", 1, "Voltage L2", UnitOfElectricPotential.VOLT),
        CozifyArraySensor(coordinator, "u", 2, "Voltage L3", UnitOfElectricPotential.VOLT),
        CozifyArraySensor(coordinator, "i", 0, "Current L1", UnitOfElectricCurrent.AMPERE),
        CozifyArraySensor(coordinator, "i", 1, "Current L2", UnitOfElectricCurrent.AMPERE),
        CozifyArraySensor(coordinator, "i", 2, "Current L3", UnitOfElectricCurrent.AMPERE),
        CozifyArraySensor(coordinator, "r", 0, "Reactive Power Total", "var"),
        CozifyArraySensor(coordinator, "r", 1, "Reactive Power L1", "var"),
        CozifyArraySensor(coordinator, "r", 2, "Reactive Power L2", "var"),
        CozifyArraySensor(coordinator, "r", 3, "Reactive Power L3", "var"),
    ]
    
    async_add_entities(sensors)

class CozifyEnergySensor(CoordinatorEntity, SensorEntity):
    """Energiasensori (kWh)."""
    def __init__(self, coordinator, key, name, unit):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"cozify_han_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return float(self.coordinator.data.get(self._key, 0))

class CozifyArraySensor(CoordinatorEntity, SensorEntity):
    """Array-pohjainen sensori (W, V, A)."""
    def __init__(self, coordinator, key, index, name, unit):
        super().__init__(coordinator)
        self._key = key
        self._index = index
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"cozify_han_{key}_{index}"
        self._attr_native_unit_of_measurement = unit
        
        if unit == UnitOfPower.WATT:
            self._attr_device_class = SensorDeviceClass.POWER
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == UnitOfElectricPotential.VOLT:
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        elif unit == UnitOfElectricCurrent.AMPERE:
            self._attr_device_class = SensorDeviceClass.CURRENT

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        arr = self.coordinator.data.get(self._key, [])
        if isinstance(arr, list) and len(arr) > self._index:
            return float(arr[self._index])
        return 0
