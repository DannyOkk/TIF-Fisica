"""Vista: Visualización con matplotlib."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from typing import List, Optional
from src.modelo.particula import Particula


class Visualizador:
    """Renderiza simulación con matplotlib.
    
    Muestra:
    - Panel izquierdo: Simulación 2D con partículas
    - Panel derecho arriba: Gráfico de momento en tiempo
    - Panel derecho abajo: Gráfico de energía en tiempo
    """
    
    def __init__(
        self,
        ancho_dominio: float,
        alto_dominio: float,
        titulo: str = "Simulador de Colisiones 2D"
    ) -> None:
        self.ancho = ancho_dominio
        self.alto = alto_dominio
        self.titulo = titulo
        self.fig: Optional[plt.Figure] = None
        self.ax_sim: Optional[plt.Axes] = None
        self.ax_momento: Optional[plt.Axes] = None
        self.ax_energia: Optional[plt.Axes] = None
    
    def crear_figura(self) -> None:
        """Crea estructura de gráficos."""
        self.fig = plt.figure(figsize=(14, 6))
        self.fig.suptitle(self.titulo, fontsize=14, fontweight='bold')
        
        # Simulación 2D
        self.ax_sim = plt.subplot(1, 2, 1)
        self.ax_sim.set_xlim(0, self.ancho)
        self.ax_sim.set_ylim(0, self.alto)
        self.ax_sim.set_aspect('equal')
        self.ax_sim.set_xlabel('x (m)')
        self.ax_sim.set_ylabel('y (m)')
        self.ax_sim.set_title('Simulación 2D')
        self.ax_sim.grid(True, alpha=0.3)
        
        # Gráficos de tiempo
        right_panel = plt.subplot(1, 2, 2)
        right_panel.axis('off')
        
        # Momento
        self.ax_momento = plt.subplot(2, 2, 2)
        self.ax_momento.set_xlabel('Pasos')
        self.ax_momento.set_ylabel('Momento (kg·m/s)')
        self.ax_momento.set_title('Momento Lineal Total')
        self.ax_momento.grid(True, alpha=0.3)
        
        # Energía
        self.ax_energia = plt.subplot(2, 2, 4)
        self.ax_energia.set_xlabel('Pasos')
        self.ax_energia.set_ylabel('Energía (J)')
        self.ax_energia.set_title('Energía Cinética Total')
        self.ax_energia.grid(True, alpha=0.3)
    
    def dibujar_particulas(self, particulas: List[Particula]) -> None:
        """Dibuja todas las partículas en el panel de simulación."""
        if self.ax_sim is None:
            return
        
        self.ax_sim.clear()
        self.ax_sim.set_xlim(0, self.ancho)
        self.ax_sim.set_ylim(0, self.alto)
        self.ax_sim.set_aspect('equal')
        self.ax_sim.set_title('Simulación 2D')
        self.ax_sim.grid(True, alpha=0.3)
        
        for p in particulas:
            circle = Circle(
                p.posicion,
                p.radio,
                color=p.color,
                alpha=0.7,
                edgecolor='black',
                linewidth=2
            )
            self.ax_sim.add_patch(circle)
            # Etiqueta con ID
            self.ax_sim.text(
                p.posicion[0],
                p.posicion[1],
                str(p.id),
                ha='center',
                va='center',
                fontsize=8,
                color='white',
                fontweight='bold'
            )
    
    def actualizar_graficos(
        self,
        momentos: List[float],
        energias: List[float]
    ) -> None:
        """Actualiza gráficos de magnitudes conservadas."""
        if self.ax_momento is None or self.ax_energia is None:
            return
        
        # Momento
        self.ax_momento.clear()
        self.ax_momento.plot(momentos, 'b-', linewidth=2, label='|P_total|')
        self.ax_momento.set_xlabel('Pasos')
        self.ax_momento.set_ylabel('Momento (kg·m/s)')
        self.ax_momento.set_title('Momento Lineal Total')
        self.ax_momento.grid(True, alpha=0.3)
        self.ax_momento.legend()
        
        # Energía
        self.ax_energia.clear()
        self.ax_energia.plot(energias, 'r-', linewidth=2, label='E_cinética')
        self.ax_energia.set_xlabel('Pasos')
        self.ax_energia.set_ylabel('Energía (J)')
        self.ax_energia.set_title('Energía Cinética Total')
        self.ax_energia.grid(True, alpha=0.3)
        self.ax_energia.legend()
    
    def animar(
        self,
        particulas: List[Particula],
        historico_posiciones: List[List[np.ndarray]],
        momentos: List[float],
        energias: List[float]
    ) -> None:
        """Crea animación de la simulación paso a paso."""
        if self.ax_sim is None or not historico_posiciones:
            return
        
        # Mostrar cada frame con pausa
        for frame in range(len(historico_posiciones)):
            # Limpiar panel de simulación
            self.ax_sim.clear()
            self.ax_sim.set_xlim(0, self.ancho)
            self.ax_sim.set_ylim(0, self.alto)
            self.ax_sim.set_aspect('equal')
            self.ax_sim.set_xlabel('x (m)')
            self.ax_sim.set_ylabel('y (m)')
            self.ax_sim.set_title(f'Simulación 2D - Paso {frame + 1}/{len(historico_posiciones)}')
            self.ax_sim.grid(True, alpha=0.3)
            
            # Dibujar partículas en posición del frame actual
            for i, p in enumerate(particulas):
                posicion = historico_posiciones[frame][i]
                circle = Circle(
                    posicion,
                    p.radio,
                    facecolor=p.color,
                    alpha=0.7,
                    edgecolor='black',
                    linewidth=2
                )
                self.ax_sim.add_patch(circle)
                self.ax_sim.text(
                    posicion[0],
                    posicion[1],
                    str(p.id),
                    ha='center',
                    va='center',
                    fontsize=8,
                    color='white',
                    fontweight='bold'
                )
            
            # Actualizar gráficos de magnitudes hasta el frame actual
            if frame > 0:
                pasos_actuales = frame + 1
                
                # Momento
                self.ax_momento.clear()
                self.ax_momento.plot(momentos[:pasos_actuales], 'b-', linewidth=2, label='|P_total|')
                self.ax_momento.set_xlabel('Pasos')
                self.ax_momento.set_ylabel('Momento (kg·m/s)')
                self.ax_momento.set_title('Momento Lineal Total')
                self.ax_momento.grid(True, alpha=0.3)
                self.ax_momento.legend()
                if momentos[:pasos_actuales]:
                    self.ax_momento.set_ylim(0, max(momentos[:pasos_actuales]) * 1.1)
                
                # Energía
                self.ax_energia.clear()
                self.ax_energia.plot(energias[:pasos_actuales], 'r-', linewidth=2, label='E_cinética')
                self.ax_energia.set_xlabel('Pasos')
                self.ax_energia.set_ylabel('Energía (J)')
                self.ax_energia.set_title('Energía Cinética Total')
                self.ax_energia.grid(True, alpha=0.3)
                self.ax_energia.legend()
                if energias[:pasos_actuales]:
                    self.ax_energia.set_ylim(0, max(energias[:pasos_actuales]) * 1.1)
            
            plt.tight_layout()
            plt.pause(0.05)  # 50ms de pausa entre frames
        
        self.mostrar()
    
    def mostrar(self) -> None:
        """Muestra la figura."""
        if self.fig:
            plt.tight_layout()
            plt.show()
