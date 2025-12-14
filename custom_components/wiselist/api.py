"""API WebSocket per WiseList con supporto Settings."""
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_LIST_NAME, CONF_RARE_DAYS

EVENT_WISELIST_UPDATED = "wiselist_updated"

def async_setup_api(hass: HomeAssistant):
    """Configura le API WebSocket."""
    websocket_api.async_register_command(hass, websocket_handle_get_lists)
    websocket_api.async_register_command(hass, websocket_handle_items)
    websocket_api.async_register_command(hass, websocket_handle_add)
    websocket_api.async_register_command(hass, websocket_handle_update)
    websocket_api.async_register_command(hass, websocket_handle_clear)
    websocket_api.async_register_command(hass, websocket_handle_remove)


def get_list_instance(hass, list_id):
    """Recupera l'oggetto WiseListData specifico per l'ID richiesto."""
    domain_data = hass.data.get(DOMAIN, {})
    return domain_data.get(list_id)


@callback
@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/get_lists",
})
def websocket_handle_get_lists(hass, connection, msg):
    """Restituisce l'elenco di tutte le liste configurate."""
    entries = hass.config_entries.async_entries(DOMAIN)
    lists = []
    for entry in entries:
        lists.append({
            "id": entry.entry_id,
            # MODIFICA: Usiamo entry.title per riflettere le rinomine fatte dall'utente nell'UI
            "name": entry.title 
        })
    connection.send_result(msg["id"], lists)


@callback
@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/items",
    vol.Required("list_id"): str,
})
def websocket_handle_items(hass, connection, msg):
    """Invia gli oggetti E LE IMPOSTAZIONI di una specifica lista."""
    list_id = msg["list_id"]
    instance = get_list_instance(hass, list_id)
    
    # Recuperiamo anche la configurazione dell'entry (per i giorni rari)
    entry = hass.config_entries.async_get_entry(list_id)
    
    if not instance or not entry:
        connection.send_error(msg["id"], "list_not_found", "Lista non trovata")
        return
        
    # MODIFICA: Cerchiamo prima nelle opzioni (modificabili), poi nei dati (setup iniziale)
    rare_days = entry.options.get(CONF_RARE_DAYS, entry.data.get(CONF_RARE_DAYS, 180))

    # Risposta Arricchita
    connection.send_result(msg["id"], {
        "items": instance.items,
        "settings": {
            "rare_days": rare_days
        }
    })


@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/add",
    vol.Required("list_id"): str,
    vol.Required("name"): str,
})
@websocket_api.async_response
async def websocket_handle_add(hass, connection, msg):
    """Aggiunge un oggetto."""
    instance = get_list_instance(hass, msg["list_id"])
    if not instance:
        connection.send_error(msg["id"], "list_not_found", "Lista non trovata")
        return

    item = await instance.async_add(msg["name"])
    connection.send_result(msg["id"], item)
    connection.send_event(EVENT_WISELIST_UPDATED, {
        "action": "add", 
        "item": item, 
        "list_id": msg["list_id"]
    })


@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/update",
    vol.Required("list_id"): str,
    vol.Required("item_id"): str,
    vol.Optional("name"): str,
    vol.Optional("complete"): bool,
})
@websocket_api.async_response
async def websocket_handle_update(hass, connection, msg):
    """Aggiorna un oggetto."""
    msg_id = msg.pop("id")
    list_id = msg.pop("list_id")
    item_id = msg.pop("item_id")
    msg.pop("type")
    
    instance = get_list_instance(hass, list_id)
    if not instance:
        connection.send_error(msg_id, "list_not_found", "Lista non trovata")
        return

    current_item = next((i for i in instance.items if i["id"] == item_id), None)
    data_to_update = msg

    if current_item and msg.get("complete") is True:
        current_count = current_item.get("counter", 0)
        data_to_update["counter"] = current_count + 1
        data_to_update["last_updated"] = dt_util.now().isoformat()

    item = await instance.async_update(item_id, data_to_update)
    
    connection.send_result(msg_id, item)
    connection.send_event(EVENT_WISELIST_UPDATED, {
        "action": "update", 
        "item": item, 
        "list_id": list_id
    })


@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/clear_completed",
    vol.Required("list_id"): str,
})
@websocket_api.async_response
async def websocket_handle_clear(hass, connection, msg):
    """Pulisce i completati."""
    instance = get_list_instance(hass, msg["list_id"])
    if not instance:
        connection.send_error(msg["id"], "list_not_found", "Lista non trovata")
        return

    await instance.async_clear_completed()
    connection.send_result(msg["id"])
    connection.send_event(EVENT_WISELIST_UPDATED, {
        "action": "clear", 
        "list_id": msg["list_id"]
    })


@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/remove",
    vol.Required("list_id"): str,
    vol.Required("item_id"): str,
})
@websocket_api.async_response
async def websocket_handle_remove(hass, connection, msg):
    """Rimuove un oggetto."""
    instance = get_list_instance(hass, msg["list_id"])
    if not instance:
        connection.send_error(msg["id"], "list_not_found", "Lista non trovata")
        return

    await instance.async_remove(msg["item_id"])
    connection.send_result(msg["id"])
    connection.send_event(EVENT_WISELIST_UPDATED, {
        "action": "remove", 
        "item_id": msg["item_id"],
        "list_id": msg["list_id"]
    })