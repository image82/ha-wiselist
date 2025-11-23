"""Componente WiseList per Home Assistant."""
import logging
import uuid
import json
import os

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util
from homeassistant.components.http import StaticPathConfig

from .api import async_setup_api

_LOGGER = logging.getLogger(__name__)

DOMAIN = "wiselist"
PERSISTENCE = ".wiselist.json"

# Definiamo dove si trova la card
CARD_FILENAME = "wiselist-card.js"
CARD_URL = "/wiselist/wiselist-card.js"

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WiseList component."""
    
    # 1. Registra la risorsa statica per la Card (Magia HACS)
    component_path = hass.config.path(f"custom_components/{DOMAIN}")
    card_path = os.path.join(component_path, CARD_FILENAME)
    
    if os.path.exists(card_path):
        await hass.http.async_register_static_paths([
            StaticPathConfig(CARD_URL, card_path, False)
        ])
    
    # 2. Setup Dati
    data = hass.data[DOMAIN] = WiseListData(hass)
    await data.async_load()
    data.fix_permissions()

    # 3. Setup API
    async_setup_api(hass)

    # 4. Registrazione Servizi
    async def handle_add_item(call: ServiceCall):
        name = call.data.get("name", "Oggetto Test")
        await data.async_add(name)

    async def handle_remove_item(call: ServiceCall):
        name = call.data.get("name")
        item = next((i for i in data.items if i["name"] == name), None)
        if item:
            await data.async_remove(item["id"])

    async def handle_update_item(call: ServiceCall):
        name = call.data.get("name")
        complete = call.data.get("complete", True) 
        item = next((i for i in data.items if i["name"] == name), None)
        if item:
            update_data = {"complete": complete}
            if complete:
                current_count = item.get("counter", 0)
                update_data["counter"] = current_count + 1
                update_data["last_updated"] = dt_util.now().isoformat()
            await data.async_update(item["id"], update_data)

    async def handle_clear_completed(call: ServiceCall):
        await data.async_clear_completed()

    # I servizi ora si chiamano wiselist.add_item, ecc.
    hass.services.async_register(DOMAIN, "add_item", handle_add_item)
    hass.services.async_register(DOMAIN, "remove_item", handle_remove_item)
    hass.services.async_register(DOMAIN, "update_item_status", handle_update_item)
    hass.services.async_register(DOMAIN, "clear_completed", handle_clear_completed)

    return True


class WiseListData:
    """Classe per gestire la lista e il salvataggio su file."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.items = []

    def fix_permissions(self):
        path = self.hass.config.path(PERSISTENCE)
        if os.path.exists(path):
            try:
                os.chmod(path, 0o666)
            except OSError:
                _LOGGER.warning("Impossibile cambiare i permessi del file database")

    async def async_add(self, name):
        item = {
            "name": name,
            "id": uuid.uuid4().hex,
            "complete": False,
            "counter": 0,
            "last_updated": None
        }
        self.items.append(item)
        await self.async_save()
        return item

    async def async_update(self, item_id, info):
        item = next((i for i in self.items if i["id"] == item_id), None)
        if item is None:
            return None
        item.update(info)
        await self.async_save()
        return item

    async def async_remove(self, item_id):
        self.items = [item for item in self.items if item["id"] != item_id]
        await self.async_save()

    async def async_clear_completed(self):
        self.items = [item for item in self.items if not item["complete"]]
        await self.async_save()

    async def async_load(self):
        def load():
            path = self.hass.config.path(PERSISTENCE)
            if not os.path.exists(path):
                return []
            try:
                with open(path, "r", encoding="utf-8") as fobj:
                    return json.load(fobj)
            except (ValueError, OSError):
                _LOGGER.error("Could not load WiseList data")
                return []
        self.items = await self.hass.async_add_executor_job(load)

    async def async_save(self):
        def save():
            path = self.hass.config.path(PERSISTENCE)
            try:
                with open(path, "w", encoding="utf-8") as fobj:
                    json.dump(self.items, fobj, indent=2, ensure_ascii=False)
                try:
                    os.chmod(path, 0o666)
                except OSError:
                    pass
            except OSError:
                _LOGGER.error("Could not save WiseList data")
        await self.hass.async_add_executor_job(save)
