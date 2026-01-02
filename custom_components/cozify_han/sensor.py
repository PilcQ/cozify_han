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
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Aseta sensorit (YAML-konfiguraation kautta tai integraationa)."""
    
    # Haetaan IP-osoite konfiguraatiosta
    host = config.get(CONF_HOST)
    
    # Muodostetaan URL dynaamisesti (alkuperäinen polku oli /meter) 
    url = f"http://{host}/meter"

    async def async_update_data():
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                async with session.get(url) as response:
                    return await response.json()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="cozify_han_data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5), # Sama kuin scan_interval 
    )

    await coordinator.async_config_entry_first_refresh()

    sensors = [
        CozifyEnergySensor(coordinator, "ic", "Total Power Imported", UnitOfEnergy.KILO_WATT_HOUR), [cite: 26]
        CozifyEnergySensor(coordinator, "ec", "Total Power Exported", UnitOfEnergy.KILO_WATT_HOUR), [cite: 2]
        # Tehosensorit (pi-lista) [cite: 7-11]
        CozifyArraySensor(coordinator, "pi", 0, "Consumption Power Total", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, "pi", 1, "Consumption Power L1", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, "pi", 2, "Consumption Power L2", UnitOfPower.WATT),
        CozifyArraySensor(coordinator, "pi", 3, "Consumption Power L3", UnitOfPower.WATT),
    ]
    
    async_add_entities(sensors)

class CozifyEnergySensor(CoordinatorEntity, SensorEntity):
    """Sähköenergian kokonaislukemat (ic, ec)."""
    def __init__(self, coordinator, key, name, unit):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Cozify HAN {name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        return float(self.coordinator.data.get(self._key, 0))

class CozifyArraySensor(CoordinatorEntity, SensorEntity):
    """Listamuotoiset arvot (pi, pe, p, u, i).""" [cite: 27]
    def __init__(self, coordinator, key, index, name, unit):
        super().__init__(coordinator)
        self._key = key
        self._index = index
        self._attr_name = f"Cozify HAN {name}"
        self._attr_native_unit_of_measurement = unit
        if unit == UnitOfPower.WATT:
            self._attr_device_class = SensorDeviceClass.POWER

    @property
    def native_value(self):
        arr = self.coordinator.data.get(self._key, [])
        if len(arr) > self._index:
            return float(arr[self._index])
        return 0
# sensor.py (alkuosa säilyy samana kuin aiemmin)

async def async_setup_entry(hass, entry, async_add_entities):
    """Aseta sensorit Config Entryn perusteella."""
    config = entry.data
    host = config[CONF_HOST]
    url = f"http://{host}/meter"

    # Tähän tulee sama Coordinator-logiikka kuin aiemmin viestissäni
    # Mutta se käyttää nyt tätä dynaamista URL-osoitetta
    
    # ... (coordinator-koodi) ...
    
    # async_add_entities(sensors)
