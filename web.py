#!/usr/bin/env python3
"""Servidor Flask para interfaz web del simulador de colisiones.

Este script inicia el servidor web sin abrir automáticamente el navegador.
El navegador se abre desde el menú principal del programa.
"""

from src.web_server import app

if __name__ == '__main__':
    print("\n" + "="*60)
    print("SERVIDOR WEB - SIMULADOR DE COLISIONES 2D")
    print("="*60)
    print("\n✓ Servidor ejecutándose en: http://127.0.0.1:5002")
    print("✓ Puedes cerrar este servidor con: Ctrl+C")
    print("\n" + "="*60 + "\n")
    
    # Ejecutar servidor
    app.run(debug=False, host='127.0.0.1', port=5002, use_reloader=False)
