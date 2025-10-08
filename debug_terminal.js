// ============================================
// SCRIPT DI DEBUG PER IL TERMINALE XTERM.JS
// ============================================
// Copia e incolla questo script nella Console del browser (F12)
// quando sei sulla pagina di Proximity

console.log('🔍 ===== DEBUG TERMINALE XTERM.JS =====\n');

// 1. Verifica presenza del token
console.log('1️⃣ VERIFICA TOKEN:');
const token = localStorage.getItem('proximity_token');
if (token) {
    console.log('   ✅ Token trovato!');
    console.log('   📝 Lunghezza token:', token.length, 'caratteri');
    console.log('   🔑 Token (primi 50 caratteri):', token.substring(0, 50) + '...');
    
    // Decodifica JWT per vedere il payload
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        console.log('   📦 Payload JWT:', payload);
        console.log('   👤 Username:', payload.sub);
        console.log('   🕐 Scadenza:', new Date(payload.exp * 1000).toLocaleString());
        console.log('   ⏰ Token valido:', payload.exp * 1000 > Date.now() ? '✅ SÌ' : '❌ SCADUTO');
    } catch (e) {
        console.log('   ⚠️ Errore decodifica JWT:', e);
    }
} else {
    console.log('   ❌ NESSUN TOKEN TROVATO!');
    console.log('   ⚠️ DEVI FARE IL LOGIN PRIMA!');
}

// 2. Verifica Auth object
console.log('\n2️⃣ VERIFICA AUTH OBJECT:');
if (typeof Auth !== 'undefined') {
    console.log('   ✅ Auth object disponibile');
    console.log('   🔐 Auth.isAuthenticated():', Auth.isAuthenticated());
    console.log('   🔑 Auth.getToken():', Auth.getToken() ? 'Token presente' : 'NO TOKEN');
    console.log('   👤 Auth.getUser():', Auth.getUser());
} else {
    console.log('   ❌ Auth object NON disponibile!');
}

// 3. Verifica authFetch
console.log('\n3️⃣ VERIFICA authFetch:');
if (typeof authFetch !== 'undefined') {
    console.log('   ✅ authFetch function disponibile');
    
    // Test authFetch con headers
    const headers = Auth.getHeaders();
    console.log('   📋 Headers generati:');
    console.log('      - Content-Type:', headers['Content-Type']);
    console.log('      - Authorization:', headers['Authorization'] ? '✅ PRESENTE' : '❌ MANCANTE');
    if (headers['Authorization']) {
        console.log('      - Bearer token:', headers['Authorization'].substring(0, 30) + '...');
    }
} else {
    console.log('   ❌ authFetch function NON disponibile!');
}

// 4. Verifica API_BASE
console.log('\n4️⃣ VERIFICA API_BASE:');
if (typeof API_BASE !== 'undefined') {
    console.log('   ✅ API_BASE definito:', API_BASE);
} else {
    console.log('   ❌ API_BASE NON definito!');
}

// 5. Test completo di chiamata API
console.log('\n5️⃣ TEST CHIAMATA API:');
if (Auth.isAuthenticated()) {
    console.log('   🧪 Eseguendo test di chiamata a /api/v1/system/info...');
    
    fetch(`${API_BASE}/system/info`, {
        headers: Auth.getHeaders()
    })
    .then(response => {
        console.log('   📡 Status Code:', response.status);
        if (response.status === 200) {
            console.log('   ✅ CHIAMATA RIUSCITA! Il token funziona!');
            return response.json();
        } else if (response.status === 401) {
            console.log('   ❌ 401 UNAUTHORIZED! Il token NON è valido o è scaduto!');
            console.log('   💡 Fai logout e rilogin!');
        } else {
            console.log('   ⚠️ Status inaspettato:', response.status);
        }
    })
    .then(data => {
        if (data) {
            console.log('   📦 Risposta:', data);
        }
    })
    .catch(error => {
        console.log('   ❌ Errore:', error);
    });
} else {
    console.log('   ⚠️ Utente NON autenticato - impossibile testare');
    console.log('   💡 FAI IL LOGIN PRIMA!');
}

// 6. Verifica funzioni terminale
console.log('\n6️⃣ VERIFICA FUNZIONI TERMINALE:');
console.log('   showAppConsole:', typeof showAppConsole !== 'undefined' ? '✅ Disponibile' : '❌ Non disponibile');
console.log('   initializeXterm:', typeof initializeXterm !== 'undefined' ? '✅ Disponibile' : '❌ Non disponibile');
console.log('   executeTerminalCommand:', typeof executeTerminalCommand !== 'undefined' ? '✅ Disponibile' : '❌ Non disponibile');
console.log('   xterm library:', typeof Terminal !== 'undefined' ? '✅ Caricata' : '❌ Non caricata');

// 7. Riepilogo e suggerimenti
console.log('\n📋 ===== RIEPILOGO =====');
if (!token) {
    console.log('🔴 PROBLEMA: Nessun token trovato!');
    console.log('💡 SOLUZIONE:');
    console.log('   1. Fai logout se necessario: Auth.logout()');
    console.log('   2. Ricarica la pagina: location.reload()');
    console.log('   3. Fai il login con username e password');
    console.log('   4. Riprova ad aprire il terminale');
} else if (typeof Auth !== 'undefined' && !Auth.isAuthenticated()) {
    console.log('🟡 PROBLEMA: Token presente ma Auth.isAuthenticated() ritorna false!');
    console.log('💡 VERIFICA:');
    console.log('   - Il token potrebbe essere scaduto');
    console.log('   - Prova a fare logout e rilogin');
} else {
    console.log('🟢 TUTTO OK! Il terminale dovrebbe funzionare!');
    console.log('💡 Se ancora non funziona:');
    console.log('   1. Apri Network tab (F12)');
    console.log('   2. Prova un comando nel terminale');
    console.log('   3. Controlla la richiesta POST /api/v1/apps/{app_id}/exec');
    console.log('   4. Verifica che l\'header Authorization: Bearer ... sia presente');
}

console.log('\n🔍 ===== FINE DEBUG =====');
