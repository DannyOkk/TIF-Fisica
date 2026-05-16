#!/usr/bin/env python3
"""Lanzador de interfaz web para el simulador de colisiones."""

import webbrowser
import time
from src.web_server import app

if __name__ == '__main__':
    print("\n" + "="*60)
    print("SIMULADOR DE COLISIONES 2D - INTERFAZ WEB")
    print("="*60)
    print("\n🚀 Iniciando servidor Flask...")
    print("📍 Abre tu navegador en: http://127.0.0.1:5001")
    print("\n💡 Controles:")
    print("   - ⏵ Reproducir: Inicia la animación")
    print("   - ⏸ Pausar: Pausa la animación")
    print("   - ⏮ Anterior / ⏭ Siguiente: Navega frame a frame")
    print("   - Velocidad: Acelera o desacelera la reproducción")
    print("   - Ir a paso: Salta a cualquier frame")
    print("\n" + "="*60 + "\n")
    
    # Abrir navegador automáticamente
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5001')
    
    # Ejecutar servidor
    app.run(debug=False, host='127.0.0.1', port=5001)
