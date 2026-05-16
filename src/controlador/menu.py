"""Menú principal: interfaz de usuario interactiva."""

import numpy as np
from typing import List, Tuple
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
    
    def ejemplo_colision_elastica(self) -> None:
        """Ejemplo: dos partículas, colisión perfectamente elástica."""
        print("\n" + "="*60)
        print("EJEMPLO: COLISIÓN ELÁSTICA (e=1.0)")
        print("="*60)
        print("Masas iguales, velocidades opuestas")
        print("Predicción: Momento y energía constantes")
        
        self._crear_simulador()
        
        self.simulador.agregar_particula(
            posicion=np.array([3.0, 5.0]),
            velocidad=np.array([3.0, 0.0]),
            masa=1.0,
            radio=0.5,
            coef_restitution=1.0,
            color='red'
        )
        
        self.simulador.agregar_particula(
            posicion=np.array([7.0, 5.0]),
            velocidad=np.array([-2.0, 0.0]),
            masa=1.0,
            radio=0.5,
            coef_restitution=1.0,
            color='blue'
        )
        
        print("\n⏳ Ejecutando... (300 pasos)")
        self.simulador.ejecutar(300)
    
    def ejemplo_colision_inelastica(self) -> None:
        """Ejemplo: colisión inelástica con pérdida de energía."""
        print("\n" + "="*60)
        print("EJEMPLO: COLISIÓN INELÁSTICA (e=0.6)")
        print("="*60)
        print("Masas diferentes, coef. restitución parcial")
        print("Predicción: Momento constante, energía disminuye")
        
        self._crear_simulador()
        
        self.simulador.agregar_particula(
            posicion=np.array([2.0, 5.0]),
            velocidad=np.array([4.0, 0.0]),
            masa=2.0,
            radio=0.5,
            coef_restitution=0.6,
            color='red'
        )
        
        self.simulador.agregar_particula(
            posicion=np.array([8.0, 5.0]),
            velocidad=np.array([-1.0, 0.0]),
            masa=1.0,
            radio=0.5,
            coef_restitution=0.6,
            color='blue'
        )
        
        print("\n⏳ Ejecutando... (300 pasos)")
        self.simulador.ejecutar(300)
    
    def ejemplo_multiples_particulas(self) -> None:
        """Ejemplo: sistema con 5 partículas aleatoriamente."""
        print("\n" + "="*60)
        print("EJEMPLO: MÚLTIPLES PARTÍCULAS")
        print("="*60)
        print("Sistema complejo con 5 partículas y múltiples colisiones")
        
        self._crear_simulador()
        
        # Posiciones, velocidades, masas fijas
        configs = [
            (np.array([1.5, 2.0]), np.array([2.0, 1.5]), 1.0),
            (np.array([8.5, 8.0]), np.array([-1.5, -2.0]), 1.2),
            (np.array([5.0, 5.0]), np.array([0.5, -1.0]), 0.8),
            (np.array([2.0, 8.0]), np.array([1.0, -2.0]), 1.5),
            (np.array([8.0, 2.0]), np.array([-2.0, 1.0]), 1.0),
        ]
        
        colores = ['red', 'blue', 'green', 'yellow', 'orange']
        
        for i, (pos, vel, masa) in enumerate(configs):
            self.simulador.agregar_particula(
                posicion=pos,
                velocidad=vel,
                masa=masa,
                radio=0.4,
                coef_restitution=0.8,
                color=colores[i]
            )
        
        print("\n⏳ Ejecutando... (500 pasos)")
        self.simulador.ejecutar(500)
    
    def mostrar_menu_principal(self) -> None:
        """Muestra menú principal."""
        print("\n" + "="*60)
        print("SIMULADOR DE COLISIONES EN 2D")
        print("="*60)
        print("\n¿Qué deseas hacer?")
        print("  1. Simulación personalizada (ingresar tus propios datos)")
        print("  2. Ejemplo: Colisión elástica")
        print("  3. Ejemplo: Colisión inelástica")
        print("  4. Ejemplo: Múltiples partículas")
        print("  5. Salir (cierra el programa)")
        print("\n" + "-"*60)
    
    def procesar_opcion(self, opcion: str) -> None:
        """Procesa opción del menú."""
        if opcion == '1':
            self.personalizado()
        elif opcion == '2':
            self.ejemplo_colision_elastica()
        elif opcion == '3':
            self.ejemplo_colision_inelastica()
        elif opcion == '4':
            self.ejemplo_multiples_particulas()
        elif opcion == '5':
            print("\n✓ Gracias por usar el simulador. ¡Hasta pronto!")
            self.corriendo = False
        else:
            print("   ⚠️  Opción no válida. Intenta nuevamente.")
    
    def ejecutar(self) -> None:
        """Loop principal que mantiene el programa corriendo."""
        print("\n" + "#"*60)
        print("# SIMULADOR DE COLISIONES EN 2D - TFI")
        print("# Ingeniería en Informática")
        print("#"*60)
        
        while self.corriendo:
            self.mostrar_menu_principal()
            opcion = input("Selecciona una opción (1-5): ").strip()
            self.procesar_opcion(opcion)
