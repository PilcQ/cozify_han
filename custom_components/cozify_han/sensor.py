import logging
from datetime import timedelta
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

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
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import async_timeout

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Asetetaan sensorit perustuen laitteen /meter vastaukseen."""
    host = entry.data[CONF_HOST]
    session = async_get_clientsession(hass)

    # 1. Haetaan laitteen tiedot osoitteesta /han
    device_info_data = {}
    try:
        async with async_timeout.timeout(5):
            response = await session.get(f"http://{host}/han", ssl=False)
            if response.status == 200:
                device_info_data = await response.json()
    except Exception as err:
        _LOGGER.warning("Laitetietojen haku /han epäonnistui: %s", err)

    # 2. Päivitysmetodi: Haetaan data osoitteesta /meter
    async def async_update_data():
        try:
            async with async_timeout.timeout(5):
                response = await session.get(f"http://{host}/meter", ssl=False)
                if response.status != 200:
                    raise UpdateFailed(f"Virheellinen statuskoodi: {response.status}")
                return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Yhteysvirhe: {err}")

    scan_interval = entry.options.get("update_interval", 5)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Cozify HAN sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    # Määritellään kaikki sensorit
    sensors = [
        # Energia (kWh)
        CozifyEnergySensor(coordinator, entry, "ic", "Total Power Imported", UnitOfEnergy.KILO_WATT_HOUR, device_info_data),
        CozifyEnergySensor(coordinator, entry, "ec", "Total Power Exported", UnitOfEnergy.KILO_WATT_HOUR, device_info_data),
        
        # Tehot (p-lista: [Total, L1, L2, L3])
        CozifyArraySensor(coordinator, entry, "p", 0, "Power Total", UnitOfPower.WATT, device_info_data),
        CozifyArraySensor(coordinator, entry, "p", 1, "Power L1", UnitOfPower.WATT, device_info_data),
        CozifyArraySensor(coordinator, entry, "p", 2, "Power L2", UnitOfPower.WATT, device_info_data),
        CozifyArraySensor(coordinator, entry, "p", 3, "Power L3", UnitOfPower.WATT, device_info_data),
        
        # Jännitteet (u-lista: [L1, L2, L3])
        CozifyArraySensor(coordinator, entry, "u", 0, "Voltage L1", UnitOfElectricPotential.VOLT, device_info_data),
        CozifyArraySensor(coordinator, entry, "u", 1, "Voltage L2", UnitOfElectricPotential.VOLT, device_info_data),
        CozifyArraySensor(coordinator, entry, "u", 2, "Voltage L3", UnitOfElectricPotential.VOLT, device_info_data),
        
        # Virrat (i-lista: [L1, L2, L3])
        CozifyArraySensor(coordinator, entry, "i", 0, "Current L1", UnitOfElectricCurrent.AMPERE, device_info_data),
        CozifyArraySensor(coordinator, entry, "i", 1, "Current L2", UnitOfElectricCurrent.AMPERE, device_info_data),
        CozifyArraySensor(coordinator, entry, "i", 2, "Current L3", UnitOfElectricCurrent.AMPERE, device_info_data),

        # Reaktiivinen teho (r-lista: [Total, L1, L2, L3])
        CozifyArraySensor(coordinator, entry, "r", 0, "Reactive Power Total", "var", device_info_data),

        # Päivittäiset maksimit ja diagnostiikka
        CozifyMaxCurrentSensor(coordinator, entry, "Current Max L1", 0, device_info_data),
        CozifyMaxCurrentSensor(coordinator, entry, "Current Max L2", 1, device_info_data),
        CozifyMaxCurrentSensor(coordinator, entry, "Current Max L3", 2, device_info_data),
        CozifyPeakPowerSensor(coordinator, entry, device_info_data),
        CozifyTimestampSensor(coordinator, entry, device_info_data),
    CozifyDiagnosticSensor(coordinator, entry, "MAC Address", device_info_data.get("mac"), device_info_data),
        CozifyDiagnosticSensor(coordinator, entry, "Serial Number", device_info_data.get("serial"), device_info_data),
        CozifyDiagnosticSensor(coordinator, entry, "IP Address", host, device_info_data)
    ]
    
    async_add_entities(sensors)


class CozifyBaseEntity(CoordinatorEntity):
    """Yhteinen kantaluokka kaikille Cozify-sensoreille."""

    def __init__(self, coordinator, entry, device_info_data=None):
        super().__init__(coordinator)
        self._entry = entry
        self._device_info_data = device_info_data or {}

    @property
    def device_info(self):
        """Palauttaa laitteen tiedot käyttäen /han osoitteesta saatuja tietoja."""
        return {
            "identifiers": {(DOMAIN, self._device_info_data.get("mac", self._entry.entry_id))},
            "name": self._device_info_data.get("name", "Cozify HAN"),
            "manufacturer": "Cozify",
            "model": self._device_info_data.get("model", "HAN Reader"),
            "sw_version": self._device_info_data.get("version"),
            "hw_version": self._device_info_data.get("serial"), # Sarjanumero tässä
            "configuration_url": f"http://{self._entry.data[CONF_HOST]}",
        }


class CozifyEnergySensor(CozifyBaseEntity, SensorEntity):
    """Energiasensori (kWh)."""
    def __init__(self, coordinator, entry, data_key, name, unit, device_info_data):
        super().__init__(coordinator, entry, device_info_data)
        self._data_key = data_key
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"{entry.entry_id}_{data_key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        if self.coordinator.data is None: return None
        try:
            return float(self.coordinator.data.get(self._data_key, 0))
        except (TypeError, ValueError):
            return None


class CozifyArraySensor(CozifyBaseEntity, SensorEntity):
    """Lukee arvoja JSON-listoista (u, i, p, r)."""
    def __init__(self, coordinator, entry, data_key, index, name, unit, device_info_data):
        super().__init__(coordinator, entry, device_info_data)
        self._data_key = data_key
        self._index = index
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"{entry.entry_id}_{data_key}_{index}"
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
        if unit == UnitOfPower.WATT:
            self._attr_device_class = SensorDeviceClass.POWER
        elif unit == UnitOfElectricPotential.VOLT:
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        elif unit == UnitOfElectricCurrent.AMPERE:
            self._attr_device_class = SensorDeviceClass.CURRENT

    @property
    def native_value(self):
        if self.coordinator.data is None: return None
        arr = self.coordinator.data.get(self._data_key)
        if isinstance(arr, list) and len(arr) > self._index:
            try:
                val = arr[self._index]
                return float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                return 0.0
        return 0.0


class CozifyMaxCurrentSensor(CozifyBaseEntity, SensorEntity):
    """Tallentaa päivän korkeimman ampeerilukeman vaiheittain."""
    def __init__(self, coordinator, entry, name, phase_index, device_info_data):
        super().__init__(coordinator, entry, device_info_data)
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"{entry.entry_id}_max_i_{phase_index}"
        self._phase_index = phase_index
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_device_class = SensorDeviceClass.CURRENT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._max_val = 0.0
        self._day = dt_util.now().day

    @property
    def native_value(self):
        if self.coordinator.data is None: return self._max_val
        now = dt_util.now()
        if now.day != self._day:
            self._max_val = 0.0
            self._day = now.day
        try:
            val = float(self.coordinator.data.get("i", [])[self._phase_index])
            if val > self._max_val: self._max_val = val
        except (IndexError, ValueError, TypeError): pass
        return self._max_val


class CozifyPeakPowerSensor(CozifyBaseEntity, SensorEntity):
    """Päivän huipputeho (W)."""
    def __init__(self, coordinator, entry, device_info_data):
        super().__init__(coordinator, entry, device_info_data)
        self._attr_name = "Cozify HAN Peak Power Day"
        self._attr_unique_id = f"{entry.entry_id}_peak_p"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._max_p = 0.0
        self._day = dt_util.now().day

    @property
    def native_value(self):
        if self.coordinator.data is None: return self._max_p
        now = dt_util.now()
        if now.day != self._day:
            self._max_p = 0.0
            self._day = now.day
        try:
            val = float(self.coordinator.data.get("p", [0])[0])
            if val > self._max_p: self._max_p = val
        except (IndexError, ValueError, TypeError): pass
        return self._max_p


class CozifyTimestampSensor(CozifyBaseEntity, SensorEntity):
    """Viimeisin päivitysaika."""
    def __init__(self, coordinator, entry, device_info_data):
        super().__init__(coordinator, entry, device_info_data)
        self._attr_name = "Cozify HAN Last Update"
        self._attr_unique_id = f"{entry.entry_id}_ts"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        if self.coordinator.data is None: return None
        try:
            return dt_util.utc_from_timestamp(float(self.coordinator.data.get("ts")))
        except (TypeError, ValueError): return None


class CozifyDiagnosticSensor(CozifyBaseEntity, SensorEntity):
    """Staattiset diagnostiikkatiedot."""
    def __init__(self, coordinator, entry, name, value, device_info_data):
        super().__init__(coordinator, entry, device_info_data)
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"{entry.entry_id}_{name.lower().replace(' ', '_')}"
        self._attr_native_value = value
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self._attr_native_value
