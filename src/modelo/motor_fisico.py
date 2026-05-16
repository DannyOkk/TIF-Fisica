"""Motor físico: maneja colisiones y física."""

import numpy as np
from typing import List, Tuple
from .particula import Particula


class MotorFisico:
    """Resuelve colisiones entre partículas usando componentes normal/tangencial.
    
    MÉTODO NUMÉRICO DE INTEGRACIÓN:
    ===============================
    Integración temporal: Método Euler Explícito
    - Ecuación diferencial: dx/dt = v,  dv/dt = a
    - Discretización: x_{n+1} = x_n + v_n * dt,  v_{n+1} = v_n + a_n * dt
    - Paso temporal (dt): 0.01 segundos
    - Precisión: O(dt²) por paso, acumulativo a lo largo de simulación
    
    RESOLUCIÓN DE COLISIONES:
    =========================
    Cuando detecta colisión entre partículas p1 y p2:
    
    1. Calcula vector normal: n̂ = (p2.pos - p1.pos) / |distancia|
    
    2. Descomposición de velocidades:
       v₁ₙ = (v₁ · n̂) n̂    (componente normal de p1)
       v₁ₜ = v₁ - v₁ₙ       (componente tangencial de p1)
       [Similar para p2]
    
    3. Ecuación de restitución (componente normal):
       Velocidad relativa: v_rel_n = (v₂ - v₁) · n̂
       Impulso: j = -(1 + e) * v_rel_n / (1/m₁ + 1/m₂)
       donde e ∈ [0,1] es el coef. de restitución promedio
    
    4. Aplicación del impulso:
       Δv₁ = (j / m₁) * n̂
       Δv₂ = (-j / m₂) * n̂
    
    5. Reconstrucción: v_nueva = v_tangencial + (v_normal + Δv)
    
    CONSERVACIÓN FÍSICA:
    ====================
    ✓ Momento lineal: p_total = m₁*v₁ + m₂*v₂ (conservado exactamente)
    ✓ Energía: Depende de e
      - e=1.0 (elástica): Energía cinética conservada
      - e<1.0 (inelástica): Energía disipada = (1/2)*μ*v_rel²*(1-e²)
    
    AMORTIGUAMIENTO:
    ================
    - Factor de amortiguamiento de aire: 0.9995 por paso
    - Simula resistencia del medio
    
    Algoritmo completo por paso:
    1. Euler update posiciones: x_{n+1} = x_n + v_n*dt
    2. Detectar colisiones O(N²)
    3. Resolver colisiones con impulsos
    4. Detectar colisiones con fronteras
    5. Aplicar amortiguamiento
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
        
        FÓRMULA DE IMPULSO BASADA EN COEFICIENTE DE RESTITUCIÓN:
        =========================================================
        
        Entrada: velocidades v₁, v₂; masas m₁, m₂; coef. restitución e₁, e₂
        
        1. Promedio de coeficientes: e = (e₁ + e₂) / 2
        
        2. Vector normal unitario: n̂ = (p₂·pos - p₁·pos) / ||p₂·pos - p₁·pos||
        
        3. Velocidad relativa en dirección normal:
           v_rel_n = (v₂ - v₁) · n̂
        
        4. IMPULSO (en dirección normal):
           j = -(1 + e) * v_rel_n / (1/m₁ + 1/m₂)
        
        5. Cambio de velocidades:
           Δv₁ = (j / m₁) * n̂
           Δv₂ = -(j / m₂) * n̂
        
        6. Velocidades finales:
           v₁_new = v₁ + Δv₁
           v₂_new = v₂ + Δv₂
        
        CONSERVACIÓN Y PROPIEDADES:
        ===========================
        ✓ Momento lineal (antes == después):
          m₁·v₁ + m₂·v₂ = m₁·v₁_new + m₂·v₂_new
        
        ✓ Coeficiente de restitución:
          (v₂_new - v₁_new) · n̂ = -e * (v₂ - v₁) · n̂
        
        ✓ Energía disipada (cuando e < 1):
          ΔE_k = (1/2) * μ * v_rel² * (1 - e²)
          donde μ = m₁*m₂/(m₁+m₂) es la masa reducida
        
        CASOS ESPECIALES:
        =================
        - Si v_rel_n >= 0: partículas se alejan → no hay colisión
        - Si distancia < 1e-10: evita singularidad numérica
        - Si e=1.0: colisión elástica (E_k conservada)
        - Si e=0.0: colisión plástica (máxima disipación)
        
        Modifica velocidades in-place de p1 y p2.
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
