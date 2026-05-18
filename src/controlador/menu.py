"""Menú principal: interfaz de usuario interactiva."""

import numpy as np
import json
from typing import List, Tuple
from pathlib import Path
from src.modelo.contenedor import Contenedor
from src.controlador import Simulador


class Menu:
    """Menú interactivo que mantiene el programa corriendo.
    
    El usuario puede:
    - Crear simulaciones personalizadas
    - Ver ejemplos predefinidos
    - Salir (única forma de cerrar el programa)
    """
    
    def __init__(self) -> None:
        self.simulador: Simulador = None
        self.corriendo = True
    
    def _crear_simulador(self) -> None:
        """Instancia un nuevo simulador."""
        contenedor = Contenedor(ancho=10.0, alto=10.0)
        self.simulador = Simulador(
            contenedor,
            dt=0.01,
            ancho_dominio=10.0,
            alto_dominio=10.0
        )
    
    def _cargar_escenario_json(self, archivo_json: str) -> None:
        """Carga escenario desde archivo JSON.
        
        Formato JSON esperado:
        {
          "nombre": "Nombre del escenario",
          "dt": 0.01,
          "ancho_dominio": 10.0,
          "alto_dominio": 10.0,
          "pasos": 300,
          "particulas": [
            {"posicion": [x, y], "velocidad": [vx, vy], "masa": m,
             "radio": r, "e": restitution, "color": "color"}
          ]
        }
        """
        ruta = Path(__file__).parent.parent.parent / "scenarios" / archivo_json
        
        if not ruta.exists():
            print(f"❌ Archivo no encontrado: {ruta}")
            return False
        
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            # Crear simulador con parámetros del JSON
            contenedor = Contenedor(
                ancho=datos.get("ancho_dominio", 10.0),
                alto=datos.get("alto_dominio", 10.0)
            )
            self.simulador = Simulador(
                contenedor,
                dt=datos.get("dt", 0.01),
                ancho_dominio=datos.get("ancho_dominio", 10.0),
                alto_dominio=datos.get("alto_dominio", 10.0)
            )
            
            # Agregar partículas
            for p in datos["particulas"]:
                self.simulador.agregar_particula(
                    posicion=np.array(p["posicion"]),
                    velocidad=np.array(p["velocidad"]),
                    masa=p["masa"],
                    radio=p["radio"],
                    coef_restitution=p["e"],
                    color=p["color"]
                )
            
            # Ejecutar simulación
            pasos = datos.get("pasos", 300)
            print(f"\n✓ Escenario: {datos.get('nombre', 'Sin nombre')}")
            print(f"✓ Descripción: {datos.get('descripcion', 'N/A')}")
            print(f"✓ Partículas: {len(datos['particulas'])}")
            print(f"⏳ Ejecutando {pasos} pasos...\n")
            self.simulador.ejecutar(pasos)
            return True
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"❌ Error al cargar JSON: {e}")
            return False
    
    def _listar_escenarios(self) -> List[str]:
        """Lista archivos JSON disponibles en la carpeta scenarios."""
        ruta_scenarios = Path(__file__).parent.parent.parent / "scenarios"
        if not ruta_scenarios.exists():
            return []
        return sorted([f.name for f in ruta_scenarios.glob("*.json")])
    
    def _input_numero(self, prompt: str, tipo=float, rango: Tuple[float, float] = None) -> any:
        """Lee número del usuario con validación."""
        while True:
            try:
                valor = tipo(input(prompt))
                if rango and (valor < rango[0] or valor > rango[1]):
                    print(f"   ⚠️  Ingresa un valor entre {rango[0]} y {rango[1]}")
                    continue
                return valor
            except ValueError:
                print(f"   ⚠️  Ingresa un número válido ({tipo.__name__})")
    
    def _input_vector2d(self, prompt: str) -> np.ndarray:
        """Lee vector 2D del usuario."""
        print(f"\n{prompt}")
        x = self._input_numero("  x: ", float)
        y = self._input_numero("  y: ", float)
        return np.array([x, y])
    
    def personalizado(self) -> None:
        """Menú para crear simulación personalizada."""
        print("\n" + "="*60)
        print("SIMULACIÓN PERSONALIZADA")
        print("="*60)
        
        self._crear_simulador()
        
        print("\nCuántas partículas deseas agregar?")
        num_particulas = self._input_numero("Número: ", int, (1, 20))
        
        colores = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'cyan', 'magenta']
        
        for i in range(num_particulas):
            print(f"\n--- Partícula {i+1} ---")
            
            posicion = self._input_vector2d("Posición inicial [x, y] (m):")
            velocidad = self._input_vector2d("Velocidad inicial [vx, vy] (m/s):")
            masa = self._input_numero("Masa (kg): ", float, (0.1, 100.0))
            radio = self._input_numero("Radio (m): ", float, (0.1, 2.0))
            e = self._input_numero(
                "Coeficiente de restitución [0=inelástica, 1=elástica]: ",
                float,
                (0.0, 1.0)
            )
            color = colores[i % len(colores)]
            
            self.simulador.agregar_particula(posicion, velocidad, masa, radio, e, color)
        
        num_pasos = self._input_numero("\nNúmero de pasos a simular: ", int, (10, 10000))
        
        print(f"\n⏳ Ejecutando simulación con {num_pasos} pasos...")
        self.simulador.ejecutar(num_pasos)
    
    def mostrar_menu_principal(self) -> None:
        """Muestra menú principal."""
        print("\n" + "="*60)
        print("SIMULADOR DE COLISIONES EN 2D")
        print("="*60)
        print("\n¿Qué deseas hacer?")
        print("\n📱 INTERFAZ TERMINAL (recomendado para PC bajo recursos):")
        print("  1. Simulación personalizada (ingresar tus propios datos)")
        print("  2. Cargar escenario desde JSON (con ejemplos presets)")
        print("  3. Interfaz del navegador (abre en tu navegador)")
        print("  4. Salir (cierra el programa)")
        print("\n" + "-"*60)
    
    def procesar_opcion(self, opcion: str) -> None:
        """Procesa opción del menú."""
        if opcion == '1':
            self.personalizado()
        elif opcion == '2':
            self._cargar_escenario_desde_menu()
        elif opcion == '3':
            self._abrir_interfaz_navegador()
        elif opcion == '4':
            print("\n✓ Gracias por usar el simulador. ¡Hasta pronto!")
            self.corriendo = False
        else:
            print("   ⚠️  Opción no válida. Intenta nuevamente.")
    
    def _cargar_escenario_desde_menu(self) -> None:
        """Menú interactivo para cargar escenarios desde JSON."""
        escenarios = self._listar_escenarios()
        
        if not escenarios:
            print("\n❌ No hay escenarios disponibles en la carpeta 'scenarios/'")
            return
        
        print("\n" + "="*60)
        print("CARGAR ESCENARIO DESDE JSON")
        print("="*60)
        print("\nEscenarios disponibles:")
        
        for i, archivo in enumerate(escenarios, 1):
            print(f"  {i}. {archivo}")
        print(f"  {len(escenarios) + 1}. Volver")
        
        print("\n" + "-"*60)
        
        try:
            opcion = input("Selecciona un escenario: ").strip()
            idx = int(opcion) - 1
            
            if idx < 0 or idx >= len(escenarios):
                print("   ⚠️  Opción no válida.")
                return
            
            archivo = escenarios[idx]
            self._cargar_escenario_json(archivo)
            
        except ValueError:
            print("   ⚠️  Ingresa un número válido.")
    
    def _abrir_interfaz_navegador(self) -> None:
        """Abre la interfaz gráfica del navegador."""
        import subprocess
        import sys
        import webbrowser
        import time
        
        print("\n" + "="*60)
        print("INTERFAZ DEL NAVEGADOR")
        print("="*60)
        print("\n🚀 Iniciando servidor web...")
        print("📍 Abre tu navegador en: http://127.0.0.1:5002")
        print("\n💡 Controles en el navegador:")
        print("   - ⏵ Reproducir: Inicia la animación")
        print("   - ⏸ Pausar: Pausa la animación")
        print("   - 🎚️  Velocidad: Ajusta la velocidad de reproducción")
        print("   - Selecciona escenarios desde el panel derecho")
        print("\n⏱️  Abriendo navegador en 2 segundos...\n")
        print("=" * 60 + "\n")
        
        try:
            # Ejecutar web.py en un subprocess
            archivo_web = Path(__file__).parent.parent / "web_server.py"
            # Pequeño delay para que el servidor esté listo
            time.sleep(1)
            webbrowser.open('http://127.0.0.1:5002')
            
            # Ejecutar el servidor
            subprocess.run(
                [sys.executable, str(Path(__file__).parent.parent.parent / "web.py")],
                check=False
            )
        except Exception as e:
            print(f"❌ Error al abrir la interfaz del navegador: {e}")
            print("   Intenta ejecutar: python web.py")
    
    def ejecutar(self) -> None:
        """Loop principal que mantiene el programa corriendo."""
        print("\n" + "#"*60)
        print("# SIMULADOR DE COLISIONES EN 2D - TFI")
        print("# Ingeniería en Informática")
        print("#"*60)
        
        while self.corriendo:
            self.mostrar_menu_principal()
            opcion = input("Selecciona una opción (1-4): ").strip()
            self.procesar_opcion(opcion)
