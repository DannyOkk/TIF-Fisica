"""Motor físico: maneja colisiones y física."""

import numpy as np
from typing import List, Tuple
from .particula import Particula


class MotorFisico:
    """Resuelve colisiones entre partículas usando componentes normal/tangencial.
    
    Algoritmo:
    1. Calcula vector normal: n̂ = (p2.pos - p1.pos) / |distancia|
    2. Proyecta velocidades en componentes normal y tangencial
    3. Aplica ecuación de restitución (conserva momento, disipa energía según e)
    4. Reconstruye velocidades completas
    5. Aplica amortiguamiento de aire
    """
    
    DAMPING_AIRE = 0.9995  # Amortiguamiento por fricción del aire
    
    @staticmethod
    def detectar_colision(p1: Particula, p2: Particula) -> bool:
        """Retorna True si dos partículas se tocan."""
        distancia = p1.distancia_a(p2)
        return distancia < (p1.radio + p2.radio)
    
    @staticmethod
    def resolver_colision(p1: Particula, p2: Particula) -> None:
        """Resuelve colisión entre p1 y p2 in-place.
        
        Modifica velocidades aplicando:
        - Coeficiente de restitución promedio
        - Conservación exacta de momento lineal
        - Disipación de energía según e
        """
        # Vector normal
        delta_pos = p2.posicion - p1.posicion
        distancia = np.linalg.norm(delta_pos)
        
        if distancia < 1e-10:  # Evita división por cero
            return
        
        n_hat = delta_pos / distancia
        
        # Velocidades relativas en dirección normal
        v_rel = p2.velocidad - p1.velocidad
        v_rel_n = np.dot(v_rel, n_hat)
        
        if v_rel_n >= 0:  # Se alejan
            return
        
        # Coeficiente de restitución promedio
        e = 0.5 * (p1.coef_restitution + p2.coef_restitution)
        
        # Cambio de momento normal (aplicando conservación + restitución)
        impulso = -(1 + e) * v_rel_n / (1/p1.masa + 1/p2.masa)
        
        p1.velocidad -= (impulso / p1.masa) * n_hat
        p2.velocidad += (impulso / p2.masa) * n_hat
