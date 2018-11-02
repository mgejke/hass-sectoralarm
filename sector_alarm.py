import logging
import asyncio
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle
from homeassistant.helpers import discovery

DOMAIN = 'sector_alarm'

DATA_SA = "SECTOR_ALARM"

_LOGGER = logging.getLogger(__name__)
DEPENDENCIES = []

REQUIREMENTS = ['aiohttp', 'asyncsector>=0.1.3']

CONF_EMAIL = 'email'
CONF_PASSWORD = 'password'
CONF_ALARM_ID = 'alarm_id'
CONF_THERMOMETERS = 'thermometers'
CONF_ALARM_PANEL = 'alarm_panel'
CONF_CODE_FORMAT = 'code_format'
CONF_CODE = "code"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN:
    vol.Schema(
        {
            vol.Required(CONF_EMAIL): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Required(CONF_ALARM_ID): cv.string,
            vol.Optional(CONF_CODE, default=''): cv.string,
            vol.Optional(CONF_CODE_FORMAT, default='^\\d{4,6}$'): cv.string,
            vol.Optional(CONF_THERMOMETERS, default=True): cv.boolean,
            vol.Optional(CONF_ALARM_PANEL, default=True): cv.boolean
        }),
},
                           extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):

    from asyncsector import AsyncSector

    session = async_get_clientsession(hass)

    async_sector = AsyncSector(session, config[DOMAIN].get(CONF_ALARM_ID),
                               config[DOMAIN].get(CONF_EMAIL),
                               config[DOMAIN].get(CONF_PASSWORD))

    if not await async_sector.login():
        _LOGGER.debug("sector_alarm failed to log in. Check your credentials.")
        return False

    panel = config[DOMAIN].get(CONF_ALARM_PANEL, False)
    thermometers = config[DOMAIN].get(CONF_THERMOMETERS, False)

    sector_data = SectorAlarmHub(async_sector, panel, thermometers)
    await sector_data.update()
    hass.data[DATA_SA] = sector_data

    if thermometers:
        discovery.load_platform(hass, 'sensor', DOMAIN, {}, config)

    if panel:
        discovery.load_platform(
            hass, 'alarm_control_panel', DOMAIN, {
                CONF_CODE_FORMAT: config[DOMAIN][CONF_CODE_FORMAT],
                CONF_CODE: config[DOMAIN][CONF_CODE]
            }, config)

    return True


class SectorAlarmHub(object):
    """ Get the latest data and update the states """

    def __init__(self, async_sector, panel=True, thermometers=True):
        self._async_sector = async_sector

        self._failed = False

        self._alarm_state = None
        self._changed_by = None

        self._termometers = {}

        self._update_tasks = []

        if panel:
            self._update_tasks.append(self._update_history)
        if thermometers:
            self._update_tasks.append(self._update_temperatures)

    async def get_thermometers(self):
        temps = await self._async_sector.get_status()

        if temps is None:
            _LOGGER.debug('Sector Alarm failed to fetch temperature sensors')
            return None

        return (temp['Label'] for temp in temps['Temperatures'])

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update(self):
        if self._failed:
            _LOGGER.error(
                "Sector Alarm failed previous update, trying to login again")
            self._failed = not await self._async_sector.login()
            if self._failed:
                self._alarm_state = 'unknown'
                _LOGGER.error("Sector Alarm failed to login")
                return

        results = await asyncio.gather(
            *[task() for task in self._update_tasks])
        if not any(results):
            self._failed = True
            return

    async def _update_history(self):
        history = await self._async_sector.get_history()
        _LOGGER.debug('Fetched history: %s', history)

        if not history:
            return False

        for history_entry in history['LogDetails']:
            if history_entry['EventType'] in [
                    'armed', 'partialarmed', 'disarmed'
            ]:
                self._alarm_state = history_entry['EventType']
                self._changed_by = history_entry['User']
                return True

        return False

    async def _update_temperatures(self):
        temperatures = await self._async_sector.get_temperatures()
        _LOGGER.debug('Fetched temperatures: %s', temperatures)

        if temperatures:
            self._termometers = {
                temperature['Label']: temperature['Temprature']
                for temperature in temperatures
            }

        return temperatures is not None

    async def arm_away(self, code=None):
        result = await self._async_sector.arm_away(code=code)
        if result:
            self._alarm_state = 'pending'
            self._changed_by = 'HA'
        return result

    async def arm_home(self, code=None):
        result = await self._async_sector.arm_home(code=code)
        if result:
            self._alarm_state = 'pending'
            self._changed_by = 'HA'
        return result

    async def disarm(self, code=None):
        result = await self._async_sector.disarm(code=code)
        if result:
            self._alarm_state = 'pending'
            self._changed_by = 'HA'
        return result

    @property
    def alarm_state(self):
        return self._alarm_state

    @property
    def alarm_changed_by(self):
        return self._changed_by

    @property
    def alarm_id(self):
        return self._async_sector.alarm_id

    def temperatures(self, name):
        return self._termometers.get(name, None)
