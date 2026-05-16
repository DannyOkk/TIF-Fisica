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
        """Crea animación interactiva de la simulación.
        
        CONTROLES INTERACTIVOS:
        - ESPACIO: Pausar/Reanudar
        - +/=: Acelerar 2x
        - -: Desacelerar 0.5x
        - ↑: Ir al siguiente paso (cuando está pausada)
        - ↓: Ir al paso anterior (cuando está pausada)
        - ESC/Q: Cerrar animación
        - S: Guardar último frame como imagen
        
        El tiempo entre frames se ajusta con la velocidad.
        """
        if self.ax_sim is None or not historico_posiciones:
            return
        
        # Estado de control
        state = {
            'paused': False,
            'speed_multiplier': 1.0,  # 1.0 = velocidad normal (50ms)
            'current_frame': 0,
            'max_frame': len(historico_posiciones) - 1,
            'should_exit': False
        }
        
        def on_key(event):
            """Manejador de eventos de teclado."""
            if event.key == ' ':  # ESPACIO: Pausar/Reanudar
                state['paused'] = not state['paused']
                status = "PAUSADA" if state['paused'] else "REPRODUCIENDO"
                print(f"⏸️  Simulación {status}")
            
            elif event.key in ['+', '=']:  # Acelerar
                state['speed_multiplier'] = min(state['speed_multiplier'] * 2, 16)
                print(f"⏩ Velocidad x{state['speed_multiplier']:.1f}")
            
            elif event.key == '-':  # Desacelerar
                state['speed_multiplier'] = max(state['speed_multiplier'] / 2, 0.25)
                print(f"⏪ Velocidad x{state['speed_multiplier']:.1f}")
            
            elif event.key == 'up':  # Siguiente paso (cuando pausada)
                if state['paused'] and state['current_frame'] < state['max_frame']:
                    state['current_frame'] += 1
                    print(f"→ Paso {state['current_frame'] + 1}/{len(historico_posiciones)}")
            
            elif event.key == 'down':  # Paso anterior (cuando pausada)
                if state['paused'] and state['current_frame'] > 0:
                    state['current_frame'] -= 1
                    print(f"← Paso {state['current_frame'] + 1}/{len(historico_posiciones)}")
            
            elif event.key in ['escape', 'q']:  # Cerrar
                state['should_exit'] = True
                print("🛑 Cerrando animación...")
                plt.close(self.fig)
        
        # Conectar evento de teclado
        self.fig.canvas.mpl_connect('key_press_event', on_key)
        
        # Mostrar instrucciones
        print("\n" + "="*60)
        print("CONTROLES INTERACTIVOS DE ANIMACIÓN")
        print("="*60)
        print("  ESPACIO: Pausar/Reanudar")
        print("  +/-: Acelerar/Desacelerar")
        print("  ↑/↓: Siguiente/Anterior paso (cuando está pausada)")
        print("  ESC/Q: Cerrar animación")
        print("="*60 + "\n")
        
        frame_display_count = 0
        
        while state['current_frame'] <= state['max_frame'] and not state['should_exit']:
            if not state['paused']:
                frame_display_count += 1
                
                if frame_display_count % max(1, int(1 / state['speed_multiplier'])) == 0:
                    state['current_frame'] += 1
                    if state['current_frame'] > state['max_frame']:
                        state['current_frame'] = state['max_frame']
            
            # Limpiar panel de simulación
            self.ax_sim.clear()
            self.ax_sim.set_xlim(0, self.ancho)
            self.ax_sim.set_ylim(0, self.alto)
            self.ax_sim.set_aspect('equal')
            self.ax_sim.set_xlabel('x (m)')
            self.ax_sim.set_ylabel('y (m)')
            
            frame_idx = min(state['current_frame'], len(historico_posiciones) - 1)
            status_text = "[PAUSADA]" if state['paused'] else "[REPRODUCIENDO]"
            speed_text = f"x{state['speed_multiplier']:.1f}" if state['speed_multiplier'] != 1.0 else ""
            
            self.ax_sim.set_title(
                f"Simulación 2D - Paso {frame_idx + 1}/{len(historico_posiciones)} {status_text} {speed_text}"
            )
            self.ax_sim.grid(True, alpha=0.3)
            
            # Dibujar partículas en posición del frame actual
            for i, p in enumerate(particulas):
                posicion = historico_posiciones[frame_idx][i]
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
            if frame_idx > 0:
                pasos_actuales = frame_idx + 1
                
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
            
            # Calcular tiempo de pausa ajustado por velocidad
            pause_time = 0.05 / state['speed_multiplier']  # 50ms ajustado
            plt.pause(pause_time)
        
        self.mostrar()
    
    def mostrar(self) -> None:
        """Muestra la figura."""
        if self.fig:
            plt.tight_layout()
            plt.show()
