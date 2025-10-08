#!/usr/bin/env python3
"""
Test manuale per verificare il flusso di autenticazione
"""
import requests
import json

BASE_URL = "http://localhost:8765/api/v1"

def test_authentication_flow():
    print("🔐 Test Autenticazione Manuale\n")
    
    # Step 1: Prova a registrare un utente di test
    print("1️⃣  Registrazione utente di test...")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 200:
            print("   ✅ Registrazione riuscita!")
        elif response.status_code == 400 and "already exists" in response.text:
            print("   ℹ️  Utente già esistente, procedo con il login")
        else:
            print(f"   ⚠️  Registrazione: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Errore registrazione: {e}")
    
    # Step 2: Login per ottenere il token
    print("\n2️⃣  Login per ottenere il token...")
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"   ✅ Login riuscito!")
            print(f"   🔑 Token: {token[:50]}..." if token else "   ❌ Nessun token ricevuto")
            
            # Step 3: Test chiamata autenticata
            print("\n3️⃣  Test chiamata autenticata (GET /apps)...")
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(f"{BASE_URL}/apps", headers=headers)
            print(f"   📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Chiamata autenticata riuscita!")
                apps = response.json()
                print(f"   📦 Numero di app: {len(apps)}")
            else:
                print(f"   ❌ Errore: {response.text}")
            
            # Step 4: Test comando exec nel terminale
            print("\n4️⃣  Test comando exec (POST /apps/nginx-nginx-01/exec)...")
            exec_data = {
                "command": "ls -la"
            }
            
            response = requests.post(
                f"{BASE_URL}/apps/nginx-nginx-01/exec",
                headers=headers,
                json=exec_data
            )
            
            print(f"   📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Comando exec riuscito!")
                result = response.json()
                print(f"   📄 Output:\n{result.get('output', 'Nessun output')[:200]}")
            elif response.status_code == 404:
                print("   ℹ️  App 'nginx-nginx-01' non trovata (normale se non esiste)")
            else:
                print(f"   ❌ Errore: {response.text}")
            
            # Step 5: Test senza token
            print("\n5️⃣  Test chiamata SENZA token (dovrebbe fallire)...")
            response = requests.post(
                f"{BASE_URL}/apps/nginx-nginx-01/exec",
                json=exec_data
            )
            
            print(f"   📡 Status Code: {response.status_code}")
            
            if response.status_code == 401:
                print("   ✅ Correttamente rifiutata (401 Unauthorized)")
            else:
                print(f"   ⚠️  Inaspettato: {response.status_code}")
                
        else:
            print(f"   ❌ Login fallito: {response.status_code}")
            print(f"   📄 Risposta: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Errore login: {e}")

if __name__ == "__main__":
    try:
        test_authentication_flow()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
