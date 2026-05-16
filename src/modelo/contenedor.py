"""Contenedor: gestiona el dominio y colisiones con fronteras."""

import numpy as np
from .particula import Particula


class Contenedor:
    """Dominio rectangular con límites que rebotan partículas."""
    
    def __init__(self, ancho: float, alto: float, coef_restitution_pared: float = 0.9) -> None:
        """Inicializa contenedor.
        
        Args:
            ancho: Ancho del dominio en metros
            alto: Alto del dominio en metros
            coef_restitution_pared: e para rebote en paredes
        """
        self.ancho = ancho
        self.alto = alto
        self.e_pared = np.clip(coef_restitution_pared, 0.0, 1.0)
    
    def detectar_colision_frontera(self, particula: Particula) -> bool:
        """Retorna True si partícula toca alguna frontera."""
        x, y = particula.posicion
        r = particula.radio
        
        toca_x = x - r <= 0 or x + r >= self.ancho
        toca_y = y - r <= 0 or y + r >= self.alto
        
        return toca_x or toca_y
    
    def resolver_colision_frontera(self, particula: Particula) -> None:
        """Resuelve rebote contra fronteras in-place."""
        x, y = particula.posicion
        vx, vy = particula.velocidad
        r = particula.radio
        
        # Paredes verticales (x)
        if x - r <= 0:
            particula.posicion[0] = r
            particula.velocidad[0] = abs(vx) * self.e_pared
        elif x + r >= self.ancho:
            particula.posicion[0] = self.ancho - r
            particula.velocidad[0] = -abs(vx) * self.e_pared
        
        # Paredes horizontales (y)
        if y - r <= 0:
            particula.posicion[1] = r
            particula.velocidad[1] = abs(vy) * self.e_pared
        elif y + r >= self.alto:
            particula.posicion[1] = self.alto - r
            particula.velocidad[1] = -abs(vy) * self.e_pared
