"""Inizializzazione dell'integrazione WiseList."""
import logging
import os
import json
import uuid
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import DOMAIN as LOVELACE_DOMAIN
from homeassistant.components.lovelace.resources import ResourceStorageCollection

from .const import DOMAIN, CONF_LIST_NAME, TITLE

from .api import async_setup_api

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "wiselist-card.js"
CARD_URL = f"/{DOMAIN}/card.js"
LEGACY_PERSISTENCE = ".wiselist.json"
PLATFORMS: list[str] = [] 


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configura l'integrazione WiseList."""
    hass.data.setdefault(DOMAIN, {})

    # Registra risorse (card.js)
    component_path = hass.config.path(f"custom_components/{DOMAIN}")
    card_path = os.path.join(component_path, CARD_FILENAME)
    
    if os.path.exists(card_path):
        await hass.http.async_register_static_paths([
            StaticPathConfig(CARD_URL, card_path, False)
        ])
        
        try:
            if LOVELACE_DOMAIN in hass.data:
                resources: ResourceStorageCollection = hass.data[LOVELACE_DOMAIN]["resources"]
                if not resources.loaded:
                    await resources.async_load()
                found = any(item["url"] == CARD_URL for item in resources.async_items())
                if not found:
                    await resources.async_create_item({
                        "res_type": "module",
                        "url": CARD_URL,
                    })
                    _LOGGER.info("Risorsa WiseList aggiunta automaticamente a Lovelace")
        except Exception as e:
            _LOGGER.warning(f"Impossibile registrare automaticamente la risorsa WiseList: {e}")
            
    async_setup_api(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura l'istanza di WiseList da una Config Entry."""
    list_name = entry.data.get(CONF_LIST_NAME)
    entry_id = entry.entry_id
    
    filename = f".wiselist_{entry_id}.json"
    new_db_path = hass.config.path(filename)
    legacy_db_path = hass.config.path(LEGACY_PERSISTENCE)

    # Migrazione vecchio DB
    if os.path.exists(legacy_db_path) and not os.path.exists(new_db_path):
        try:
            os.rename(legacy_db_path, new_db_path)
            _LOGGER.info(f"MIGRAZIONE SUCCESSO: Il vecchio database è stato rinominato in {filename}")
        except OSError as err:
            _LOGGER.error(f"Errore durante la migrazione del database: {err}")

    data_instance = WiseListData(hass, filename)
    await data_instance.async_load()
    data_instance.fix_permissions()

    hass.data[DOMAIN][entry_id] = data_instance
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # --- NUOVO: Ascolta le modifiche alle opzioni (per aggiornare i giorni rari al volo) ---
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Scarica una Config Entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


# --- NUOVO: Listener per aggiornamento opzioni ---
async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Gestisce l'aggiornamento delle opzioni."""
    # Ricarica l'integrazione per applicare le nuove impostazioni
    await hass.config_entries.async_reload(entry.entry_id)


class WiseListData:
    """Classe per gestire la lista e il salvataggio su file."""

    def __init__(self, hass: HomeAssistant, filename: str) -> None:
        self.hass = hass
        self.filename = filename
        self.items = []

    def fix_permissions(self):
        path = self.hass.config.path(self.filename)
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
            path = self.hass.config.path(self.filename)
            if not os.path.exists(path):
                return []
            try:
                with open(path, "r", encoding="utf-8") as fobj:
                    return json.load(fobj)
            except (ValueError, OSError):
                _LOGGER.error(f"Could not load WiseList data form {self.filename}")
                return []
        self.items = await self.hass.async_add_executor_job(load)

    async def async_save(self):
        def save():
            path = self.hass.config.path(self.filename)
            try:
                with open(path, "w", encoding="utf-8") as fobj:
                    json.dump(self.items, fobj, indent=2, ensure_ascii=False)
                try:
                    os.chmod(path, 0o666)
                except OSError:
                    pass
            except OSError:
                _LOGGER.error(f"Could not save WiseList data to {self.filename}")
        await self.hass.async_add_executor_job(save)