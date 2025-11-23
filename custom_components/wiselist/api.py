"""API WebSocket per WiseList."""
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

DOMAIN = "wiselist"
EVENT_WISELIST_UPDATED = "wiselist_updated"

def async_setup_api(hass: HomeAssistant):
    """Configura le API WebSocket."""
    websocket_api.async_register_command(hass, websocket_handle_items)
    websocket_api.async_register_command(hass, websocket_handle_add)
    websocket_api.async_register_command(hass, websocket_handle_update)
    websocket_api.async_register_command(hass, websocket_handle_clear)
    websocket_api.async_register_command(hass, websocket_handle_remove)


@callback
@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/items",
})
def websocket_handle_items(hass, connection, msg):
    connection.send_result(msg["id"], hass.data[DOMAIN].items)


@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/add",
    vol.Required("name"): str,
})
@websocket_api.async_response
async def websocket_handle_add(hass, connection, msg):
    item = await hass.data[DOMAIN].async_add(msg["name"])
    connection.send_result(msg["id"], item)
    connection.send_event(EVENT_WISELIST_UPDATED, {"action": "add", "item": item})


@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/update",
    vol.Required("item_id"): str,
    vol.Optional("name"): str,
    vol.Optional("complete"): bool,
})
@websocket_api.async_response
async def websocket_handle_update(hass, connection, msg):
    msg_id = msg.pop("id")
    item_id = msg.pop("item_id")
    msg.pop("type")
    
    current_items = hass.data[DOMAIN].items
    current_item = next((i for i in current_items if i["id"] == item_id), None)

    data_to_update = msg

    if current_item and msg.get("complete") is True:
        current_count = current_item.get("counter", 0)
        data_to_update["counter"] = current_count + 1
        data_to_update["last_updated"] = dt_util.now().isoformat()

    item = await hass.data[DOMAIN].async_update(item_id, data_to_update)
    
    connection.send_result(msg_id, item)
    connection.send_event(EVENT_WISELIST_UPDATED, {"action": "update", "item": item})


@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/clear_completed",
})
@websocket_api.async_response
async def websocket_handle_clear(hass, connection, msg):
    await hass.data[DOMAIN].async_clear_completed()
    connection.send_result(msg["id"])
    connection.send_event(EVENT_WISELIST_UPDATED, {"action": "clear"})


@websocket_api.websocket_command({
    vol.Required("type"): "wiselist/remove",
    vol.Required("item_id"): str,
})
@websocket_api.async_response
async def websocket_handle_remove(hass, connection, msg):
    await hass.data[DOMAIN].async_remove(msg["item_id"])
    connection.send_result(msg["id"])
    connection.send_event(EVENT_WISELIST_UPDATED, {
        "action": "remove",
        "item_id": msg["item_id"]
    })