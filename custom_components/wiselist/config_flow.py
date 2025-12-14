"""Flusso di configurazione per WiseList."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_LIST_NAME, CONF_RARE_DAYS, TITLE

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG) # Impostiamo il livello di log a DEBUG

# Schema per la creazione iniziale
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LIST_NAME, default="Lista della Spesa"): str,
        vol.Required(CONF_RARE_DAYS, default=180): int,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any], current_entry_id: str | None = None) -> dict[str, Any]:
    """Valida l'input dell'utente, inclusa la verifica del nome duplicato."""
    _LOGGER.debug("DEBUG: Inizio validazione input.")
    list_name = data[CONF_LIST_NAME]
    
    # Controlla se esiste già una lista con lo stesso nome (escludendo l'entry corrente se presente)
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id != current_entry_id and entry.data.get(CONF_LIST_NAME) == list_name:
            raise AlreadyConfigured(f"La lista '{list_name}' è già configurata.")

    return {"title": list_name}


class WiseListConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestore del flusso di configurazione principale."""

    VERSION = 1
    # Impedisce la ridenominazione tramite il menu a tre puntini di Home Assistant
    _supports_rename = False

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Crea il flusso delle opzioni (pulsante Configura)."""
        _LOGGER.debug("DEBUG: Richiesta di creazione WiseListOptionsFlowHandler.")
        return WiseListOptionsFlowHandler(config_entry)


    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Gestisce il passo iniziale di creazione."""
        _LOGGER.debug("DEBUG: Avvio async_step_user.")
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # La validazione iniziale non ha un current_entry_id
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except AlreadyConfigured:
                errors["base"] = "name_exists"
            except Exception:
                _LOGGER.exception("Errore inatteso nel config flow")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={"title": TITLE}
        )


class WiseListOptionsFlowHandler(config_entries.OptionsFlow):
    """Gestore delle opzioni (Modifica configurazione esistente)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Inizializza le opzioni."""
        _LOGGER.debug("DEBUG: WiseListOptionsFlowHandler INIZIALIZZATO.")
        super().__init__()

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Gestisce il modulo delle opzioni (nome lista e giorni rari)."""
        _LOGGER.debug("DEBUG: Avvio async_step_init per le opzioni.")
        errors: dict[str, str] = {}
        
        # Recupera i dati correnti (sia data che options, options sovrascrive data)
        current_data = {**self.config_entry.data, **self.config_entry.options}
        
        current_list_name = current_data.get(CONF_LIST_NAME, "Lista della Spesa")
        current_rare_days = current_data.get(CONF_RARE_DAYS, 180)

        if user_input is not None:
            try:
                # 1. Validazione per nome duplicato
                await validate_input(self.hass, user_input, self.config_entry.entry_id)
                
                new_list_name = user_input[CONF_LIST_NAME]
                new_rare_days = user_input[CONF_RARE_DAYS]
                
                # 2. Separazione delle modifiche:
                # Se il nome della lista è cambiato, aggiorna i dati (data) e il titolo dell'entry
                if new_list_name != current_list_name:
                    _LOGGER.debug(f"DEBUG: Aggiorno nome lista da '{current_list_name}' a '{new_list_name}'")
                    
                    # Aggiorna il nome nel 'data' dell'entry
                    updated_data = {
                        CONF_LIST_NAME: new_list_name,
                        CONF_RARE_DAYS: self.config_entry.data.get(CONF_RARE_DAYS, 180) # Mantieni il vecchio valore se non è cambiato
                    }
                    
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data=updated_data,
                        title=new_list_name,
                    )
                
                # 3. Aggiorna le opzioni (options)
                # Le opzioni servono per le impostazioni che possono cambiare dinamicamente.
                # In questo caso, salviamo i giorni rari NELLE OPZIONI, 
                # e il nome della lista NEI DATI (dopo il controllo precedente).
                new_options = {
                    CONF_RARE_DAYS: new_rare_days
                }

                _LOGGER.debug(f"DEBUG: Opzioni salvate: {new_options}")
                return self.async_create_entry(title="", data=new_options)

            except AlreadyConfigured:
                errors["base"] = "name_exists"
            except Exception:
                _LOGGER.exception("Errore inatteso nel flusso delle opzioni")
                errors["base"] = "unknown"


        options_schema = vol.Schema({
            vol.Required(CONF_LIST_NAME, default=current_list_name): str,
            vol.Required(CONF_RARE_DAYS, default=current_rare_days): int,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
            description_placeholders={"title": "Impostazioni WiseList"}
        )


class AlreadyConfigured(HomeAssistantError):
    """Errore: Configurazione già esistente."""