"""Modelo de datos: Particula
Representa una partícula física en el espacio 2D.
"""

import numpy as np
from typing import Tuple


class Particula:
    """Particula en el espacio 2D con propiedades físicas.
    
    Atributos:
        id: Identificador único
        posicion: np.ndarray [x, y]
        velocidad: np.ndarray [vx, vy]
        masa: kg
        radio: metros
        coef_restitution: Coeficiente de restitución (0-1)
        color: Para visualización
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
        """Inicializa una partícula."""
        self.id = particula_id
        self.posicion = np.array(posicion, dtype=float)
        self.velocidad = np.array(velocidad, dtype=float)
        self.masa = masa
        self.radio = radio
        self.coef_restitution = np.clip(coef_restitution, 0.0, 1.0)
        self.color = color
    
    def calcular_energia_cinetica(self) -> float:
        """Retorna: 0.5 * m * |v|²"""
        return 0.5 * self.masa * np.dot(self.velocidad, self.velocidad)
    
    def calcular_cantidad_movimiento(self) -> np.ndarray:
        """Retorna: m * v"""
        return self.masa * self.velocidad
    
    def actualizar_posicion(self, dt: float) -> None:
        """Actualiza posición: x = x + v*dt"""
        self.posicion += self.velocidad * dt
    
    def distancia_a(self, otra: 'Particula') -> float:
        """Distancia euclidiana entre centros."""
        return float(np.linalg.norm(self.posicion - otra.posicion))
