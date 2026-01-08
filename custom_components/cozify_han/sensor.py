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
    """Asetetaan sensorit."""
    host = entry.data[CONF_HOST]
    session = async_get_clientsession(hass)

    # 1. Haetaan laitetiedot integraation käynnistyessä
    device_info_data = {}
    try:
        async with async_timeout.timeout(5):
            response = await session.get(f"http://{host}/han", ssl=False)
            if response.status == 200:
                device_info_data = await response.json()
    except Exception as err:
        _LOGGER.warning("Laitetietojen haku /han epäonnistui: %s", err)

    # 2. Päivitysmetodi koordinaattorille
    async def async_update_data():
        combined_data = {}
        try:
            async with async_timeout.timeout(10):
                # Reaaliaikainen mittaus
                resp_meter = await session.get(f"http://{host}/meter", ssl=False)
                combined_data["realtime"] = await resp_meter.json()
                
                # Konfiguraatiodata (Diagnostiikka)
                resp_conf = await session.get(f"http://{host}/configuration", ssl=False)
                combined_data["config"] = await resp_conf.json()
                
                return combined_data
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
        CozifyArraySensor(coordinator, entry, "r", 1, "Reactive Power L1", "var", device_info_data),
        CozifyArraySensor(coordinator, entry, "r", 2, "Reactive Power L2", "var", device_info_data),
        CozifyArraySensor(coordinator, entry, "r", 3, "Reactive Power L3", "var", device_info_data),

        CozifyHANConfigSensor(coordinator, entry, "v", "Firmware Version", None, None, EntityCategory.DIAGNOSTIC, device_info_data),
        CozifyHANConfigSensor(coordinator, entry, "fuse", "Main Fuse Size", UnitOfElectricCurrent.AMPERE, None, EntityCategory.DIAGNOSTIC, device_info_data),
        CozifyHANConfigSensor(coordinator, entry, "eth_mode", "Ethernet Mode", None, None, EntityCategory.DIAGNOSTIC, device_info_data),
        CozifyHANConfigSensor(coordinator, entry, "wifi_ssid", "WiFi SSID", None, None, EntityCategory.DIAGNOSTIC, device_info_data),
        CozifyHANConfigSensor(coordinator, entry, "wifi_mode", "WiFi Mode", None, None, EntityCategory.DIAGNOSTIC, device_info_data),
        CozifyHANConfigSensor(coordinator, entry, "eth_active", "Ethernet Active", None, None, EntityCategory.DIAGNOSTIC, device_info_data),
        CozifyHANConfigSensor(coordinator, entry, "wifi_active", "WiFi Active", None, None, EntityCategory.DIAGNOSTIC, device_info_data),
        CozifyHANConfigSensor(coordinator, entry, "price", "Fixed Electricity Price", "c/kWh", None, EntityCategory.DIAGNOSTIC, device_info_data),
        CozifyHANConfigSensor(coordinator, entry, "timezone", "Timezone", None, None, EntityCategory.DIAGNOSTIC, device_info_data),
        
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
            "configuration_url": f"http://{self._entry.data[CONF_HOST]}/meter",
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
        # Data on nyt 'realtime' -avaimen alla
        val = self.coordinator.data.get("realtime", {}).get(self._data_key)
        try:
            return float(val) if val is not None else None
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
        elif unit == "var":
            self._attr_device_class = SensorDeviceClass.REACTIVE_POWER

    @property
    def native_value(self):
        if self.coordinator.data is None: return None
        arr = self.coordinator.data.get("realtime", {}).get(self._data_key)
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
            val = float(self.coordinator.data.get("realtime", {}).get("i", [])[self._phase_index])
            if val > self._max_val: self._max_val = val
        except (IndexError, ValueError, TypeError): pass
        return self._max_val


class CozifyPeakPowerSensor(CozifyBaseEntity, SensorEntity):
    """Päivän huipputeho (W)."""
    def __init__(self, coordinator, entry, device_info_data):
        super().__init__(coordinator, entry, device_info_data)
        self._attr_name = "Cozify HAN Power MAX"
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
        # Nollataan huippu, jos päivä on vaihtunut
        if now.day != self._day:
            self._max_p = 0.0
            self._day = now.day
            
        try:
            # KORJATTU: Lisätty .data ja polku .get("realtime")
            realtime_data = self.coordinator.data.get("realtime", {})
            p_list = realtime_data.get("p", [0])
            val = float(p_list[0])
            
            if val > self._max_p: 
                self._max_p = val
        except (IndexError, ValueError, TypeError): 
            pass
            
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
        if not self.coordinator.data:
            return None
        
        # HAETAAN oikeasta lokerosta: realtime -> ts
        ts = self.coordinator.data.get("realtime", {}).get("ts")
        
        try:
            return dt_util.utc_from_timestamp(float(ts)) if ts else None
        except (TypeError, ValueError):
            return None


class CozifyDiagnosticSensor(CozifyBaseEntity, SensorEntity):
    def __init__(self, coordinator, entry, name, value, device_info_data):
        super().__init__(coordinator, entry, device_info_data)
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"{entry.entry_id}_{name.lower().replace(' ', '_')}"
        self._value = value # Käytetään sisäistä muuttujaa
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        return self._value
        
class CozifyHANConfigSensor(CozifyBaseEntity, SensorEntity):
    """Sensorit /configuration osoitteesta."""
    def __init__(self, coordinator, entry, key, name, unit, device_class, category, device_info_data):
        super().__init__(coordinator, entry, device_info_data)
        self._key = key
        self._attr_name = f"Cozify HAN {name}"
        self._attr_unique_id = f"{entry.entry_id}_conf_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_entity_category = category

    @property
    def native_value(self):
        if not self.coordinator.data: return None
        conf = self.coordinator.data.get("config", {})

        # Aikavyöhyke
        if self._key == "timezone": return conf.get("t")
        
        # Sähkön kiinteähinta Cozify HAN sovelluksesta asetettu (c/kWh)
        if self._key == "price": 
            try:
                return float(conf.get("p", 0))
            except (TypeError, ValueError):
                return 0.0
                
        if self._key == "eth_active": return conf.get("e", {}).get("e") is True
        if self._key == "wifi_active": return conf.get("w", {}).get("e") is True
        if self._key == "fuse": return conf.get("m", {}).get("f")
        if self._key == "eth_mode": return conf.get("e", {}).get("n", {}).get("m")
        if self._key == "wifi_ssid": return conf.get("w", {}).get("s")
        if self._key == "wifi_mode": return conf.get("w", {}).get("n", {}).get("m")
        if self._key == "v": return conf.get("v")
        
        return conf.get(self._key)
