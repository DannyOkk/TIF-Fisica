"""Contenedor: Gestión del dominio y colisiones con fronteras.

     MEDIDOR DE PRESIÓN MACROSCÓPICA
==========================================

El contenedor calcula la presión mediante detección de impulsos en las fronteras.
Cada rebote transfiere cantidad de movimiento a las paredes, que se acumula
en cada paso y se convierte en presión macroscópica.

Cálculo de Presión:
==================
Presión lineal instantánea = (Impulso_pared / dt) / Perímetro

Donde:
- Impulso_pared: Suma de cambios de momento en colisiones con paredes (kg·m/s)
- dt: Paso temporal (s)
- Perímetro: Perímetro del contenedor rectangular (m)

Resultado:
- Unidades: (kg·m/s) / (s × m) = N/m (presión lineal)
- Interpretación: Fuerza por unidad de longitud; equivale a Pa si se asume
    profundidad unitaria (1 m) en el eje fuera del plano
- Comportamiento: P ↑ con temperatura (gas más rápido)
- Comportamiento: P ↓ con enfriamiento (gas más lento)
"""

import numpy as np
from typing import Tuple
from .particula import Particula


class Contenedor:
    """Dominio rectangular que gestiona límites y calcula presión macroscópica.
    
    El contenedor define un dominio rectangular [0, ancho] × [0, alto]
    donde las partículas rebotan elásticamente (o inelásticamente según e).
    
    MÓDULO 5: Se calcula la presión acumulando impulsos en cada paso.
    
    Atributos:
    ==========
    - ancho, alto: Dimensiones del dominio (m)
    - e_pared: Coef. restitución para rebotes en paredes (0-1)
    - perimetro: 2*(ancho + alto) - necesario para calcular presión
    """
    
    def __init__(self, ancho: float, alto: float, coef_restitution_pared: float = 0.9) -> None:
        """Inicializa contenedor rectangular.
        
        Args:
            ancho: Ancho del dominio en metros (eje X: [0, ancho])
            alto: Alto del dominio en metros (eje Y: [0, alto])
            coef_restitution_pared: Coef. restitución para rebotes en paredes.
                                   Default: 0.9 (ligeramente inelástico)
                                   Rango: [0, 1] (automáticamente clampado)
        """
        self.ancho: float = float(ancho)
        self.alto: float = float(alto)
        self.e_pared: float = float(np.clip(coef_restitution_pared, 0.0, 1.0))
        
        # Perímetro total: necesario para cálculo de presión (Módulo 5)
        self.perimetro: float = 2.0 * (self.ancho + self.alto)
    
    def detectar_colision_frontera(self, particula: Particula) -> bool:
        """Detecta si una partícula está tocando alguna frontera.
        
        Una partícula toca frontera si:
        - Pared izquierda: x - r ≤ 0
        - Pared derecha: x + r ≥ ancho
        - Pared inferior: y - r ≤ 0
        - Pared superior: y + r ≥ alto
        
        Args:
            particula: Partícula a verificar
            
        Returns:
            bool: True si está tocando alguna frontera
        """
        x: float = particula.posicion[0]
        y: float = particula.posicion[1]
        r: float = particula.radio
        
        # Verifica si toca paredes verticales (x)
        toca_x: bool = (x - r <= 0) or (x + r >= self.ancho)
        
        # Verifica si toca paredes horizontales (y)
        toca_y: bool = (y - r <= 0) or (y + r >= self.alto)
        
        return toca_x or toca_y
    
    def resolver_colision_frontera(self, particula: Particula) -> float:
        """Resuelve rebote contra fronteras y retorna impulso transferido.
        
        MÓDULO 5: PRESIÓN MACROSCÓPICA
        ==============================
        
        Este método implementa rebotes contra las 4 paredes del contenedor.
        Cada rebote transfiere impulso a la pared, que se acumula para
        calcular la presión lineal instantánea: P = Impulso / (dt × perímetro)
        
        ALGORITMO DE REBOTE:
        ====================
        Para cada pared que toca:
        
        1. Reposicionar: Corregir posición para evitar penetración
        2. Invertir velocidad normal: v_new = -e * v_old (considerando e)
        3. Calcular impulso: Δp = m × |v_new - v_old| en dirección normal
        
        FÓRMULA DE IMPULSO:
        ===================
        Impulso = |m × (v_final - v_inicial)|
        
        Para una pared: v_x final = -e_pared × v_x inicial
        Impulso_pared = m × |(-e_pared × v - v)| = m × v × (1 + e_pared)
        
        Esto acumula el cambio de momento transferido a la pared.
        
        CASOS ESPECIALES:
        =================
        - e_pared = 1.0: Rebote perfectamente elástico (sin disipación)
        - e_pared < 1.0: Rebote inelástico (disipación de energía)
        - Esquinas: Se manejan dos rebotes (x e y) en el mismo paso
        
        Args:
            particula: Partícula a hacer rebotar (se modifica in-place)
            
        Returns:
            float: Impulso total transferido a las paredes en kg·m/s
        """
        x: float = particula.posicion[0]
        y: float = particula.posicion[1]
        vx: float = particula.velocidad[0]
        vy: float = particula.velocidad[1]
        r: float = particula.radio
        m: float = particula.masa
        
        impulso_total: float = 0.0
        
        # ========== COLISIONES CON PAREDES VERTICALES (x) ==========
        if x - r <= 0:
            # PARED IZQUIERDA (x = 0)
            particula.posicion[0] = r
            # Velocidad rebota: vx_new = e × |vx_old| (hacia la derecha)
            particula.velocidad[0] = abs(vx) * self.e_pared
            # Impulso transferido: cambio de momento en dirección normal
            impulso_total += abs(m * (particula.velocidad[0] - vx))
            
        elif x + r >= self.ancho:
            # PARED DERECHA (x = ancho)
            particula.posicion[0] = self.ancho - r
            # Velocidad rebota: vx_new = -e × |vx_old| (hacia la izquierda)
            particula.velocidad[0] = -abs(vx) * self.e_pared
            # Impulso transferido
            impulso_total += abs(m * (particula.velocidad[0] - vx))
        
        # ========== COLISIONES CON PAREDES HORIZONTALES (y) ==========
        if y - r <= 0:
            # PARED INFERIOR (y = 0)
            particula.posicion[1] = r
            # Velocidad rebota: vy_new = e × |vy_old| (hacia arriba)
            particula.velocidad[1] = abs(vy) * self.e_pared
            # Impulso transferido
            impulso_total += abs(m * (particula.velocidad[1] - vy))
            
        elif y + r >= self.alto:
            # PARED SUPERIOR (y = alto)
            particula.posicion[1] = self.alto - r
            # Velocidad rebota: vy_new = -e × |vy_old| (hacia abajo)
            particula.velocidad[1] = -abs(vy) * self.e_pared
            # Impulso transferido
            impulso_total += abs(m * (particula.velocidad[1] - vy))

        return float(impulso_total)
