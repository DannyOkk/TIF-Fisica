"""Vista: Visualización con matplotlib."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button
from typing import List, Optional, TYPE_CHECKING
from src.modelo.particula import Particula

if TYPE_CHECKING:
    from src.controlador.simulador import Simulador


class Visualizador:
    """Renderiza simulación con matplotlib.
    
    Muestra:
    - Panel izquierdo: Simulación 2D con partículas y fórmulas en vivo
    - Panel derecho arriba: Histograma de velocidades (Maxwell-Boltzmann)
    - Panel derecho medio: Momento lineal total
    - Panel derecho abajo: Energía cinética total
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
        self.ax_hist: Optional[plt.Axes] = None
        self.ax_momento: Optional[plt.Axes] = None
        self.ax_energia: Optional[plt.Axes] = None
        self._texto_ecuaciones = None
        self._texto_presion = None
        self._boton_calentar: Optional[Button] = None
        self._boton_enfriar: Optional[Button] = None
        # Configuración del histograma (estable, sin reescalado brusco)
        self.hist_bins = 20
        self.hist_xmax = 15.0
        self.hist_ymax = 10.0
        # Colormap térmico personalizado: azul -> amarillo -> rojo
        self.colormap = LinearSegmentedColormap.from_list(
            "termico",
            ["#1f77ff", "#f7d154", "#d62728"]
        )
    
    def crear_figura(self) -> None:
        """Crea estructura de gráficos."""
        self.fig = plt.figure(figsize=(16, 8))
        self.fig.suptitle(self.titulo, fontsize=14, fontweight='bold')

        # Gridspec para paneles: izquierda (simulación) ocupa 3 filas
        gs = self.fig.add_gridspec(3, 2, width_ratios=[2.2, 1.0], height_ratios=[1, 1, 1])

        # Simulación 2D
        self.ax_sim = self.fig.add_subplot(gs[:, 0])
        self.ax_sim.set_xlim(0, self.ancho)
        self.ax_sim.set_ylim(0, self.alto)
        self.ax_sim.set_aspect('equal')
        self.ax_sim.set_xlabel('x (m)')
        self.ax_sim.set_ylabel('y (m)')
        self.ax_sim.set_title('Simulación 2D')
        self.ax_sim.grid(True, alpha=0.3)

        # Histograma de velocidades
        self.ax_hist = self.fig.add_subplot(gs[0, 1])
        self.ax_hist.set_title('Histograma de Velocidades')
        self.ax_hist.set_xlabel('v (m/s)')
        self.ax_hist.set_ylabel('Frecuencia')
        self.ax_hist.grid(True, alpha=0.3)

        # Momento
        self.ax_momento = self.fig.add_subplot(gs[1, 1])
        self.ax_momento.set_xlabel('Pasos')
        self.ax_momento.set_ylabel('Momento (kg·m/s)')
        self.ax_momento.set_title('Momento Lineal Total')
        self.ax_momento.grid(True, alpha=0.3)

        # Energía
        self.ax_energia = self.fig.add_subplot(gs[2, 1])
        self.ax_energia.set_xlabel('Pasos')
        self.ax_energia.set_ylabel('Energía (J)')
        self.ax_energia.set_title('Energía Cinética Total')
        self.ax_energia.grid(True, alpha=0.3)

        # Crear botones térmicos en la parte inferior del panel derecho
        boton_calentar_ax = self.fig.add_axes([0.72, 0.01, 0.12, 0.05])
        boton_enfriar_ax = self.fig.add_axes([0.86, 0.01, 0.12, 0.05])
        self._boton_calentar = Button(boton_calentar_ax, 'Calentar Gas')
        self._boton_enfriar = Button(boton_enfriar_ax, 'Enfriar Gas')
    
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

        # Normalización de velocidades para el colormap térmico
        velocidades = [np.linalg.norm(p.velocidad) for p in particulas]
        vmax = max(velocidades) if velocidades else 1.0
        vmax = max(vmax, 1e-6)

        for p, vmag in zip(particulas, velocidades):
            # Color térmico según velocidad instantánea
            color = self.colormap(min(vmag / vmax, 1.0))
            circle = Circle(
                p.posicion,
                p.radio,
                facecolor=color,
                alpha=0.8,
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

    def _actualizar_histograma(self, particulas: List[Particula]) -> None:
        """Actualiza el histograma de velocidades en tiempo real."""
        if self.ax_hist is None:
            return

        velocidades = [np.linalg.norm(p.velocidad) for p in particulas]
        self.ax_hist.clear()
        self.ax_hist.hist(velocidades, bins=self.hist_bins, range=(0, self.hist_xmax), color='#4e79a7')
        self.ax_hist.set_title('Histograma de Velocidades')
        self.ax_hist.set_xlabel('v (m/s)')
        self.ax_hist.set_ylabel('Frecuencia')
        self.ax_hist.set_xlim(0, self.hist_xmax)
        # Fija el eje Y para evitar parpadeo
        self.hist_ymax = max(self.hist_ymax, len(particulas) + 1)
        self.ax_hist.set_ylim(0, self.hist_ymax)
        self.ax_hist.grid(True, alpha=0.3)

    def _construir_texto_ecuaciones(self, particulas: List[Particula]) -> str:
        """Construye texto LaTeX con el desglose de P_total y Ek_total."""
        if len(particulas) < 2:
            return r"$\text{Agrega al menos 2 partículas para el desglose}$"

        p1, p2 = particulas[0], particulas[1]
        m1, m2 = p1.masa, p2.masa
        vx1, vx2 = p1.velocidad[0], p2.velocidad[0]
        v1 = float(np.linalg.norm(p1.velocidad))
        v2 = float(np.linalg.norm(p2.velocidad))
        # Contribución del resto de partículas para mantener la igualdad del total
        resto = particulas[2:]
        p_resto_x = sum(p.masa * p.velocidad[0] for p in resto)
        ek_resto = sum(0.5 * p.masa * np.dot(p.velocidad, p.velocidad) for p in resto)
        p_total_x = m1 * vx1 + m2 * vx2 + p_resto_x
        ek_total = 0.5 * m1 * v1 ** 2 + 0.5 * m2 * v2 ** 2 + ek_resto

        resto_p = f" + ({p_resto_x:.2f})" if resto else ""
        resto_ek = f" + ({ek_resto:.2f})" if resto else ""

        # Ecuaciones en LaTeX con sustitución numérica
        linea_p = (
            r"$P_{total} = (m_1 v_{x1}) + (m_2 v_{x2}) = "
                + f"({m1:.2f} \\cdot {vx1:.2f}) + ({m2:.2f} \\cdot {vx2:.2f})"
                + f"{resto_p} = {p_total_x:.2f}\\,\\mathrm{{kg\\,m/s}}$"
        )
        linea_ek = (
            r"$E_{k\,total} = \frac{1}{2} m_1 v_1^2 + \frac{1}{2} m_2 v_2^2 = "
                + f"(0.5 \\cdot {m1:.2f} \\cdot {v1:.2f}^2) + (0.5 \\cdot {m2:.2f} \\cdot {v2:.2f}^2)"
                + f"{resto_ek} = {ek_total:.2f}\\,\\mathrm{{J}}$"
        )
        return linea_p + "\n" + linea_ek

    def _actualizar_textos(self, particulas: List[Particula], presion: float) -> None:
        """Actualiza los textos de ecuaciones y presión dentro del panel principal."""
        if self.ax_sim is None:
            return

        texto = self._construir_texto_ecuaciones(particulas)
        if self._texto_ecuaciones is None:
            self._texto_ecuaciones = self.ax_sim.text(
                0.02,
                0.98,
                texto,
                transform=self.ax_sim.transAxes,
                ha='left',
                va='top',
                fontsize=9,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )
        else:
            self._texto_ecuaciones.set_text(texto)

        texto_presion = f"Presión: {presion:.2f} Pa"
        if self._texto_presion is None:
            self._texto_presion = self.ax_sim.text(
                0.02,
                0.02,
                texto_presion,
                transform=self.ax_sim.transAxes,
                ha='left',
                va='bottom',
                fontsize=10,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )
        else:
            self._texto_presion.set_text(texto_presion)

    def _conectar_botones(self, simulador: 'Simulador') -> None:
        """Conecta callbacks de botones térmicos a la simulación."""
        if self._boton_calentar is None or self._boton_enfriar is None:
            return

        def calentar(_event) -> None:
            # Multiplica velocidades para simular calentamiento abrupto
            simulador.escalar_velocidades(1.5)

        def enfriar(_event) -> None:
            # Reduce velocidades para simular enfriamiento del gas
            simulador.escalar_velocidades(0.8)

        self._boton_calentar.on_clicked(calentar)
        self._boton_enfriar.on_clicked(enfriar)

    def animar_en_vivo(self, simulador: 'Simulador', num_pasos: int) -> None:
        """Simula y renderiza en vivo para permitir interacción térmica.
        
        Controles:
        - ESPACIO: Pausar/Reanudar
        - +/=: Acelerar 2x
        - -: Desacelerar 0.5x
        - ESC/Q: Cerrar animación
        """
        if self.ax_sim is None:
            return

        # Conectar botones térmicos a la simulación
        self._conectar_botones(simulador)

        state = {
            'paused': False,
            'speed_multiplier': 1.0,
            'should_exit': False
        }

        def on_key(event):
            if event.key == ' ':
                state['paused'] = not state['paused']
            elif event.key in ['+', '=']:
                state['speed_multiplier'] = min(state['speed_multiplier'] * 2, 16)
            elif event.key == '-':
                state['speed_multiplier'] = max(state['speed_multiplier'] / 2, 0.25)
            elif event.key == 'k':
                simulador.escalar_velocidades(1.5)
            elif event.key == 'l':
                simulador.escalar_velocidades(0.8)
            elif event.key in ['escape', 'q']:
                state['should_exit'] = True
                plt.close(self.fig)

        self.fig.canvas.mpl_connect('key_press_event', on_key)

        # Mostrar instrucciones en consola
        print("\n" + "=" * 60)
        print("CONTROLES INTERACTIVOS DE ANIMACIÓN (MODO EN VIVO)")
        print("=" * 60)
        print("  ESPACIO: Pausar/Reanudar")
        print("  +/-: Acelerar/Desacelerar")
        print("  K: Calentar Gas (x1.5)")
        print("  L: Enfriar Gas (x0.8)")
        print("  ESC/Q: Cerrar animación")
        print("=" * 60 + "\n")

        pasos_ejecutados = 0
        while pasos_ejecutados < num_pasos:
            if state['should_exit']:
                break

            if not state['paused']:
                # Ejecutar un paso de simulación en vivo
                simulador.paso_simulacion()
                pasos_ejecutados += 1

            # Panel principal: partículas con colormap térmico
            self.dibujar_particulas(simulador.particulas)

            # Histograma de velocidades
            self._actualizar_histograma(simulador.particulas)

            # Gráficos de momento y energía
            self.actualizar_graficos(simulador.historico_momentos, simulador.historico_energias)

            # Ecuaciones y presión en vivo
            self._actualizar_textos(simulador.particulas, simulador.presion_actual)

            if self.fig:
                self.fig.subplots_adjust(left=0.06, right=0.98, top=0.94, bottom=0.08)
            plt.pause(0.05 / state['speed_multiplier'])

        self.mostrar()
    
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
            velocidades_frame = [float(np.linalg.norm(p.velocidad)) for p in particulas]
            vmax_frame = max(velocidades_frame) if velocidades_frame else 1.0
            vmax_frame = max(vmax_frame, 1e-6)
            for i, p in enumerate(particulas):
                posicion = historico_posiciones[frame_idx][i]
                # Color térmico basado en velocidad actual del frame
                vmag = float(np.linalg.norm(p.velocidad))
                color = self.colormap(min(vmag / vmax_frame, 1.0))
                circle = Circle(
                    posicion,
                    p.radio,
                    facecolor=color,
                    alpha=0.8,
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
            
            if self.fig:
                self.fig.subplots_adjust(left=0.06, right=0.98, top=0.94, bottom=0.08)
            
            # Calcular tiempo de pausa ajustado por velocidad
            pause_time = 0.05 / state['speed_multiplier']  # 50ms ajustado
            plt.pause(pause_time)
        
        self.mostrar()
    
    def mostrar(self) -> None:
        """Muestra la figura."""
        if self.fig:
            self.fig.subplots_adjust(left=0.06, right=0.98, top=0.94, bottom=0.08)
            plt.show()
