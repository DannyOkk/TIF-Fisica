"""Controlador: Orquestación de la simulación física con integración de 5 módulos.

MÓDULOS INTEGRADOS EN LA CLASE SIMULADOR:
==========================================

1. ECUACIONES DINÁMICAS EN PANTALLA (LaTeX):
   - Calcula y renderiza Momento y Energía frame-a-frame
   - Delegado: Visualizador._construir_texto_ecuaciones()

2. HISTOGRAMA MAXWELL-BOLTZMANN:
   - Actualiza distribución de velocidades en tiempo real
   - Delegado: Visualizador._actualizar_histograma()

3. CÓDIGO DE COLORES POR ENERGÍA:
   - Asigna colores según velocidad instantánea (azul → rojo)
   - Delegado: Visualizador.dibujar_particulas()

4. BOTONES MÁGICOS TÉRMICOS:
   - Calentar (×1.5) / Enfriar (×0.8) el gas en vivo
   - Método: escalar_velocidades(factor)
   - Delegado: Visualizador._conectar_botones()

5. MEDIDOR DE PRESIÓN MACROSCÓPICA:
   - Calcula P = Impulso_pared / (dt × perímetro)
   - Campo: presion_actual (actualizado cada paso)
   - Delegado: Visualizador._actualizar_textos()

ESTRUCTURA DE EJECUCIÓN:
========================
paso_simulacion():
  1. Actualizar posiciones (cinemática Euler)
  2. Detectar/resolver colisiones entre partículas
  3. Detectar/resolver colisiones con fronteras
  4. Calcular presión macroscópica (Módulo 5)
  5. Registrar magnitudes conservadas (Módulos 1, 2)
  
ejecutar(num_pasos, mostrar=True):
  - Si mostrar=True: Ejecuta animar_en_vivo() con todos los módulos
  - Si mostrar=False: Solo calcula sin renderizar
"""

import numpy as np
from typing import List, Tuple
from src.modelo.particula import Particula
from src.modelo.motor_fisico import MotorFisico
from src.modelo.contenedor import Contenedor
from src.vista import Visualizador


class Simulador:
    """Orquesta la simulación física integrando detección de colisiones, 
    cálculos macroscópicos y renderización de 5 módulos visuales.
    
    Flujo de ejecución:
    ===================
    1. Agregar partículas con agregar_particula()
    2. Ejecutar simulación con ejecutar(num_pasos)
    3. Visualizador renderiza automáticamente con todos los módulos
    
    Atributos clave:
    ================
    - particulas: Lista de objetos Particula en la simulación
    - contenedor: Dominio rectangular con límites
    - dt: Paso temporal de integración (segundos)
    - presion_actual: Presión macroscópica instantánea (Pa)
    - historico_momentos: Lista de |P_total| por paso
    - historico_energias: Lista de Ek_total por paso
    """
    
    def __init__(
        self,
        contenedor: Contenedor,
        dt: float = 0.01,
        ancho_dominio: float = 10.0,
        alto_dominio: float = 10.0
    ) -> None:
        """Inicializa simulador con contenedor y visualizador.
        
        INTEGRACIÓN CON MÓDULOS:
        ========================
        - Visualizador se crea aquí para los 5 módulos
        - Paso de tiempo dt afecta el cálculo de presión (Módulo 5)
        
        Args:
            contenedor: Objeto Contenedor que define el dominio rectangular
            dt: Paso temporal (segundos) para integración Euler. Default: 0.01s
            ancho_dominio: Ancho del dominio en metros (para visualización)
            alto_dominio: Alto del dominio en metros (para visualización)
        """
        self.contenedor: Contenedor = contenedor
        self.dt: float = dt
        
        # ========== PARTÍCULAS Y IDENTIFICADORES ==========
        self.particulas: List[Particula] = []      # Todas las partículas activas
        self.contador_id: int = 0                  # Identificador auto-incremental
        
        # ========== VISUALIZADOR (TODOS LOS 5 MÓDULOS) ==========
        self.visualizador: Visualizador = Visualizador(ancho_dominio, alto_dominio)
        
        # ========== HISTÓRICOS DE MAGNITUDES CONSERVADAS ==========
        # Módulo 1: Momento (para gráfico y verificación visual)
        self.historico_momentos: List[float] = []
        
        # Módulo 1: Energía cinética (para gráfico y análisis elástico/inelástico)
        self.historico_energias: List[float] = []
        
        # Posiciones por paso (para reproducción de animación posterior)
        self.historico_posiciones: List[List[np.ndarray]] = []
        
        # Velocidades por paso (para Módulo 2: Histograma y Módulo 3: Colores)
        self.historico_velocidades: List[List[np.ndarray]] = []
        
        # ========== VARIABLES TERMODINÁMICAS MACROSCÓPICAS (MÓDULO 5) ==========
        self.presion_actual: float = 0.0            # Presión instantánea (Pa)
        self.impulso_pared_acumulado: float = 0.0  # Impulso acumulado en este paso
    
    def agregar_particula(
        self,
        posicion: np.ndarray,
        velocidad: np.ndarray,
        masa: float,
        radio: float,
        coef_restitution: float = 1.0,
        color: str = 'blue'
    ) -> None:
        """Agrega una partícula a la simulación.
        
        La partícula se registra internamente con un ID único auto-incremental
        y se incluye en todos los cálculos posteriores (colisiones, presión, etc).
        
        Args:
            posicion: np.ndarray([x, y]) - Coordenadas iniciales en metros
            velocidad: np.ndarray([vx, vy]) - Velocidad inicial en m/s
            masa: Masa de la partícula en kg
            radio: Radio de la esfera en metros
            coef_restitution: Coef. de restitución (0-1). Default: 1.0 (elástica)
            color: Color de visualización (no usado en Módulo 3, pero disponible)
        
        Ejemplo:
        --------
        sim.agregar_particula(
            posicion=np.array([2.0, 3.0]),
            velocidad=np.array([1.5, -0.5]),
            masa=0.5,
            radio=0.2,
            coef_restitution=1.0
        )
        """
        p: Particula = Particula(
            self.contador_id,
            posicion,
            velocidad,
            masa,
            radio,
            coef_restitution,
            color
        )
        self.particulas.append(p)
        self.contador_id += 1
        
        # Actualizar históricos para la nueva partícula
        # Rellenar frames anteriores con posición inicial y velocidad 0
        num_frames_existentes = len(self.historico_posiciones)
        for i in range(num_frames_existentes):
            if i < len(self.historico_posiciones):
                # Agregar posición inicial a frame anterior
                frame_pos = np.asarray(self.historico_posiciones[i])
                if frame_pos.size == 0:
                    self.historico_posiciones[i] = np.array([posicion.copy()])
                else:
                    self.historico_posiciones[i] = np.vstack([
                        frame_pos,
                        posicion.copy()
                    ])
            if i < len(self.historico_velocidades):
                # Agregar velocidad 0 a frame anterior
                frame_vel = np.asarray(self.historico_velocidades[i])
                if frame_vel.size == 0:
                    self.historico_velocidades[i] = np.array([[0.0, 0.0]])
                else:
                    self.historico_velocidades[i] = np.vstack([
                        frame_vel,
                        np.array([0.0, 0.0])
                    ])
    
    def calcular_momento_total(self) -> float:
        """Calcula la magnitud del momento lineal total.
        
        MÓDULO 1: ECUACIONES DINÁMICAS
        ==============================
        Fórmula: P_total = √[(Σ m_i·vx_i)² + (Σ m_i·vy_i)²]
        
        El momento se conserva exactamente en colisiones entre partículas
        (es una ley fundamental de la física). Ante colisiones con paredes,
        el momento disminuye debido a que las paredes absorben impulso.
        
        Returns:
            float: Magnitud del momento total en kg·m/s
        """
        # Calcular cantidad de movimiento de cada partícula: p_i = m_i * v_i
        momentos: List[np.ndarray] = [p.calcular_cantidad_movimiento() for p in self.particulas]
        
        # Sumar todos los vectores: P_total = Σ p_i
        p_total: np.ndarray = np.sum(momentos, axis=0)
        
        # Retornar magnitud (norma euclidiana)
        return float(np.linalg.norm(p_total))
    
    def calcular_energia_total(self) -> float:
        """Calcula la energía cinética total del sistema.
        
        MÓDULO 1: ECUACIONES DINÁMICAS
        ==============================
        Fórmula: Ek_total = Σ (0.5 * m_i * |v_i|²)
        
        En colisiones ELÁSTICAS (e=1.0): Ek se conserva
        En colisiones INELÁSTICAS (e<1.0): Ek disminuye por fricción
        
        Returns:
            float: Energía cinética total en Joules
        """
        return sum(p.calcular_energia_cinetica() for p in self.particulas)

    def escalar_velocidades(self, factor: float) -> None:
        """Escala TODAS las velocidades por un factor multiplicativo.
        
        MÓDULO 4: BOTONES MÁGICOS DE CONTROL TÉRMICO
        ============================================
        
        Implementa la operación de "Hot Reloading" térmica:
        - Calentar: factor = 1.5 (sube velocidades 50%)
        - Enfriar: factor = 0.8 (baja velocidades 20%)
        
        Efecto observado en vivo:
        1. Módulo 2 (Histograma): Desplazamiento abrupto de la distribución
        2. Módulo 3 (Colores): Cambio de coloración del gas
        3. Módulo 5 (Presión): Cambio brusco de presión macroscópica
        
        Matemáticamente:
        - Nueva Ek = Ek_anterior × factor²
        - Nueva Presión ∝ factor² (para gas ideal)
        
        Args:
            factor: Factor multiplicativo (float > 0)
                   Recomendado: 1.5 (calentar), 0.8 (enfriar)
        """
        for p in self.particulas:
            p.velocidad *= factor
    
    def paso_simulacion(self) -> None:
        """Ejecuta UN paso de la simulación física.
        
        ALGORITMO COMPLETO DE INTEGRACIÓN (Euler Explícito):
        ====================================================
        
        Paso 1. CINEMÁTICA (Euler):
        ──────────────────────────
        Actualiza posición de cada partícula:
        x_{n+1} = x_n + v_n * dt
        
        Paso 2. COLISIONES INTER-PARTÍCULAS:
        ────────────────────────────────────
        Para cada par (i, j) con i < j:
        - Detecta: ||p_i - p_j|| < r_i + r_j
        - Resuelve: Aplica impulso basado en coef. restitución
        - Conserva: Momento lineal exactamente
        
        Paso 3. COLISIONES CON FRONTERAS:
        ─────────────────────────────────
        Para cada partícula:
        - Detecta: x ± r fuera de [0, L] o y ± r fuera de [0, H]
        - Resuelve: Rebote elástico o inelástico
        - Acumula: Impulso transferido a paredes (para Módulo 5)
        
        Paso 4. CÁLCULO DE PRESIÓN (MÓDULO 5):
        ──────────────────────────────────────
        Presión lineal instantánea:
        P = Impulso_pared / (dt × perímetro_contenedor)
        
        Unidades: N/m = (kg·m/s) / (s × m)
        (equivale a Pa si se asume profundidad unitaria)
        
        Interpretación física:
        - Más colisiones con paredes → Mayor presión
        - Gas caliente → Mayor presión
        - Gas frío → Menor presión
        
        Paso 5. REGISTRO DE MAGNITUDES (MÓDULOS 1 Y 2):
        ──────────────────────────────────────────────
        - Momento: Para gráfico de conservación
        - Energía: Para gráfico de disipación/conservación
        - Posiciones: Para animación posterior
        """
        # ===== PASO 1: CINEMÁTICA =====
        for p in self.particulas:
            p.actualizar_posicion(self.dt)
        
        # ===== PASO 2: COLISIONES ENTRE PARTÍCULAS =====
        for i in range(len(self.particulas)):
            for j in range(i + 1, len(self.particulas)):
                if MotorFisico.detectar_colision(self.particulas[i], self.particulas[j]):
                    MotorFisico.resolver_colision(self.particulas[i], self.particulas[j])
        
        # ===== PASO 3 + 4: COLISIONES CON FRONTERAS Y PRESIÓN =====
        self.impulso_pared_acumulado = 0.0
        for p in self.particulas:
            if self.contenedor.detectar_colision_frontera(p):
                # resolver_colision_frontera retorna el impulso transferido
                self.impulso_pared_acumulado += self.contenedor.resolver_colision_frontera(p)
        
        # Calcular presión macroscópica instantánea (Módulo 5)
        # P = (impulso total / dt) / perímetro
        self.presion_actual: float = (
            self.impulso_pared_acumulado / (self.dt * self.contenedor.perimetro)
        )
        
        # ===== PASO 5: REGISTRAR MAGNITUDES =====
        # Módulo 1: Momento para gráfico
        self.historico_momentos.append(self.calcular_momento_total())
        
        # Módulo 1: Energía para gráfico
        self.historico_energias.append(self.calcular_energia_total())
        
        # Guardar posiciones para animación posterior
        posiciones_actuales: List[np.ndarray] = [
            p.posicion.copy() for p in self.particulas
        ]
        self.historico_posiciones.append(posiciones_actuales)
        
        # Guardar velocidades para Módulo 2 (Histograma) y Módulo 3 (Colores)
        velocidades_actuales: List[np.ndarray] = [
            p.velocidad.copy() for p in self.particulas
        ]
        self.historico_velocidades.append(velocidades_actuales)
    
    def ejecutar(self, num_pasos: int, mostrar: bool = True) -> None:
        """Ejecuta la simulación completa con TODOS los 5 módulos integrados.
        
        MODOS DE EJECUCIÓN:
        ===================
        
        Modo 1: VISUAL EN VIVO (mostrar=True)
        ────────────────────────────────────
        - Simula y renderiza simultáneamente
        - Todos los 5 módulos se actualizan frame-a-frame
        - Controles interactivos habilitados
        - Botones térmicos activos (Módulo 4)
        
        Modo 2: BATCH/HEADLESS (mostrar=False)
        ─────────────────────────────────────
        - Solo ejecuta física, sin renderizar
        - Más rápido (sin overhead de gráficos)
        - Datos guardados en históricos
        - Útil para validación numérica
        
        Args:
            num_pasos: Número de pasos de simulación a ejecutar
            mostrar: True = Modo visual en vivo
                     False = Modo batch sin visualización
        """
        # Limpiar históricos anteriores
        self.historico_momentos.clear()
        self.historico_energias.clear()
        self.historico_posiciones.clear()
        self.historico_velocidades.clear()
        self.presion_actual = 0.0
        self.impulso_pared_acumulado = 0.0
        
        if mostrar:
            # ===== MODO VISUAL EN VIVO (TODOS LOS 5 MÓDULOS) =====
            # Crea figura de matplotlib
            self.visualizador.crear_figura()
            
            # Inicia animación en vivo con control interactivo
            # Esta función maneja:
            # - Módulo 1: Ecuaciones dinámicas LaTeX
            # - Módulo 2: Histograma Maxwell-Boltzmann
            # - Módulo 3: Colormap térmico
            # - Módulo 4: Botones calentar/enfriar
            # - Módulo 5: Presión macroscópica
            self.visualizador.animar_en_vivo(self, num_pasos)
        else:
            # ===== MODO BATCH (SOLO FÍSICA) =====
            # Ejecuta todos los pasos sin visualización
            for _ in range(num_pasos):
                self.paso_simulacion()
    
    def limpiar(self) -> None:
        """Limpia estado completo de la simulación.
        
        Resetea:
        - Todas las partículas
        - Contadores de ID
        - Históricos de magnitudes
        - Variables termodinámicas
        
        Útil para ejecutar múltiples simulaciones secuenciales
        sin interferencia de datos anteriores.
        """
        self.particulas.clear()
        self.contador_id = 0
        self.historico_momentos.clear()
        self.historico_energias.clear()
        self.historico_posiciones.clear()
        self.historico_velocidades.clear()
        self.presion_actual = 0.0
        self.impulso_pared_acumulado = 0.0
