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
from src.modelo.particula import Particula

if TYPE_CHECKING:
    from src.controlador.simulador import Simulador


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
        """Dibuja todas las partículas con código de colores térmico dinámico.
        
        MÓDULO 3: CÓDIGO DE COLORES POR ENERGÍA (Termalización)
        =========================================================
        
        El color de cada esfera depende de su magnitud de velocidad instantánea:
        - AZUL (v baja):     Partícula frenada/fría, Ek baja
        - VERDE/AMARILLO:    Partícula a velocidad promedio, Ek media
        - ROJO (v alta):     Partícula eyectada/caliente, Ek alta
        
        Fórmula de color: c = colormap(v_mag / v_max_actual)
        
        Esto permite visualizar en vivo:
        - Calentamiento del gas: más partículas viran de azul a rojo
        - Enfriamiento del gas: más partículas viran de rojo a azul
        - Zonas de colisión: cambios abruptos de color entre partículas
        
        Args:
            particulas: Lista de partículas a renderizar
        """
        if self.ax_sim is None:
            return
        
        self.ax_sim.clear()
        self.ax_sim.set_xlim(0, self.ancho)
        self.ax_sim.set_ylim(0, self.alto)
        self.ax_sim.set_aspect('equal')
        self.ax_sim.set_title('Simulación 2D - Partículas codificadas por temperatura (color)')
        self.ax_sim.grid(True, alpha=0.3)

        # ========== CÁLCULO DE NORMALIZACIÓN TÉRMICA ==========
        # Obtiene magnitudes de velocidad de todas las partículas
        velocidades: List[float] = [float(np.linalg.norm(p.velocidad)) for p in particulas]
        
        # Normalización: mapear velocidades a rango [0, 1] para el colormap
        vmax: float = max(velocidades) if velocidades else 1.0
        vmax = max(vmax, 1e-6)  # Evita división por cero
        
        # ========== RENDERIZADO DE CADA PARTÍCULA ==========
        for p, vmag in zip(particulas, velocidades):
            # Índice de color normalizado: 0 (frío/azul) a 1 (caliente/rojo)
            indice_color: float = min(vmag / vmax, 1.0)
            color = self.colormap(indice_color)
            
            # Dibujar círculo con color térmico
            circle = Circle(
                p.posicion,
                p.radio,
                facecolor=color,
                alpha=0.8,
                edgecolor='black',
                linewidth=2
            )
            self.ax_sim.add_patch(circle)
            
            # Etiqueta con ID de partícula (texto blanco para contraste)
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
        """Actualiza gráficos de magnitudes conservadas.
        
        Muestra la evolución temporal de:
        - Momento lineal total: |P| = |Σ m_i * v_i|
        - Energía cinética total: Ek = Σ (0.5 * m_i * v_i²)
        
        Args:
            momentos: Lista de valores de momento por paso
            energias: Lista de valores de energía por paso
        """
        if self.ax_momento is None or self.ax_energia is None:
            return
        
        # ========== GRÁFICO DE MOMENTO LINEAL TOTAL ==========
        self.ax_momento.clear()
        self.ax_momento.plot(momentos, 'b-', linewidth=2, label='|P_total|')
        self.ax_momento.set_xlabel('Paso temporal')
        self.ax_momento.set_ylabel('Momento |P| (kg·m/s)')
        self.ax_momento.set_title('Momento Lineal Total (Conservado)')
        self.ax_momento.grid(True, alpha=0.3)
        self.ax_momento.legend()
        if momentos:
            self.ax_momento.set_ylim(0, max(momentos) * 1.1)
        
        # ========== GRÁFICO DE ENERGÍA CINÉTICA TOTAL ==========
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
        """Actualiza histograma de velocidades en tiempo real.
        
        MÓDULO 2: HISTOGRAMA MAXWELL-BOLTZMANN
        ======================================
        
        Muestra la distribución instantánea de magnitudes de velocidad de todas
        las partículas activas. La forma del histograma converge hacia una curva
        de Maxwell-Boltzmann en sistemas en equilibrio termodinámico.
        
        Comportamiento en eventos:
        - Colisión elástica (e=1.0): Redistribuye velocidades, forma se mantiene
        - Calentamiento (×1.5): Histograma se desplaza hacia la derecha
        - Enfriamiento (×0.8): Histograma se desplaza hacia la izquierda
        - Sistema masivo: Converge hacia Maxwell-Boltzmann
        
        Los ejes X e Y son ESTABLES para evitar parpadeos:
        - Eje X: [0, 15] m/s (límite superior fijo)
        - Eje Y: [0, max(N_particulas, 10)] (reescala solo cuando necesario)
        
        Args:
            particulas: Lista de partículas cuyas velocidades se analizan
        """
        if self.ax_hist is None:
            return

        # Calcula magnitudes de velocidad para cada partícula
        velocidades: List[float] = [float(np.linalg.norm(p.velocidad)) for p in particulas]
        
        # Limpiar histograma anterior
        self.ax_hist.clear()
        
        # Crear histograma con bins estables
        self.ax_hist.hist(
            velocidades,
            bins=self.hist_bins,
            range=(0, self.hist_xmax),  # Rango fijo para evitar reescalado
            color='#4e79a7',              # Azul acero (color de barras)
            alpha=0.7,
            edgecolor='black',
            linewidth=1.5
        )
        
        self.ax_hist.set_title('Distribución de Velocidades (Maxwell-Boltzmann)')
        self.ax_hist.set_xlabel('Magnitud de velocidad v (m/s)')
        self.ax_hist.set_ylabel('Frecuencia (# partículas)')
        
        # Límites estables en X
        self.ax_hist.set_xlim(0, self.hist_xmax)
        
        # Límites dinámicos pero suavizados en Y
        self.hist_ymax = max(self.hist_ymax, len(particulas) + 1)
        self.ax_hist.set_ylim(0, self.hist_ymax)
        
        self.ax_hist.grid(True, alpha=0.3)

    def _construir_texto_ecuaciones(self, particulas: List[Particula]) -> str:
        """Construye texto LaTeX con desglose numérico de ecuaciones en vivo.
        
        MÓDULO 1: ECUACIONES DINÁMICAS EN PANTALLA (LaTeX)
        ==================================================
        
        Muestra frame-a-frame la sustitución de valores en dos ecuaciones clave:
        
        1. MOMENTO LINEAL TOTAL (CONSERVADO en colisiones)
           P_total = (m₁·vₓ₁) + (m₂·vₓ₂) = [Resultado] kg·m/s
           
           El usuario observa cómo las velocidades vₓ cambien en el impacto,
           pero el RESULTADO TOTAL permanece exactamente constante (salvo en
           colisiones con paredes, donde se disipa).
        
        2. ENERGÍA CINÉTICA TOTAL
           Ek_total = (0.5·m₁·v₁²) + (0.5·m₂·v₂²) = [Resultado] J
           
           Evidencia en vivo:
           - Choque ELÁSTICO (e=1.0): Ek se conserva exactamente
           - Choque INELÁSTICO (e<1.0): Ek decae instantáneamente
        
        Args:
            particulas: Lista de partículas para calcular magnitudes
            
        Returns:
            String con LaTeX renderizable para ax.text()
        """
        if len(particulas) < 2:
            return r"$\text{⚠ Agrega al menos 2 partículas para ver el desglose}$"

        # Obtener referencias a las dos primeras partículas (para ejemplo visual)
        p1, p2 = particulas[0], particulas[1]
        m1: float = float(p1.masa)
        m2: float = float(p2.masa)
        vx1: float = float(p1.velocidad[0])
        vx2: float = float(p2.velocidad[0])
        
        # Magnitudes de velocidad (para Energía)
        v1: float = float(np.linalg.norm(p1.velocidad))
        v2: float = float(np.linalg.norm(p2.velocidad))
        
        # Contribución del resto de partículas (para mantener igualdad)
        resto: List[Particula] = particulas[2:]
        p_resto_x: float = sum(p.masa * p.velocidad[0] for p in resto)
        ek_resto: float = sum(0.5 * p.masa * np.dot(p.velocidad, p.velocidad) for p in resto)
        
        # Totales calculados
        p_total_x: float = m1 * vx1 + m2 * vx2 + p_resto_x
        ek_total: float = 0.5 * m1 * (v1 ** 2) + 0.5 * m2 * (v2 ** 2) + ek_resto

        # Formateo de término adicional si hay más de 2 partículas
        resto_p_str: str = f" + ({p_resto_x:.2f})" if resto else ""
        resto_ek_str: str = f" + ({ek_resto:.2f})" if resto else ""

        # ========== ECUACIÓN 1: MOMENTO LINEAL TOTAL ==========
        linea_p: str = (
            r"$P_{total} = (m_1 v_{x1}) + (m_2 v_{x2})"
                + resto_p_str
                + rf" = ({m1:.2f} \cdot {vx1:.2f}) + ({m2:.2f} \cdot {vx2:.2f})"
                + resto_p_str
                + rf" = {p_total_x:.2f}\,\mathrm{{kg\,m/s}}$"
        )
        
        # ========== ECUACIÓN 2: ENERGÍA CINÉTICA TOTAL ==========
        linea_ek: str = (
            r"$E_k = \frac{1}{2}m_1 v_1^2 + \frac{1}{2}m_2 v_2^2"
                + resto_ek_str
                + rf" = (0.5 \cdot {m1:.2f} \cdot {v1:.2f}^2) + (0.5 \cdot {m2:.2f} \cdot {v2:.2f}^2)"
                + resto_ek_str
                + rf" = {ek_total:.2f}\,\mathrm{{J}}$"
        )
        
        return linea_p + "\n" + linea_ek

    def _actualizar_textos(self, particulas: List[Particula], presion: float) -> None:
        """Actualiza textos dinámicos de ecuaciones y presión macroscópica.
        
        MÓDULO 1 + MÓDULO 5: Integración de texto dinámico en panel principal
        =====================================================================
        
        Muestra dos paneles de información en el panel de simulación:
        
        1. ECUACIONES (arriba-izquierda):
           - Desglose frame-a-frame del Momento y Energía
           - Permite verificar visualmente la conservación
        
        2. PRESIÓN MACROSCÓPICA (abajo-izquierda):
           - Valor instantáneo calculado como: P = Impulso_pared / (dt × perímetro)
           - Sube cuando hay muchas colisiones con paredes
           - Cambia con calentamiento/enfriamiento del gas
        
        Args:
            particulas: Lista de partículas para ecuaciones
            presion: Presión macroscópica instantánea (Pa) calculada por motor físico
        """
        if self.ax_sim is None:
            return

        # ========== MÓDULO 1: ACTUALIZAR ECUACIONES DINÁMICAS ==========
        texto_ecuaciones: str = self._construir_texto_ecuaciones(particulas)
        
        if self._texto_ecuaciones is None:
            # Primera vez: crear objeto de texto
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
            # Actualizar contenido
            self._texto_ecuaciones.set_text(texto_ecuaciones)

        # ========== MÓDULO 5: ACTUALIZAR PRESIÓN MACROSCÓPICA ==========
        texto_presion: str = (
            f"💨 Presión Macroscópica: {presion:.2f} Pa\n"
            f"   [Impulso/Perímetro/dt]"
        )
        
        if self._texto_presion is None:
            # Primera vez: crear objeto de texto
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
            # Actualizar contenido
            self._texto_presion.set_text(texto_presion)

    def _conectar_botones(self, simulador: 'Simulador') -> None:
        """Conecta callbacks a botones de control térmico.
        
        MÓDULO 4: BOTONES MÁGICOS DE CONTROL TÉRMICO (Hot Reloading)
        ============================================================
        
        Implementa dos operaciones que modifican instantáneamente el estado
        térmico del gas en plena simulación:
        
        1. BOTÓN "Calentar Gas" (naranja):
           - Multiplica vectorialmente todas las velocidades por 1.5
           - Efecto: Sistema se descontrola, velocidades suben 50%
           - En histograma: Desplazamiento abrupto a la derecha
           - En color: Más partículas pasan de azul/verde a rojo
           - Físicamente: Inyección de energía térmica
        
        2. BOTÓN "Enfriar Gas" (azul):
           - Multiplica todas las velocidades por 0.8
           - Efecto: Sistema se ralentiza, velocidades bajan 20%
           - En histograma: Desplazamiento abrupto a la izquierda
           - En color: Más partículas pasan de rojo a verde/azul
           - Físicamente: Extracción de energía térmica
        
        Ambos efectos son INSTANTÁNEOS y permiten visualizar en vivo cómo
        responden los sistemas dinámicos (Ek, Presión, Distribución) a
        cambios abruptos de temperatura.
        
        Args:
            simulador: Referencia al simulador para escalar velocidades
        """
        if self._boton_calentar is None or self._boton_enfriar is None:
            return

        def calentar(event) -> None:
            """Callback: Calentar gas × 1.5"""
            simulador.escalar_velocidades(1.5)
            print("🔥 ¡GAS CALENTADO! Velocidades multiplicadas por 1.5")

        def enfriar(event) -> None:
            """Callback: Enfriar gas × 0.8"""
            simulador.escalar_velocidades(0.8)
            print("❄️ ¡GAS ENFRIADO! Velocidades multiplicadas por 0.8")
        self._boton_calentar.on_clicked(calentar)
        self._boton_enfriar.on_clicked(enfriar)

    def animar_en_vivo(self, simulador: 'Simulador', num_pasos: int) -> None:
        """Simula y renderiza en vivo con todos los módulos integrados.
        
        MODO EN VIVO: INTEGRACIÓN DE TODOS LOS MÓDULOS
        ===============================================
        
        Este método ejecuta la simulación física en tiempo real mientras renderiza
        cinco módulos simultáneamente:
        
        1. ECUACIONES DINÁMICAS (LaTeX):
           - Momento total frame-a-frame
           - Energía cinética frame-a-frame
           - Ubicación: Arriba-izquierda del panel principal
        
        2. HISTOGRAMA MAXWELL-BOLTZMANN:
           - Distribución instantánea de velocidades
           - Se actualiza cada frame
           - Ubicación: Panel superior-derecho
        
        3. CÓDIGO DE COLORES TÉRMICO:
           - Partículas cambian color según velocidad instantánea
           - Azul = frío (v baja)
           - Rojo = caliente (v alta)
           - Ubicación: Panel principal izquierdo
        
        4. BOTONES TÉRMICOS:
           - Calentar Gas (×1.5): Inyecta energía instantáneamente
           - Enfriar Gas (×0.8): Extrae energía instantáneamente
           - Ubicación: Parte inferior de la interfaz
        
        5. PRESIÓN MACROSCÓPICA:
           - Cálculo instantáneo de P = Impulso / (dt × perímetro)
           - Ubicación: Abajo-izquierda del panel principal
        
        CONTROLES INTERACTIVOS:
        =======================
        - ESPACIO: Pausar/Reanudar animación
        - +/=: Acelerar animación (2×, máximo 16×)
        - -: Desacelerar animación (0.5×, mínimo 0.25×)
        - K: Calentar Gas (×1.5) - Atajo de teclado
        - L: Enfriar Gas (×0.8) - Atajo de teclado
        - ESC/Q: Cerrar simulación
        
        Args:
            simulador: Referencia al controlador Simulador
            num_pasos: Número total de pasos a simular
        """
        if self.ax_sim is None:
            return

        # ========== CONECTAR BOTONES TÉRMICOS ==========
        self._conectar_botones(simulador)

        # ========== ESTADO INTERACTIVO ==========
        state: dict = {
            'paused': bool(False),                    # ¿Está pausada?
            'speed_multiplier': float(1.0),          # Factor de velocidad de reproducción
            'should_exit': bool(False)                # ¿Debe cerrarse?
        }

        def on_key(event) -> None:
            """Manejador de eventos de teclado durante animación en vivo."""
            if event.key == ' ':  # ESPACIO
                state['paused'] = not state['paused']
                estado_texto: str = "PAUSADA ⏸️" if state['paused'] else "REPRODUCIENDO ▶️"
                print(f"→ Simulación {estado_texto}")
                
            elif event.key in ['+', '=']:  # Acelerar
                state['speed_multiplier'] = min(state['speed_multiplier'] * 2, 16)
                print(f"⏩ Velocidad de animación: {state['speed_multiplier']:.1f}×")
                
            elif event.key == '-':  # Desacelerar
                state['speed_multiplier'] = max(state['speed_multiplier'] / 2, 0.25)
                print(f"⏪ Velocidad de animación: {state['speed_multiplier']:.1f}×")
                
            elif event.key == 'k':  # Atajo: Calentar
                simulador.escalar_velocidades(1.5)
                print("🔥 ¡GAS CALENTADO! (atajo K)")
                
            elif event.key == 'l':  # Atajo: Enfriar
                simulador.escalar_velocidades(0.8)
                print("❄️ ¡GAS ENFRIADO! (atajo L)")
                
            elif event.key in ['escape', 'q']:  # Cerrar
                state['should_exit'] = True
                print("🛑 Cerrando simulación...")
                if self.fig:
                    plt.close(self.fig)

        # Conectar manejador de teclado
        if self.fig:
            self.fig.canvas.mpl_connect('key_press_event', on_key)

        # ========== MOSTRAR INSTRUCCIONES ==========
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

        # ========== LOOP PRINCIPAL DE ANIMACIÓN EN VIVO ==========
        pasos_ejecutados: int = 0
        
        while pasos_ejecutados < num_pasos:
            if state['should_exit']:
                break

            # Ejecutar paso de simulación si NO está pausado
            if not state['paused']:
                simulador.paso_simulacion()
                pasos_ejecutados += 1

            # ========== MÓDULO 3: RENDERIZAR PARTICULAS CON COLORMAP TÉRMICO ==========
            self.dibujar_particulas(simulador.particulas)

            # ========== MÓDULO 2: ACTUALIZAR HISTOGRAMA MAXWELL-BOLTZMANN ==========
            self._actualizar_histograma(simulador.particulas)

            # ========== ACTUALIZAR GRÁFICOS DE CONSERVACIÓN ==========
            self.actualizar_graficos(simulador.historico_momentos, simulador.historico_energias)

            # ========== MÓDULOS 1 + 5: ECUACIONES Y PRESIÓN ==========
            self._actualizar_textos(simulador.particulas, simulador.presion_actual)

            # Ajustar layout y pausar para reproducción
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
