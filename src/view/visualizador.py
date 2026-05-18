"""Vista: Visualización con matplotlib.

Módulos implementados:
======================
1. ECUACIONES DINÁMICAS EN PANTALLA (LaTeX): Muestra el desglose en vivo de Momento y Energía.
2. HISTOGRAMA MAXWELL-BOLTZMANN: Visualiza la distribución de velocidades instantánea.
3. CÓDIGO DE COLORES TÉRMICO: Partículas se colorean según su energía cinética.
4. BOTONES DE CONTROL TÉRMICO: Calentar (×1.5) y Enfriar (×0.8) el gas en vivo.
5. MEDIDOR DE PRESIÓN MACROSCÓPICA: Calcula y muestra presión en tiempo real.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button
from typing import List, Optional, Tuple, TYPE_CHECKING
from src.model.particula import Particula

if TYPE_CHECKING:
    from src.controller.simulador import Simulador


class Visualizador:
    """Renderiza simulación con matplotlib integrando múltiples módulos físicos.
    
    Estructura de paneles:
    ======================
    - IZQUIERDA (3 filas): Simulación 2D con partículas codificadas por color térmico
                          + ecuaciones dinámicas LaTeX (Momento y Energía)
                          + medidor de presión macroscópica
    - DERECHA SUPERIOR:    Histograma de velocidades (Maxwell-Boltzmann en vivo)
    - DERECHA MEDIO:       Gráfico de Momento Lineal Total vs pasos
    - DERECHA INFERIOR:    Gráfico de Energía Cinética Total vs pasos
    
    Controles interactivos:
    =======================
    - Botón "Calentar Gas":  ×1.5 velocidades (desplaza histograma a la derecha)
    - Botón "Enfriar Gas":   ×0.8 velocidades (desplaza histograma a la izquierda)
    - Teclas +/-: Acelerar/Desacelerar animación
    - Tecla ESPACIO: Pausar/Reanudar
    - K/L: Atajos para calentar/enfriar
    - ESC/Q: Cerrar simulación
    """
    
    def __init__(
        self,
        ancho_dominio: float,
        alto_dominio: float,
        titulo: str = "Simulador de Colisiones 2D"
    ) -> None:
        """Inicializa el visualizador con estructura de paneles múltiples.
        
        MÓDULO 3: Colormap térmico (azul=frío, verde/amarillo=templado, rojo=caliente)
        MÓDULO 1: Texto dinámico para ecuaciones LaTeX de Momento y Energía
        MÓDULO 2: Histograma con bins estables para Maxwell-Boltzmann
        MÓDULO 5: Medidor de presión instantánea
        MÓDULO 4: Botones para Calentar/Enfriar gas
        
        Args:
            ancho_dominio: Ancho del contenedor en metros (eje X)
            alto_dominio: Alto del contenedor en metros (eje Y)
            titulo: Título de la ventana de simulación
        """
        self.ancho: float = ancho_dominio
        self.alto: float = alto_dominio
        self.titulo: str = titulo
        
        # Atributos de figura y ejes (None hasta que se cree la figura)
        self.fig: Optional[plt.Figure] = None
        self.ax_sim: Optional[plt.Axes] = None      # Panel principal de simulación
        self.ax_hist: Optional[plt.Axes] = None     # Histograma de velocidades (Módulo 2)
        self.ax_momento: Optional[plt.Axes] = None  # Gráfico de momento
        self.ax_energia: Optional[plt.Axes] = None  # Gráfico de energía
        
        # MÓDULO 1: Objetos de texto para ecuaciones dinámicas en LaTeX
        self._texto_ecuaciones: Optional[plt.Text] = None  # Desglose de P_total y E_k
        self._texto_presion: Optional[plt.Text] = None     # Indicador de presión macroscópica
        
        # MÓDULO 4: Botones de control térmico
        self._boton_calentar: Optional[Button] = None  # Botón "Calentar Gas"
        self._boton_enfriar: Optional[Button] = None   # Botón "Enfriar Gas"
        
        # MÓDULO 2: Configuración del histograma (estable, sin reescalado brusco)
        self.hist_bins: int = 20                 # Número de barras del histograma
        self.hist_xmax: float = 15.0            # Límite superior del eje X (m/s)
        self.hist_ymax: float = 10.0            # Límite superior dinámico del eje Y
        
        # MÓDULO 3: Colormap térmico personalizado para código de colores por energía
        # Escala: Azul (frío, v baja) → Amarillo (templado, v media) → Rojo (caliente, v alta)
        self.colormap: LinearSegmentedColormap = LinearSegmentedColormap.from_list(
            "termico",
            ["#1f77ff", "#f7d154", "#d62728"]  # Azul, Amarillo, Rojo
        )
    
    def crear_figura(self) -> None:
        """Crea la estructura de gráficos con GridSpec.
        
        LAYOUT:
        =======
        ┌─────────────────────────┬───────────┐
        │                         │ HISTOGR.  │ (Módulo 2: Maxwell-Boltzmann)
        │  SIM. 2D                │           │
        │  (Módulo 3:             ├───────────┤
        │   Colores Térmicos)     │ MOMENTO   │
        │  (Módulo 1:             │           │
        │   Ecuaciones LaTeX)     ├───────────┤
        │  (Módulo 5:             │ ENERGÍA   │
        │   Presión)              │           │
        ├─────────────────────────┴───────────┤
        │ [Calentar Gas] [Enfriar Gas]         │ (Módulo 4: Botones Térmicos)
        └─────────────────────────────────────┘
        
        Los paneles derechos (Histograma, Momento, Energía) se sincronizan en vivo
        durante la simulación para mostrar la evolución termodinámica.
        """
        # Crear figura principal con escala de 16:8 (proporción 2:1)
        self.fig = plt.figure(figsize=(16, 8))
        self.fig.suptitle(self.titulo, fontsize=14, fontweight='bold')

        # GridSpec: columna izquierda ocupa 2.2 unidades (más ancha),
        #           columna derecha ocupa 1.0 unidad (más estrecha)
        gs = self.fig.add_gridspec(3, 2, width_ratios=[2.2, 1.0], height_ratios=[1, 1, 1])

        # ========== PANEL IZQUIERDO (SIMULACIÓN 2D) ==========
        # Ocupa todas las 3 filas de la columna izquierda
        self.ax_sim = self.fig.add_subplot(gs[:, 0])
        self.ax_sim.set_xlim(0, self.ancho)
        self.ax_sim.set_ylim(0, self.alto)
        self.ax_sim.set_aspect('equal')  # Mantiene proporciones de esferas
        self.ax_sim.set_xlabel('x (m)')
        self.ax_sim.set_ylabel('y (m)')
        self.ax_sim.set_title('Simulación 2D - Partículas codificadas por temperatura (color)')
        self.ax_sim.grid(True, alpha=0.3)

        # ========== PANEL DERECHO SUPERIOR (HISTOGRAMA) ==========
        # Módulo 2: Histograma dinámico de velocidades
        self.ax_hist = self.fig.add_subplot(gs[0, 1])
        self.ax_hist.set_title('Distribución de Velocidades (Maxwell-Boltzmann)')
        self.ax_hist.set_xlabel('Magnitud de velocidad v (m/s)')
        self.ax_hist.set_ylabel('Frecuencia (# partículas)')
        self.ax_hist.grid(True, alpha=0.3)

        # ========== PANEL DERECHO MEDIO (MOMENTO) ==========
        self.ax_momento = self.fig.add_subplot(gs[1, 1])
        self.ax_momento.set_xlabel('Paso temporal')
        self.ax_momento.set_ylabel('Momento |P| (kg·m/s)')
        self.ax_momento.set_title('Momento Lineal Total')
        self.ax_momento.grid(True, alpha=0.3)

        # ========== PANEL DERECHO INFERIOR (ENERGÍA) ==========
        self.ax_energia = self.fig.add_subplot(gs[2, 1])
        self.ax_energia.set_xlabel('Paso temporal')
        self.ax_energia.set_ylabel('Energía Ek (J)')
        self.ax_energia.set_title('Energía Cinética Total')
        self.ax_energia.grid(True, alpha=0.3)

        # ========== MÓDULO 4: BOTONES DE CONTROL TÉRMICO ==========
        # Ubicados en la parte inferior de la interfaz
        boton_calentar_ax = self.fig.add_axes([0.72, 0.01, 0.12, 0.05])
        boton_enfriar_ax = self.fig.add_axes([0.86, 0.01, 0.12, 0.05])
        self._boton_calentar = Button(boton_calentar_ax, 'Calentar Gas', color='#ff7f0e')
        self._boton_enfriar = Button(boton_enfriar_ax, 'Enfriar Gas', color='#1f77ff')
    
    def dibujar_particulas(self, particulas: List[Particula]) -> None:
        """Dibuja todas las partículas con código de colores térmico dinámico."""
        if self.ax_sim is None:
            return
        
        self.ax_sim.clear()
        self.ax_sim.set_xlim(0, self.ancho)
        self.ax_sim.set_ylim(0, self.alto)
        self.ax_sim.set_aspect('equal')
        self.ax_sim.set_title('Simulación 2D - Partículas codificadas por temperatura (color)')
        self.ax_sim.grid(True, alpha=0.3)

        velocidades: List[float] = [float(np.linalg.norm(p.velocidad)) for p in particulas]
        
        vmax: float = max(velocidades) if velocidades else 1.0
        vmax = max(vmax, 1e-6)
        
        for p, vmag in zip(particulas, velocidades):
            indice_color: float = min(vmag / vmax, 1.0)
            color = self.colormap(indice_color)
            
            circle = Circle(
                p.posicion,
                p.radio,
                facecolor=color,
                alpha=0.8,
                edgecolor='black',
                linewidth=2
            )
            self.ax_sim.add_patch(circle)
            
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
        
        self.ax_momento.clear()
        self.ax_momento.plot(momentos, 'b-', linewidth=2, label='|P_total|')
        self.ax_momento.set_xlabel('Paso temporal')
        self.ax_momento.set_ylabel('Momento |P| (kg·m/s)')
        self.ax_momento.set_title('Momento Lineal Total (Conservado)')
        self.ax_momento.grid(True, alpha=0.3)
        self.ax_momento.legend()
        if momentos:
            self.ax_momento.set_ylim(0, max(momentos) * 1.1)
        
        self.ax_energia.clear()
        self.ax_energia.plot(energias, 'r-', linewidth=2, label='E_cinética')
        self.ax_energia.set_xlabel('Paso temporal')
        self.ax_energia.set_ylabel('Energía Ek (J)')
        self.ax_energia.set_title('Energía Cinética Total')
        self.ax_energia.grid(True, alpha=0.3)
        self.ax_energia.legend()
        if energias:
            self.ax_energia.set_ylim(0, max(energias) * 1.1)

    def _actualizar_histograma(self, particulas: List[Particula]) -> None:
        """Actualiza histograma de velocidades en tiempo real."""
        if self.ax_hist is None:
            return

        velocidades: List[float] = [float(np.linalg.norm(p.velocidad)) for p in particulas]
        
        self.ax_hist.clear()
        
        self.ax_hist.hist(
            velocidades,
            bins=self.hist_bins,
            range=(0, self.hist_xmax),
            color='#4e79a7',
            alpha=0.7,
            edgecolor='black',
            linewidth=1.5
        )
        
        self.ax_hist.set_title('Distribución de Velocidades (Maxwell-Boltzmann)')
        self.ax_hist.set_xlabel('Magnitud de velocidad v (m/s)')
        self.ax_hist.set_ylabel('Frecuencia (# partículas)')
        
        self.ax_hist.set_xlim(0, self.hist_xmax)
        
        self.hist_ymax = max(self.hist_ymax, len(particulas) + 1)
        self.ax_hist.set_ylim(0, self.hist_ymax)
        
        self.ax_hist.grid(True, alpha=0.3)

    def _construir_texto_ecuaciones(self, particulas: List[Particula]) -> str:
        """Construye texto LaTeX con desglose numérico de ecuaciones en vivo."""
        if len(particulas) < 2:
            return r"$\text{⚠ Agrega al menos 2 partículas para ver el desglose}$"

        p1, p2 = particulas[0], particulas[1]
        m1: float = float(p1.masa)
        m2: float = float(p2.masa)
        vx1: float = float(p1.velocidad[0])
        vy1: float = float(p1.velocidad[1])
        vx2: float = float(p2.velocidad[0])
        vy2: float = float(p2.velocidad[1])
        
        v1: float = float(np.linalg.norm(p1.velocidad))
        v2: float = float(np.linalg.norm(p2.velocidad))
        
        resto: List[Particula] = particulas[2:]
        p_resto_x: float = sum(p.masa * p.velocidad[0] for p in resto)
        p_resto_y: float = sum(p.masa * p.velocidad[1] for p in resto)
        ek_resto: float = sum(0.5 * p.masa * np.dot(p.velocidad, p.velocidad) for p in resto)
        
        p_total_x: float = m1 * vx1 + m2 * vx2 + p_resto_x
        p_total_y: float = m1 * vy1 + m2 * vy2 + p_resto_y
        p_total_mag: float = float(np.sqrt(p_total_x ** 2 + p_total_y ** 2))
        ek_total: float = 0.5 * m1 * (v1 ** 2) + 0.5 * m2 * (v2 ** 2) + ek_resto

        resto_p_str_x: str = f" + ({p_resto_x:.2f})" if resto else ""
        resto_p_str_y: str = f" + ({p_resto_y:.2f})" if resto else ""
        resto_ek_str: str = f" + ({ek_resto:.2f})" if resto else ""

        linea_p: str = (
            r"$P_{total} = \sqrt{(m_1 v_{x1} + m_2 v_{x2}"
                + resto_p_str_x
                + r")^2 + (m_1 v_{y1} + m_2 v_{y2}"
                + resto_p_str_y
                + r")^2}"
                + rf" = \sqrt{{({p_total_x:.2f})^2 + ({p_total_y:.2f})^2}}"
                + rf" = {p_total_mag:.2f}\,\mathrm{{kg\,m/s}}$"
        )
        
        linea_ek: str = (
            r"$E_k = \frac{1}{2}m_1 v_1^2 + \frac{1}{2}m_2 v_2^2"
                + resto_ek_str
                + rf" = (0.5 \cdot {m1:.2f} \cdot {v1:.2f}^2) + (0.5 \cdot {m2:.2f} \cdot {v2:.2f}^2)"
                + resto_ek_str
                + rf" = {ek_total:.2f}\,\mathrm{{J}}$"
        )
        
        return linea_p + "\n" + linea_ek

    def _actualizar_textos(self, particulas: List[Particula], presion: float) -> None:
        """Actualiza textos dinámicos de ecuaciones y presión macroscópica."""
        if self.ax_sim is None:
            return

        texto_ecuaciones: str = self._construir_texto_ecuaciones(particulas)
        
        if self._texto_ecuaciones is None:
            self._texto_ecuaciones = self.ax_sim.text(
                0.02,
                0.98,
                texto_ecuaciones,
                transform=self.ax_sim.transAxes,
                ha='left',
                va='top',
                fontsize=9,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.85, edgecolor='black', linewidth=1.5)
            )
        else:
            self._texto_ecuaciones.set_text(texto_ecuaciones)

        texto_presion: str = (
            f"💨 Presión lineal: {presion:.2f} N/m\n"
            f"   [Impulso/Perímetro/dt]"
        )
        
        if self._texto_presion is None:
            self._texto_presion = self.ax_sim.text(
                0.02,
                0.02,
                texto_presion,
                transform=self.ax_sim.transAxes,
                ha='left',
                va='bottom',
                fontsize=10,
                bbox=dict(boxstyle='round', facecolor='#ffe6cc', alpha=0.85, edgecolor='black', linewidth=1.5),
                fontweight='bold'
            )
        else:
            self._texto_presion.set_text(texto_presion)

    def _conectar_botones(self, simulador: 'Simulador') -> None:
        """Conecta callbacks a botones de control térmico."""
        if self._boton_calentar is None or self._boton_enfriar is None:
            return

        def calentar(event) -> None:
            simulador.escalar_velocidades(1.5)
            print("🔥 ¡GAS CALENTADO! Velocidades multiplicadas por 1.5")

        def enfriar(event) -> None:
            simulador.escalar_velocidades(0.8)
            print("❄️ ¡GAS ENFRIADO! Velocidades multiplicadas por 0.8")
        self._boton_calentar.on_clicked(calentar)
        self._boton_enfriar.on_clicked(enfriar)

    def animar_en_vivo(self, simulador: 'Simulador', num_pasos: int) -> None:
        """Simula y renderiza en vivo con todos los módulos integrados."""
        if self.ax_sim is None:
            return

        self._conectar_botones(simulador)

        state: dict = {
            'paused': bool(False),
            'speed_multiplier': float(1.0),
            'should_exit': bool(False)
        }

        def on_key(event) -> None:
            if event.key == ' ':
                state['paused'] = not state['paused']
                estado_texto: str = "PAUSADA ⏸️" if state['paused'] else "REPRODUCIENDO ▶️"
                print(f"→ Simulación {estado_texto}")
                
            elif event.key in ['+', '=']:
                state['speed_multiplier'] = min(state['speed_multiplier'] * 2, 16)
                print(f"⏩ Velocidad de animación: {state['speed_multiplier']:.1f}×")
                
            elif event.key == '-':
                state['speed_multiplier'] = max(state['speed_multiplier'] / 2, 0.25)
                print(f"⏪ Velocidad de animación: {state['speed_multiplier']:.1f}×")
                
            elif event.key == 'k':
                simulador.escalar_velocidades(1.5)
                print("🔥 ¡GAS CALENTADO! (atajo K)")
                
            elif event.key == 'l':
                simulador.escalar_velocidades(0.8)
                print("❄️ ¡GAS ENFRIADO! (atajo L)")
                
            elif event.key in ['escape', 'q']:
                state['should_exit'] = True
                print("🛑 Cerrando simulación...")
                if self.fig:
                    plt.close(self.fig)

        if self.fig:
            self.fig.canvas.mpl_connect('key_press_event', on_key)

        print("\n" + "=" * 70)
        print("🎬 SIMULADOR EN VIVO - INTEGRACIÓN DE 5 MÓDULOS FÍSICOS")
        print("=" * 70)
        print("┌─── MÓDULOS ACTIVOS ──────────────────────────────────────┐")
        print("│ 1️⃣  ECUACIONES DINÁMICAS (LaTeX)  → Panel superior izq.   │")
        print("│ 2️⃣  HISTOGRAMA MAXWELL-BOLTZMANN  → Panel superior der.   │")
        print("│ 3️⃣  CÓDIGO TÉRMICO POR VELOCIDAD  → Colores en esferas   │")
        print("│ 4️⃣  BOTONES MÁGICOS TÉRMICOS      → Calentar/Enfriar    │")
        print("│ 5️⃣  PRESIÓN MACROSCÓPICA          → Abajo izquierda     │")
        print("└──────────────────────────────────────────────────────────┘")
        print("┌─── CONTROLES INTERACTIVOS ────────────────────────────────┐")
        print("│ ESPACIO    : Pausar/Reanudar                              │")
        print("│ +/-        : Acelerar/Desacelerar (×2 / ÷2)               │")
        print("│ K/L        : Calentar/Enfriar gas (×1.5 / ×0.8)            │")
        print("│ ESC/Q      : Cerrar simulación                            │")
        print("└──────────────────────────────────────────────────────────┘\n")

        pasos_ejecutados: int = 0
        
        while pasos_ejecutados < num_pasos:
            if state['should_exit']:
                break

            if not state['paused']:
                simulador.paso_simulacion()
                pasos_ejecutados += 1

            self.dibujar_particulas(simulador.particulas)
            self._actualizar_histograma(simulador.particulas)
            self.actualizar_graficos(simulador.historico_momentos, simulador.historico_energias)
            self._actualizar_textos(simulador.particulas, simulador.presion_actual)

            if self.fig:
                self.fig.subplots_adjust(left=0.06, right=0.98, top=0.94, bottom=0.08)
            plt.pause(0.05 / state['speed_multiplier'])

        self.mostrar()
    
    def mostrar(self) -> None:
        """Muestra la figura."""
        if self.fig:
            self.fig.subplots_adjust(left=0.06, right=0.98, top=0.94, bottom=0.08)
            plt.show()
