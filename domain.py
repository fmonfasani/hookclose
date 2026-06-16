#!/usr/bin/env python3
"""
Verificador de dominios wa+XXX.com
Corre en tu máquina local con: python3 check_wa_domains.py

Requiere: pip install requests
"""
import requests
import time
import itertools
import sys

def is_pronounceable(s):
    """Solo pasa palabras que suenan bien al decirlas"""
    vowels = set('aeiou')
    cons_run = vow_run = 0
    for c in s:
        if c in vowels:
            vow_run += 1; cons_run = 0
            if vow_run > 2: return False
        else:
            cons_run += 1; vow_run = 0
            if cons_run > 2: return False
    # Tiene al menos una vocal
    return any(c in vowels for c in s)

def check_domain(domain):
    """
    RDAP de Verisign — API oficial del registro .com
    404 = dominio libre
    200 = tomado
    """
    url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'domain-checker/1.0'})
        if r.status_code == 404:
            return 'AVAILABLE'
        elif r.status_code == 200:
            return 'TAKEN'
        else:
            return f'UNKNOWN_{r.status_code}'
    except requests.exceptions.Timeout:
        return 'TIMEOUT'
    except Exception as e:
        return f'ERROR'

def generate_names():
    """Genera wa + 3 o 4 letras pronunciables"""
    chars = 'abcdefghijklmnoprstuvxz'
    names = []

    # 1 letra + sell
    for combo in itertools.product(chars, repeat=1):
        suffix = ''.join(combo)
        if is_pronounceable(suffix):
            names.append( suffix + 'sell')


    # 2 letras + sell
    for combo in itertools.product(chars, repeat=2):
        suffix = ''.join(combo)
        if is_pronounceable(suffix):
            names.append( suffix + 'sell')



    # wa + 3 letras + sell
    for combo in itertools.product(chars, repeat=3):
        suffix = ''.join(combo)
        if is_pronounceable(suffix):
            names.append( suffix + 'sell')

    # wa + 4 letras (solo los más pronunciables)
    for combo in itertools.product(chars, repeat=4):
        suffix = ''.join(combo)
        if is_pronounceable(suffix) and len([c for c in suffix if c in 'aeiou']) >= 2:
            names.append('wa' + suffix)

    return names

if __name__ == '__main__':
    print("=" * 60)
    print("BUSCADOR DE DOMINIOS wa+XXX.com DISPONIBLES")
    print("=" * 60)

    names = generate_names()
    print(f"Total combinaciones pronunciables: {len(names):,}")
    print(f"Iniciando... (Ctrl+C para parar)\n")

    available = []
    taken = 0
    errors = 0

    try:
        for i, name in enumerate(names):
            domain = f"{name}.com"
            status = check_domain(domain)

            if status == 'AVAILABLE':
                available.append(domain)
                print(f"✅  LIBRE: {domain}")
            elif status == 'TAKEN':
                taken += 1
            else:
                errors += 1

            # Progress cada 50
            if (i + 1) % 50 == 0:
                pct = (i + 1) / len(names) * 100
                print(f"    [{i+1:,}/{len(names):,} — {pct:.1f}%] disponibles: {len(available)}")

            # Parar al encontrar 100 disponibles
            if len(available) >= 100:
                print("\n✓ 100 disponibles encontrados — suficiente para elegir")
                break

            time.sleep(0.15)  # rate limit suave

    except KeyboardInterrupt:
        print("\n\n[Interrumpido por el usuario]")

    print(f"\n{'=' * 60}")
    print(f"Verificados: {i+1:,} | Disponibles: {len(available)} | Tomados: {taken}")
    print(f"\n🟢 DOMINIOS DISPONIBLES:")
    for d in sorted(available):
        print(f"   {d}")

    # Guardar resultado
    with open('wa_domains_disponibles.txt', 'w') as f:
        f.write('\n'.join(sorted(available)))
    print(f"\nGuardado en: wa_domains_disponibles.txt")