"""Controlador: orquestación de la simulación."""

import numpy as np
from typing import List, Tuple
from src.modelo.particula import Particula
from src.modelo.motor_fisico import MotorFisico
from src.modelo.contenedor import Contenedor
from src.vista import Visualizador


class Simulador:
    """Orquesta la simulación: actualiza estado, detecta/resuelve colisiones, visualiza."""
    
    def __init__(
        self,
        contenedor: Contenedor,
        dt: float = 0.01,
        ancho_dominio: float = 10.0,
        alto_dominio: float = 10.0
    ) -> None:
        """Inicializa simulador.
        
        Args:
            contenedor: Dominio físico
            dt: Paso de tiempo (segundos)
            ancho_dominio: Para visualización
            alto_dominio: Para visualización
        """
        self.contenedor = contenedor
        self.dt = dt
        self.particulas: List[Particula] = []
        self.contador_id = 0
        self.visualizador = Visualizador(ancho_dominio, alto_dominio)
        self.historico_momentos: List[float] = []
        self.historico_energias: List[float] = []
        self.historico_posiciones: List[List[np.ndarray]] = []  # Posiciones por paso
        # Variables termodinámicas macroscópicas
        self.presion_actual: float = 0.0
        self.impulso_pared_acumulado: float = 0.0
    
    def agregar_particula(
        self,
        posicion: np.ndarray,
        velocidad: np.ndarray,
        masa: float,
        radio: float,
        coef_restitution: float = 1.0,
        color: str = 'blue'
    ) -> None:
        """Agrega particula a la simulación."""
        p = Particula(
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
    
    def calcular_momento_total(self) -> float:
        """Retorna magnitud del momento total."""
        momentos = [p.calcular_cantidad_movimiento() for p in self.particulas]
        p_total = np.sum(momentos, axis=0)
        return float(np.linalg.norm(p_total))
    
    def calcular_energia_total(self) -> float:
        """Retorna energía cinética total."""
        return sum(p.calcular_energia_cinetica() for p in self.particulas)

    def escalar_velocidades(self, factor: float) -> None:
        """Escala todas las velocidades por un factor (calentamiento/enfriamiento)."""
        for p in self.particulas:
            p.velocidad *= factor
    
    def paso_simulacion(self) -> None:
        """Ejecuta un paso: cinemática → colisiones → límites → registro."""
        # 1. Actualizar posiciones
        for p in self.particulas:
            p.actualizar_posicion(self.dt)
        
        # 2. Detectar y resolver colisiones entre partículas
        for i in range(len(self.particulas)):
            for j in range(i + 1, len(self.particulas)):
                if MotorFisico.detectar_colision(self.particulas[i], self.particulas[j]):
                    MotorFisico.resolver_colision(self.particulas[i], self.particulas[j])
        
        # 3. Resolver colisiones con fronteras y acumular impulso
        # Acumulador de impulso transferido a las paredes en este paso
        self.impulso_pared_acumulado = 0.0
        for p in self.particulas:
            if self.contenedor.detectar_colision_frontera(p):
                self.impulso_pared_acumulado += self.contenedor.resolver_colision_frontera(p)
        # Presión macroscópica instantánea: P = (impulso / dt) / perímetro
        self.presion_actual = self.impulso_pared_acumulado / (self.dt * self.contenedor.perimetro)
        
        # 4. Registrar magnitudes
        self.historico_momentos.append(self.calcular_momento_total())
        self.historico_energias.append(self.calcular_energia_total())
        
        # 5. Guardar posiciones actuales para animación
        posiciones_actuales = [p.posicion.copy() for p in self.particulas]
        self.historico_posiciones.append(posiciones_actuales)
    
    def ejecutar(self, num_pasos: int, mostrar: bool = True) -> None:
        """Ejecuta simulación y muestra visualización animada.
        
        Args:
            num_pasos: Número de pasos a simular
            mostrar: Si True, muestra animación con matplotlib. Si False, solo calcula sin visualizar
        """
        self.historico_momentos.clear()
        self.historico_energias.clear()
        self.historico_posiciones.clear()
        self.presion_actual = 0.0
        self.impulso_pared_acumulado = 0.0
        
        if mostrar:
            # Modo en vivo: simula y renderiza en el mismo loop para habilitar interacción
            self.visualizador.crear_figura()
            self.visualizador.animar_en_vivo(self, num_pasos)
        else:
            # Modo batch: solo calcula sin visualizar
            for _ in range(num_pasos):
                self.paso_simulacion()
    
    def limpiar(self) -> None:
        """Limpia partículas y datos de simulación anterior."""
        self.particulas.clear()
        self.contador_id = 0
        self.historico_momentos.clear()
        self.historico_energias.clear()
        self.historico_posiciones.clear()
        self.presion_actual = 0.0
        self.impulso_pared_acumulado = 0.0
