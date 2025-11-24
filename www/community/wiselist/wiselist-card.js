class WiseListCard extends HTMLElement {
    constructor() {
        super();
        this._items = []; 
        this._configData = this.loadConfig();
    }

    loadConfig() {
        const defaultConf = {
            rareThreshold: 180,
            sections: {
                active: true,
                recent: true,
                rare: false
            }
        };
        try {
            // Nuova chiave storage WiseList
            const stored = localStorage.getItem('wiselist_card_config');
            return stored ? { ...defaultConf, ...JSON.parse(stored) } : defaultConf;
        } catch (e) {
            return defaultConf;
        }
    }

    saveConfig() {
        localStorage.setItem('wiselist_card_config', JSON.stringify(this._configData));
    }

    set hass(hass) {
        this._hass = hass;
        if (!this.content) {
            this.initCard();
            this.fetchItems();
        }
    }

    initCard() {
        const card = document.createElement('ha-card');
        
        this.container = document.createElement('div');
        this.container.style.position = 'relative';

        this.headerDiv = document.createElement('div');
        this.headerDiv.className = 'card-header-custom';
        this.headerDiv.innerHTML = `
            <div class="header-title">WiseList</div>
            <ha-icon class="menu-btn" icon="mdi:dots-vertical"></ha-icon>
        `;
        this.headerDiv.querySelector('.menu-btn').addEventListener('click', () => this.openSettingsModal());

        this.content = document.createElement('div');
        this.content.style.padding = '0 16px 16px';
        
        this.inputContainer = document.createElement('div');
        this.inputContainer.style.position = 'relative'; 
        this.renderInputArea(); 

        this.listContainer = document.createElement('div');

        this.modal = document.createElement('div');
        this.modal.style.display = 'none'; 
        this.modal.className = 'modal-overlay';

        const style = document.createElement('style');
        style.textContent = `
            .card-header-custom { display: flex; justify-content: space-between; align-items: center; padding: 16px 16px 0 16px; margin-bottom: 16px; font-size: 20px; font-weight: 500; letter-spacing: 0.2px; color: var(--primary-text-color); }
            .menu-btn { color: var(--secondary-text-color); cursor: pointer; padding: 8px; border-radius: 50%; transition: background 0.2s; }
            .menu-btn:hover { background: rgba(127,127,127, 0.2); }
            .add-row { display: flex; margin-bottom: 20px; gap: 10px; }
            .add-input { flex-grow: 1; padding: 10px; border-radius: 4px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); font-size: 14px; }
            .add-btn { cursor: pointer; background: var(--primary-color); color: white; border: none; padding: 6px 14px; border-radius: 4px; font-weight: bold; font-size: 18px; }
            .suggestions-dropdown { position: absolute; top: 42px; left: 0; right: 50px; background: var(--card-background-color); border: 1px solid var(--divider-color); border-top: none; border-radius: 0 0 4px 4px; z-index: 100; max-height: 200px; overflow-y: auto; box-shadow: 0 4px 8px rgba(0,0,0,0.3); display: none; }
            .suggestions-dropdown.visible { display: block; }
            .suggestion-item { padding: 10px; border-bottom: 1px solid var(--divider-color); cursor: pointer; font-size: 14px; display: flex; justify-content: space-between; align-items: center; }
            .suggestion-item:hover { background: rgba(127,127,127, 0.1); }
            .suggestion-badge { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: var(--secondary-background-color); color: var(--secondary-text-color); text-transform: uppercase; }
            .section-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; user-select: none; margin: 24px 0 8px; border-bottom: 1px solid var(--divider-color); padding-bottom: 4px; }
            .section-title { font-size: 11px; text-transform: uppercase; color: var(--primary-color); font-weight: bold; letter-spacing: 0.5px; }
            .section-chevron { transition: transform 0.3s ease; color: var(--secondary-text-color); }
            .section-chevron.closed { transform: rotate(-90deg); }
            .section-content { overflow: hidden; transition: max-height 0.3s ease; }
            .section-content.closed { display: none; }
            .list-item { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--divider-color); }
            .list-item:hover { background: rgba(127,127,127, 0.1); }
            .checkbox { margin-right: 16px; cursor: pointer; width: 16px; height: 16px; accent-color: var(--primary-color); }
            .item-content { flex-grow: 1; cursor: pointer; display: flex; align-items: center; } 
            .item-name { font-size: 14px; }
            .item-name.completed { text-decoration: line-through; color: var(--secondary-text-color); }
            .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 9999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(4px); }
            .modal-box { background: var(--card-background-color); width: 90%; max-width: 400px; padding: 24px; border-radius: 28px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; gap: 16px; }
            .modal-header { font-size: 22px; font-weight: normal; color: var(--primary-text-color); margin-bottom: 8px; }
            .edit-row { display: flex; align-items: center; gap: 16px; background: var(--secondary-background-color); padding: 8px 16px; border-radius: 8px; }
            .edit-checkbox { width: 20px; height: 20px; cursor: pointer; accent-color: var(--primary-color); }
            .edit-input { flex-grow: 1; padding: 8px 0; border: none; background: transparent; color: var(--primary-text-color); font-size: 16px; outline: none; border-bottom: 2px solid transparent; transition: border-color 0.2s; }
            .edit-input:focus { border-bottom: 2px solid var(--primary-color); }
            .stats-container { display: flex; flex-direction: column; gap: 8px; padding-left: 10px; }
            .stat-row { font-size: 14px; color: var(--secondary-text-color); }
            .stat-val { font-weight: normal; color: var(--primary-text-color); margin-left: 5px; }
            .dialog-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 8px; }
            ha-button { --mdc-typography-button-text-transform: none; --mdc-theme-primary: var(--primary-color); }
        `;
        
        card.appendChild(style);
        card.appendChild(this.headerDiv);
        this.content.appendChild(this.inputContainer);
        this.content.appendChild(this.listContainer);
        this.container.appendChild(this.content);
        card.appendChild(this.modal);
        card.appendChild(this.container);
        this.appendChild(card);

        if(this._hass) {
            this._hass.connection.subscribeEvents((event) => {
                this.fetchItems();
            }, "wiselist_updated"); // Evento rinominato
        }
    }

    formatName(name) {
        if (!name) return "";
        return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
    }

    renderInputArea() {
        const addRow = document.createElement('div');
        addRow.className = 'add-row';
        const input = document.createElement('input');
        input.className = 'add-input';
        input.placeholder = "Cerca o aggiungi prodotto...";
        input.setAttribute("autocomplete", "off");
        const suggestions = document.createElement('div');
        suggestions.className = 'suggestions-dropdown';
        
        input.addEventListener("input", () => {
            const val = input.value.trim().toLowerCase();
            suggestions.innerHTML = '';
            if (val.length < 2) { suggestions.classList.remove('visible'); return; }
            const matches = this._items.filter(i => i.name.toLowerCase().includes(val));
            if (matches.length > 0) {
                matches.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'suggestion-item';
                    let statusText = "DA COMPRARE";
                    if (item.complete) {
                        const cutoffDate = new Date();
                        cutoffDate.setDate(cutoffDate.getDate() - this._configData.rareThreshold);
                        const lastUp = item.last_updated ? new Date(item.last_updated).getTime() : 0;
                        statusText = (lastUp > cutoffDate.getTime()) ? "RECENTE" : "RARO";
                    }
                    div.innerHTML = `<span>${item.name}</span><span class="suggestion-badge">${statusText}</span>`;
                    div.onclick = () => {
                        input.value = ''; suggestions.classList.remove('visible');
                        this.handleSuggestionClick(item);
                    };
                    suggestions.appendChild(div);
                });
                suggestions.classList.add('visible');
            } else { suggestions.classList.remove('visible'); }
        });

        input.addEventListener("blur", () => { setTimeout(() => { suggestions.classList.remove('visible'); }, 200); });
        input.addEventListener("keyup", (e) => { 
            if (e.key === "Enter") { this.addItem(input.value); input.value = ''; suggestions.classList.remove('visible'); }
        });

        const addBtn = document.createElement('button');
        addBtn.className = 'add-btn';
        addBtn.innerText = '+';
        addBtn.onclick = () => { this.addItem(input.value); input.value = ''; input.focus(); suggestions.classList.remove('visible'); };

        addRow.appendChild(input);
        addRow.appendChild(addBtn);
        this.inputContainer.appendChild(addRow);
        this.inputContainer.appendChild(suggestions);
    }

    async handleSuggestionClick(item) {
        if (item.complete) {
            const index = this._items.findIndex(i => i.id === item.id);
            if (index > -1) { this._items[index].complete = false; this.renderItems(this._items); }
            await this._hass.callWS({ type: 'wiselist/update', item_id: item.id, complete: false });
        } else { this.openDetail(item); }
    }

    async fetchItems() {
        this._isFetching = true;
        try {
            const items = await this._hass.callWS({ type: 'wiselist/items' });
            this._items = items;
            this.renderItems(this._items);
        } catch (err) { console.error("Errore recupero lista", err); } finally { this._isFetching = false; }
    }

    renderItems(items) {
        this.listContainer.innerHTML = '';
        const thresholdDays = this._configData.rareThreshold || 180;
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - thresholdDays);
        const cutoffTime = cutoffDate.getTime();

        const activeItems = items.filter(i => !i.complete).sort((a, b) => {
            const dateA = a.last_updated ? new Date(a.last_updated).getTime() : 0;
            const dateB = b.last_updated ? new Date(b.last_updated).getTime() : 0;
            return dateA - dateB; 
        });
        const recentItems = items.filter(i => {
            if (!i.complete) return false;
            if (!i.last_updated) return false; 
            return new Date(i.last_updated).getTime() > cutoffTime;
        }).sort((a, b) => {
            const countDiff = (b.counter || 0) - (a.counter || 0);
            if (countDiff !== 0) return countDiff;
            const dateA = a.last_updated ? new Date(a.last_updated).getTime() : 0;
            const dateB = b.last_updated ? new Date(b.last_updated).getTime() : 0;
            return dateB - dateA;
        });
        const rareItems = items.filter(i => {
            if (!i.complete) return false;
            if (!i.last_updated) return true; 
            return new Date(i.last_updated).getTime() <= cutoffTime;
        }).sort((a, b) => {
            const countDiff = (b.counter || 0) - (a.counter || 0);
            if (countDiff !== 0) return countDiff;
            const dateA = a.last_updated ? new Date(a.last_updated).getTime() : 0;
            const dateB = b.last_updated ? new Date(b.last_updated).getTime() : 0;
            return dateB - dateA;
        });

        const renderSection = (title, itemsList, sectionKey) => {
            const isOpen = this._configData.sections[sectionKey];
            const sectionDiv = document.createElement('div');
            const header = document.createElement('div');
            header.className = 'section-header';
            header.innerHTML = `<div class="section-title">${title} (${itemsList.length})</div><ha-icon class="section-chevron ${isOpen ? '' : 'closed'}" icon="mdi:chevron-down"></ha-icon>`;
            header.onclick = () => {
                this._configData.sections[sectionKey] = !this._configData.sections[sectionKey];
                this.saveConfig(); this.renderItems(this._items);
            };
            const content = document.createElement('div');
            content.className = `section-content ${isOpen ? '' : 'closed'}`;
            itemsList.forEach(item => { content.appendChild(this.createItemRow(item)); });
            sectionDiv.appendChild(header); sectionDiv.appendChild(content);
            this.listContainer.appendChild(sectionDiv);
        };

        if (activeItems.length > 0) renderSection("DA ACQUISTARE", activeItems, 'active');
        if (recentItems.length > 0) renderSection("ACQUISTATI DI RECENTE", recentItems, 'recent');
        if (rareItems.length > 0) renderSection(`ACQUISTATI RARAMENTE (> ${thresholdDays}gg)`, rareItems, 'rare');
    }

    createItemRow(item) {
        const row = document.createElement('div');
        row.className = 'list-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'checkbox';
        checkbox.checked = item.complete;
        checkbox.onclick = () => this.toggleItemStatus(item);
        const content = document.createElement('div');
        content.className = 'item-content';
        content.onclick = () => this.openDetail(item); 
        const nameSpan = document.createElement('span');
        nameSpan.className = `item-name ${item.complete ? 'completed' : ''}`;
        nameSpan.innerText = item.name;
        content.appendChild(nameSpan); row.appendChild(checkbox); row.appendChild(content);
        return row;
    }

    async toggleItemStatus(item) {
        const targetState = !item.complete;
        const index = this._items.findIndex(i => i.id === item.id);
        if (index > -1) {
            this._items[index].complete = targetState;
            if (targetState) {
                this._items[index].counter = (this._items[index].counter || 0) + 1;
                this._items[index].last_updated = new Date().toISOString();
            }
            this.renderItems(this._items);
        }
        await this._hass.callWS({ type: 'wiselist/update', item_id: item.id, complete: targetState });
    }

    async addItem(rawName) {
        if (!rawName) return;
        const name = this.formatName(rawName);
        const existingItem = this._items.find(i => i.name.toLowerCase() === name.toLowerCase());
        if (existingItem) { this.openDetail(existingItem); return; }
        const newItem = await this._hass.callWS({ type: 'wiselist/add', name: name });
        if (newItem) { this._items.push(newItem); this.renderItems(this._items); }
    }

    openSettingsModal() {
        this.modal.innerHTML = ''; this.modal.style.display = 'flex'; 
        const box = document.createElement('div'); box.className = 'modal-box';
        const header = document.createElement('div'); header.className = 'modal-header'; header.innerText = "Impostazioni"; box.appendChild(header);
        const editRow = document.createElement('div'); editRow.className = 'edit-row'; editRow.style.flexDirection = 'column'; editRow.style.alignItems = 'flex-start';
        const label = document.createElement('div'); label.innerText = "Giorni per 'Raramente':"; label.style.fontSize = '12px'; label.style.color = 'var(--secondary-text-color)';
        const input = document.createElement('input'); input.className = 'edit-input'; input.type = 'number'; input.value = this._configData.rareThreshold; input.style.width = '100%'; input.style.borderBottom = '1px solid var(--divider-color)';
        editRow.appendChild(label); editRow.appendChild(input); box.appendChild(editRow);
        const actions = document.createElement('div'); actions.className = 'dialog-actions'; actions.style.justifyContent = 'flex-end';
        const btnCancel = document.createElement('ha-button'); btnCancel.setAttribute('appearance', 'plain'); btnCancel.innerText = 'Chiudi'; btnCancel.addEventListener('click', () => { this.modal.style.display = 'none'; });
        const btnSave = document.createElement('ha-button'); btnSave.setAttribute('variant', 'brand'); btnSave.setAttribute('appearance', 'accent'); btnSave.innerText = 'Salva';
        btnSave.addEventListener('click', () => {
            const newVal = parseInt(input.value);
            if (!isNaN(newVal) && newVal > 0) {
                this._configData.rareThreshold = newVal; this.saveConfig(); this.renderItems(this._items);
            }
            this.modal.style.display = 'none';
        });
        actions.appendChild(btnCancel); actions.appendChild(btnSave); box.appendChild(actions); this.modal.appendChild(box);
    }

    openDetail(item) {
        this.modal.innerHTML = ''; this.modal.style.display = 'flex'; 
        const box = document.createElement('div'); box.className = 'modal-box';
        const header = document.createElement('div'); header.className = 'modal-header'; header.innerText = "Modifica Prodotto"; box.appendChild(header);
        const editRow = document.createElement('div'); editRow.className = 'edit-row';
        const editCheck = document.createElement('input'); editCheck.type = 'checkbox'; editCheck.className = 'edit-checkbox'; editCheck.checked = item.complete;
        const editInput = document.createElement('input'); editInput.className = 'edit-input'; editInput.value = item.name;
        const saveAction = async () => {
             const newName = this.formatName(editInput.value);
             item.name = newName; item.complete = editCheck.checked;
             this.renderItems(this._items); 
             await this._hass.callWS({ type: 'wiselist/update', item_id: item.id, name: newName, complete: editCheck.checked });
            this.modal.style.display = 'none';
        };
        editInput.addEventListener("keyup", (e) => { if (e.key === "Enter") saveAction(); });
        editRow.appendChild(editCheck); editRow.appendChild(editInput); box.appendChild(editRow);
        const statsContainer = document.createElement('div'); statsContainer.className = 'stats-container';
        let dateStr = "-";
        if (item.last_updated) {
            const d = new Date(item.last_updated);
            dateStr = `${d.toLocaleDateString()} ${d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
        }
        const stat1 = document.createElement('div'); stat1.className = 'stat-row'; stat1.innerHTML = `Acquistato: <span class="stat-val">${item.counter || 0} volte</span>`;
        const stat2 = document.createElement('div'); stat2.className = 'stat-row'; stat2.innerHTML = `Ultimo: <span class="stat-val">${dateStr}</span>`;
        statsContainer.appendChild(stat1); statsContainer.appendChild(stat2); box.appendChild(statsContainer);
        const actions = document.createElement('div'); actions.className = 'dialog-actions';
        const closeModal = () => { this.modal.style.display = 'none'; };
        const btnCancel = document.createElement('ha-button'); btnCancel.setAttribute('appearance', 'plain'); btnCancel.innerText = 'Annulla'; btnCancel.addEventListener('click', closeModal);
        const btnDelete = document.createElement('ha-button'); btnDelete.setAttribute('variant', 'danger'); btnDelete.setAttribute('appearance', 'plain'); btnDelete.innerText = 'Elimina';
        btnDelete.addEventListener('click', async () => {
            if(confirm("Eliminare definitivamente?")) {
                this._items = this._items.filter(i => i.id !== item.id);
                this.renderItems(this._items);
                closeModal();
                await this._hass.callWS({ type: 'wiselist/remove', item_id: item.id });
            }
        });
        const btnSave = document.createElement('ha-button'); btnSave.setAttribute('variant', 'brand'); btnSave.setAttribute('appearance', 'accent'); btnSave.innerText = 'Salva'; btnSave.addEventListener('click', saveAction);
        actions.appendChild(btnCancel); actions.appendChild(btnDelete); actions.appendChild(btnSave); box.appendChild(actions);
        this.modal.appendChild(box);
        setTimeout(() => editInput.focus(), 50);
    }
    setConfig(config) { }
    getCardSize() { return 5; }
}

customElements.define('wiselist-card', WiseListCard);
