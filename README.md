# **WiseList**

## **🇮🇹 Italiano**

Un'evoluzione intelligente della lista della spesa per Home Assistant.  
Gestisce automaticamente i prodotti da acquistare, quelli recenti e quelli rari, con contatore acquisti e date.

### **Funzionalità**

* 🛒 **3 Liste Automatiche:** Da Acquistare, Recenti (\< 180gg), Rari (\> 180gg).  
* 📅 **Logica Temporale:** I prodotti si spostano automaticamente tra le liste in base alla frequenza di acquisto.  
* 🔢 **Contatore Acquisti:** Tiene traccia di quante volte compri un prodotto.  
* 🔎 **Ricerca Type-Ahead:** Suggerimenti intelligenti mentre scrivi per evitare duplicati.  
* ⚙️ **Configurabile:** Scegli tu (tramite menu) dopo quanti giorni un prodotto diventa "Raro".  
* 💾 **Persistenza:** Ricorda quali liste hai lasciato aperte o chiuse.  
* 📱 **Mobile Friendly:** Design ottimizzato in stile Home Assistant.

### **Installazione via HACS**

1. Vai in HACS \-\> Integrazioni \-\> 3 puntini in alto a destra \-\> **Repository Personalizzati**.  
2. Incolla l'URL di questo repository: https://github.com/TUO\_USER\_GITHUB/ha-wiselist  
3. Categoria: **Integrazione**.  
4. Clicca **Aggiungi**, poi cerca "WiseList" nella lista e clicca **Scarica**.  
5. **Riavvia Home Assistant**.

### **Configurazione Dashboard**

Dopo aver installato e riavviato, devi aggiungere manualmente la scheda alla tua dashboard YAML:

type: custom:wiselist-card

*Nota: La risorsa javascript viene registrata automaticamente dall'integrazione, non serve aggiungerla manualmente alle risorse.*

## **🇬🇧 English**

A smart evolution of the shopping list for Home Assistant.  
Automatically manages items to buy, recent items, and rare items, featuring purchase counters and dates logic.

### **Features**

* 🛒 **3 Automatic Lists:** To Buy, Recent (\< 180 days), Rare (\> 180 days).  
* 📅 **Time Logic:** Items automatically move between lists based on purchase frequency.  
* 🔢 **Purchase Counter:** Tracks how many times you buy a product.  
* 🔎 **Type-Ahead Search:** Smart suggestions while typing to avoid duplicates.  
* ⚙️ **Configurable:** Choose (via menu) after how many days an item becomes "Rare".  
* 💾 **Persistence:** Remembers which lists you left open or closed.  
* 📱 **Mobile Friendly:** Design optimized for Home Assistant style.

### **Installation via HACS**

1. Go to HACS \-\> Integrations \-\> 3 dots top right \-\> **Custom Repositories**.  
2. Paste the URL of this repository: https://github.com/YOUR\_GITHUB\_USER/ha-wiselist  
3. Category: **Integration**.  
4. Click **Add**, then search for "WiseList" in the list and click **Download**.  
5. **Restart Home Assistant**.

### **Dashboard Configuration**

After installing and restarting, manually add the card to your YAML dashboard:

type: custom:wiselist-card

*Note: The javascript resource is automatically registered by the integration, no need to add it manually to resources.*