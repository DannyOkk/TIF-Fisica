"""Modelo de datos: Particula

Representa una partícula física puntual (aproximación esférica) en el espacio 2D.
Almacena todas las propiedades necesarias para simulación física:
- Cinemática: posición, velocidad, aceleración
- Dinámica: masa, radio, coeficiente de restitución
"""

import numpy as np
from typing import Tuple


class Particula:
    """Particula física en el espacio 2D con propiedades cinemáticas y dinámicas.
    
    Representa una esfera rígida en 2D con las siguientes características:
    - Movimiento traslacional (sin rotación)
    - Propiedades físicas (masa, radio, coef. restitución)
    - Cálculos de energía y momento
    
    Atributos:
    ==========
    - id: Identificador único auto-incremental
    - posicion: np.ndarray [x, y] en metros
    - velocidad: np.ndarray [vx, vy] en m/s
    - masa: Masa en kg
    - radio: Radio de la esfera en metros
    - coef_restitution: Coef. de restitución e ∈ [0, 1]
                        e = 1.0 → Colisión perfectamente elástica
                        e < 1.0 → Colisión inelástica (disipación)
    - color: String con nombre de color (para visualización)
    
    PROPIEDADES CALCULADAS:
    =======================
    - Energía cinética: Ek = 0.5 * m * |v|²
    - Cantidad de movimiento: p = m * v
    - Magnitud de velocidad: |v| = √(vx² + vy²)
    """
    
    def __init__(
        self,
        particula_id: int,
        posicion: np.ndarray,
        velocidad: np.ndarray,
        masa: float,
        radio: float,
        coef_restitution: float = 1.0,
        color: str = 'blue'
    ) -> None:
        """Inicializa una partícula con sus propiedades iniciales.
        
        Args:
            particula_id: Identificador único (entero auto-incremental)
            posicion: Coordenadas iniciales [x, y] en metros
            velocidad: Velocidad inicial [vx, vy] en m/s
            masa: Masa de la partícula en kg
            radio: Radio de la esfera en metros
            coef_restitution: Coeficiente de restitución (0-1)
                             Clamped automáticamente a [0, 1]
            color: Nombre de color (ej: 'red', 'blue'). Default: 'blue'
        """
        self.id: int = particula_id
        self.posicion: np.ndarray = np.array(posicion, dtype=float)
        self.velocidad: np.ndarray = np.array(velocidad, dtype=float)
        self.masa: float = float(masa)
        self.radio: float = float(radio)
        # Clampear coef. restitución a [0, 1]
        self.coef_restitution: float = float(np.clip(coef_restitution, 0.0, 1.0))
        self.color: str = color
    
    def calcular_energia_cinetica(self) -> float:
        """Calcula la energía cinética instantánea de la partícula.
        
        MÓDULO 1: ECUACIONES DINÁMICAS
        ==============================
        Fórmula: Ek = 0.5 * m * |v|²
        
        Donde:
        - m: masa de la partícula (kg)
        - |v|: magnitud del vector velocidad (m/s)
        
        Retorna:
            float: Energía cinética en Joules
        """
        # |v|² = vx² + vy² = v · v (producto escalar)
        velocidad_cuadrada: float = np.dot(self.velocidad, self.velocidad)
        return float(0.5 * self.masa * velocidad_cuadrada)
    
    def calcular_cantidad_movimiento(self) -> np.ndarray:
        """Calcula el vector cantidad de movimiento (momentum) instantáneo.
        
        MÓDULO 1: ECUACIONES DINÁMICAS
        ==============================
        Fórmula: p = m * v
        
        Donde:
        - m: masa de la partícula (kg)
        - v: vector velocidad [vx, vy] (m/s)
        
        Retorna:
            np.ndarray: Vector [px, py] en kg·m/s
        """
        return self.masa * self.velocidad
    
    def actualizar_posicion(self, dt: float) -> None:
        """Actualiza la posición usando integración Euler explícita.
        
        MÉTODO NUMÉRICO DE INTEGRACIÓN:
        ================================
        Ecuación diferencial: dx/dt = v
        Discretización: x_{n+1} = x_n + v_n * Δt
        
        Donde:
        - x_n: posición en paso n
        - v_n: velocidad en paso n
        - dt: paso temporal (segundos)
        
        Precisión: O(dt²) por paso. Error acumulativo es O(dt) a lo largo
        de la simulación.
        
        Args:
            dt: Paso temporal en segundos
        """
        self.posicion += self.velocidad * dt
    
    def distancia_a(self, otra: 'Particula') -> float:
        """Calcula distancia euclidiana entre centros de dos partículas.
        
        DETECCIÓN DE COLISIONES:
        ========================
        Se considera colisión cuando:
        distancia < radio_1 + radio_2
        
        Fórmula: d = |p1_pos - p2_pos| = √((x1-x2)² + (y1-y2)²)
        
        Args:
            otra: Otra instancia de Particula
            
        Returns:
            float: Distancia en metros (siempre ≥ 0)
        """
        return float(np.linalg.norm(self.posicion - otra.posicion))
