"""Proxmox app initialization with mock support."""

import os

# Letta all'import del pacchetto, ma usata solo quando qualcuno chiede
# davvero ProxmoxService: vedi __getattr__ qui sotto.
USE_MOCK = os.getenv("USE_MOCK_PROXMOX") == "1"

__all__ = ["ProxmoxService", "ProxmoxError"]


def __getattr__(name):
    """Risolve ProxmoxService e ProxmoxError al primo uso, non all'import.

    Prima l'import di `.services` stava qui, al livello del modulo. Ma
    `apps.proxmox` e' in INSTALLED_APPS, e Django importa tutti i moduli delle
    app *prima* di caricare i modelli: importare i modelli da un __init__ di
    pacchetto rompeva `django.setup()` con

        django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.

    Il backend partiva comunque solo perche' docker-compose.yml fissa
    USE_MOCK_PROXMOX=1, che prendeva il ramo del mock (senza dipendenze dai
    modelli). Senza quella variabile l'applicazione non si avviava, e pytest
    non riusciva nemmeno a raccogliere i test.

    Con la risoluzione pigra entrambi i rami funzionano, e il momento
    dell'import e' quello in cui il servizio serve davvero: a registro delle
    app gia' pronto.
    """
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if USE_MOCK:
        print("🎭 MOCK: USE_MOCK_PROXMOX=1, carico MockProxmoxService")
        from .mock_service import MockProxmoxService, ProxmoxError
        resolved = {"ProxmoxService": MockProxmoxService, "ProxmoxError": ProxmoxError}
    else:
        print("📦 REALE: carico ProxmoxService")
        from .services import ProxmoxService, ProxmoxError
        resolved = {"ProxmoxService": ProxmoxService, "ProxmoxError": ProxmoxError}

    # Memorizzate nel modulo: il prossimo accesso non passa piu' da qui.
    globals().update(resolved)
    return resolved[name]
