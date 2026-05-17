"""Servidor web Flask para interfaz gráfica de la simulación.

Interfaz profesional y optimizada con:
- Simulación 2D limpia y clara
- Panel de fórmulas con valores instantáneos
- Información de presión macroscópica
- Rendimiento optimizado (caché de frames)
"""

import json
import numpy as np
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from src.modelo.contenedor import Contenedor
from src.controlador.simulador import Simulador
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.gridspec import GridSpec
from io import BytesIO
import base64
import traceback

app = Flask(__name__)

# Variable global para almacenar simulación actual
current_sim = {
    'simulador': None,
    'historico': None,
    'frame': 0,
    'paused': True,
    'speed': 1.0
}

def cargar_escenario(nombre_archivo, num_pasos=300):
    """Carga un escenario JSON y retorna simulador.
    
    Args:
        nombre_archivo: Nombre del archivo JSON de escenario
        num_pasos: Número de pasos de simulación a ejecutar
    """
    try:
        ruta = Path(__file__).parent.parent / "scenarios" / nombre_archivo
        
        if not ruta.exists():
            return None, f"Archivo no encontrado: {nombre_archivo}"
        
        with open(ruta, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Crear simulador
        contenedor = Contenedor(
            ancho=datos.get("ancho_dominio", 10.0),
            alto=datos.get("alto_dominio", 10.0)
        )
        simulador = Simulador(
            contenedor,
            dt=datos.get("dt", 0.01),
            ancho_dominio=datos.get("ancho_dominio", 10.0),
            alto_dominio=datos.get("alto_dominio", 10.0)
        )
        
        # Agregar partículas
        for p in datos.get("particulas", []):
            simulador.agregar_particula(
                posicion=np.array(p["posicion"]),
                velocidad=np.array(p["velocidad"]),
                masa=p["masa"],
                radio=p["radio"],
                coef_restitution=p["e"],
                color=p["color"]
            )
        
        # Ejecutar simulación sin mostrar matplotlib (solo calcular)
        simulador.ejecutar(num_pasos, mostrar=False)
        
        return simulador, datos
    
    except Exception as e:
        return None, f"Error al cargar escenario: {str(e)}\n{traceback.format_exc()}"

def generar_frame_base64(simulador, frame_num):
    """Genera imagen Base64 con simulación MÁS GRANDE (90%) + gráficos compactos (10%).
    
    Layout:
    - Izquierda (90%): Simulación 2D MÁS GRANDE + Fórmulas dinámicas
    - Derecha (10%): Gráficos miniatura (Histograma, Momento, Energía)
    """
    try:
        if not simulador or frame_num >= len(simulador.historico_posiciones):
            return None
        
        plt.ioff()
        
        # Figura optimizada: 20x10 para máxima visibilidad de simulación
        fig = plt.figure(figsize=(20, 10), dpi=75)
        fig.patch.set_facecolor('white')
        
        # GridSpec: 2 columnas (izq 90%, der 10%), con filas para gráficos
        gs = GridSpec(4, 18, figure=fig, height_ratios=[3, 0.2, 0.5, 0.5], 
                     width_ratios=[1]*16 + [1, 1], hspace=0.3, wspace=0.25)
        
        # ===== IZQUIERDA ARRIBA: SIMULACIÓN 2D MÁS GRANDE =====
        ax_sim = fig.add_subplot(gs[0:2, 0:16])  # 16 columnas en izquierda, 2 filas
        historico = simulador.historico_posiciones[frame_num]
        colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for i, p in enumerate(simulador.particulas):
            circle = plt.Circle(
                historico[i],
                p.radio,
                facecolor=colores[i % len(colores)],
                alpha=0.85,
                edgecolor='black',
                linewidth=1.5
            )
            ax_sim.add_patch(circle)
        
        ax_sim.set_xlim(-0.5, simulador.contenedor.ancho + 0.5)
        ax_sim.set_ylim(-0.5, simulador.contenedor.alto + 0.5)
        ax_sim.set_aspect('equal')
        ax_sim.set_xlabel('x (m)', fontsize=12, fontweight='bold')
        ax_sim.set_ylabel('y (m)', fontsize=12, fontweight='bold')
        ax_sim.set_title(f'Simulación 2D - Frame {frame_num + 1}/{len(simulador.historico_posiciones)}', 
                        fontsize=14, fontweight='bold', pad=12)
        ax_sim.grid(True, alpha=0.2, linestyle='--')
        ax_sim.set_facecolor('#fafafa')
        
        # ===== IZQUIERDA ABAJO: FÓRMULAS DINÁMICAS (MÁS ABAJO) =====
        ax_formulas = fig.add_subplot(gs[2:4, 0:16])
        ax_formulas.axis('off')
        
        # Construir texto de fórmulas con valores actuales
        if frame_num > 0 and len(simulador.historico_velocidades[frame_num]) > 0:
            vel_actual = simulador.historico_velocidades[frame_num]
            mom_actual = simulador.historico_momentos[frame_num]
            ene_actual = simulador.historico_energias[frame_num]
            pres_actual = simulador.presion_actual
            
            texto = f"""Momento Total: |P| = {mom_actual:.4f} kg·m/s  |  Energía: E = {ene_actual:.4f} J  |  Presión: P = {pres_actual:.2f} Pa"""
        else:
            texto = "Cálculos en progreso..."
        
        ax_formulas.text(0.5, 0.6, texto, fontsize=11, family='monospace',
                        horizontalalignment='center', verticalalignment='center',
                        bbox=dict(boxstyle='round', facecolor='#e8f5e9', 
                        alpha=0.85, pad=0.8))
        
        # ===== DERECHA ARRIBA: HISTOGRAMA (MINIATURA) =====
        ax_hist = fig.add_subplot(gs[0, 16:18])
        velocidades_frame = simulador.historico_velocidades[frame_num] if frame_num < len(simulador.historico_velocidades) else []
        velocidades_mag = [np.linalg.norm(v) for v in velocidades_frame] if velocidades_frame else []
        
        if velocidades_mag:
            ax_hist.hist(velocidades_mag, bins=10, range=(0, 12), color='steelblue', 
                        edgecolor='black', alpha=0.7)
        ax_hist.set_xlabel('v (m/s)', fontsize=7)
        ax_hist.set_ylabel('Freq', fontsize=7)
        ax_hist.set_title('MB', fontsize=8, fontweight='bold')
        ax_hist.set_xlim(0, 12)
        ax_hist.grid(True, alpha=0.2, axis='y')
        ax_hist.tick_params(labelsize=6)
        
        # ===== DERECHA MEDIO: MOMENTO (MINIATURA) =====
        ax_momento = fig.add_subplot(gs[1, 16:18])
        frames_list = list(range(min(frame_num + 1, len(simulador.historico_momentos))))
        momentos_list = simulador.historico_momentos[:frame_num + 1]
        
        ax_momento.plot(frames_list, momentos_list, 'b-', linewidth=1)
        ax_momento.axvline(frame_num, color='red', linestyle='--', alpha=0.5, linewidth=0.8)
        ax_momento.set_xlabel('F', fontsize=7)
        ax_momento.set_ylabel('P', fontsize=7)
        ax_momento.set_title('Mom', fontsize=8, fontweight='bold')
        ax_momento.grid(True, alpha=0.2)
        ax_momento.tick_params(labelsize=6)
        
        # ===== DERECHA ABAJO: ENERGÍA (MINIATURA) =====
        ax_energia = fig.add_subplot(gs[2:4, 16:18])
        energias_list = simulador.historico_energias[:frame_num + 1]
        
        ax_energia.plot(frames_list, energias_list, 'r-', linewidth=1)
        ax_energia.axvline(frame_num, color='blue', linestyle='--', alpha=0.5, linewidth=0.8)
        ax_energia.set_xlabel('F', fontsize=7)
        ax_energia.set_ylabel('E', fontsize=7)
        ax_energia.set_title('Ene', fontsize=8, fontweight='bold')
        ax_energia.grid(True, alpha=0.2)
        ax_energia.tick_params(labelsize=6)
        
        # Guardar figura
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=75, bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close('all')
        
        return image_base64
    
    except Exception as e:
        print(f"❌ Error generar_frame {frame_num}: {e}\n{traceback.format_exc()}")
        return None


@app.route('/')
def index():
    """Página principal."""
    return render_template('index.html')

@app.route('/api/escenarios')
def listar_escenarios():
    """Lista escenarios disponibles."""
    ruta_scenarios = Path(__file__).parent.parent / "scenarios"
    escenarios = []
    
    for archivo in sorted(ruta_scenarios.glob("*.json")):
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            escenarios.append({
                'nombre_archivo': archivo.name,
                'nombre': datos.get('nombre', archivo.name),
                'descripcion': datos.get('descripcion', '')
            })
        except:
            pass
    
    return jsonify(escenarios)

@app.route('/api/cargar/<nombre_archivo>', methods=['POST'])
def cargar_simulacion(nombre_archivo):
    """Carga una simulación con número de pasos personalizado."""
    try:
        # Obtener número de pasos del request (por defecto 300)
        datos_request = request.get_json() or {}
        num_pasos = datos_request.get('num_pasos', 300)
        
        # Validar que sea un número válido
        num_pasos = max(1, min(int(num_pasos), 5000))  # Entre 1 y 5000
        
        simulador, datos = cargar_escenario(nombre_archivo, num_pasos)
        
        if simulador is None:
            return jsonify({'error': datos}), 400
        
        current_sim['simulador'] = simulador
        current_sim['frame'] = 0
        current_sim['paused'] = True
        current_sim['speed'] = 1.0
        
        # Construir información detallada de partículas
        particulas_info = []
        for i, p in enumerate(simulador.particulas):
            particulas_info.append({
                'id': p.id,
                'masa': round(p.masa, 2),
                'radio': round(p.radio, 2),
                'e': round(p.coef_restitution, 2),
                'color': p.color,
                'posicion_inicial': simulador.historico_posiciones[0][i].tolist(),
                'velocidad_inicial': simulador.historico_velocidades[0][i].tolist()
            })
        
        return jsonify({
            'nombre': datos.get('nombre'),
            'descripcion': datos.get('descripcion'),
            'total_frames': len(simulador.historico_posiciones),
            'num_particulas': len(simulador.particulas),
            'num_pasos': num_pasos,
            'dt': simulador.dt,
            'dominio': {
                'ancho': simulador.contenedor.ancho,
                'alto': simulador.contenedor.alto
            },
            'particulas': particulas_info
        })
    except Exception as e:
        print(f"Error en /api/cargar: {e}\n{traceback.format_exc()}")
        return jsonify({'error': f'Error al cargar: {str(e)}'}), 500

@app.route('/api/frame/<int:frame_num>')
def obtener_frame(frame_num):
    """Obtiene un frame específico."""
    try:
        if current_sim['simulador'] is None:
            return jsonify({'error': 'Sin simulación cargada'}), 400
        
        if frame_num >= len(current_sim['simulador'].historico_posiciones):
            frame_num = len(current_sim['simulador'].historico_posiciones) - 1
        
        image_base64 = generar_frame_base64(current_sim['simulador'], frame_num)
        
        if image_base64 is None:
            return jsonify({'error': 'No se pudo generar frame'}), 500
        
        return jsonify({
            'frame': frame_num,
            'total': len(current_sim['simulador'].historico_posiciones),
            'image': image_base64
        })
    except Exception as e:
        print(f"Error en /api/frame: {e}\n{traceback.format_exc()}")
        return jsonify({'error': f'Error al obtener frame: {str(e)}'}), 500


@app.route('/api/magnitudes/<int:frame_num>')
def obtener_magnitudes(frame_num):
    """Obtiene ecuaciones dinámicas con valores para un frame específico."""
    try:
        sim = current_sim['simulador']
        if sim is None:
            return jsonify({'error': 'Sin simulación cargada'}), 400
        
        if frame_num >= len(sim.historico_velocidades):
            return jsonify({'error': 'Frame inválido'}), 400
        
        vel_frame = sim.historico_velocidades[frame_num]
        presion = sim.presion_actual if hasattr(sim, 'presion_actual') else 0
        
        # Construir desglose de momento
        desglose_momento = []
        momento_total = 0
        for i, p in enumerate(sim.particulas):
            if i < len(vel_frame):
                vx = vel_frame[i][0] if len(vel_frame[i]) > 0 else 0
                vy = vel_frame[i][1] if len(vel_frame[i]) > 1 else 0
                v_mag = np.linalg.norm(vel_frame[i])
                px = p.masa * vx
                py = p.masa * vy
                p_mag = np.sqrt(px**2 + py**2)
                momento_total += p_mag
                desglose_momento.append({
                    'particula': i + 1,
                    'masa': round(p.masa, 2),
                    'vx': round(vx, 3),
                    'vy': round(vy, 3),
                    'v_mag': round(v_mag, 3),
                    'px': round(px, 4),
                    'py': round(py, 4),
                    'p_mag': round(p_mag, 4)
                })
        
        # Construir desglose de energía
        desglose_energia = []
        energia_total = 0
        for i, p in enumerate(sim.particulas):
            if i < len(vel_frame):
                v_mag = np.linalg.norm(vel_frame[i])
                ek = 0.5 * p.masa * (v_mag ** 2)
                energia_total += ek
                desglose_energia.append({
                    'particula': i + 1,
                    'masa': round(p.masa, 2),
                    'v_mag': round(v_mag, 3),
                    'ek': round(ek, 4)
                })
        
        return jsonify({
            'frame': frame_num,
            'momento': {
                'desglose': desglose_momento,
                'total': round(momento_total, 4)
            },
            'energia': {
                'desglose': desglose_energia,
                'total': round(energia_total, 4)
            },
            'presion': round(presion, 2)
        })
    except Exception as e:
        print(f"Error en /api/magnitudes: {e}\n{traceback.format_exc()}")
        return jsonify({'error': f'Error al obtener magnitudes: {str(e)}'}), 500


@app.route('/api/nueva_simulacion', methods=['POST'])
def nueva_simulacion():
    """Crea una simulación personalizada vacía."""
    try:
        datos = request.get_json() or {}
        ancho = float(datos.get('ancho', 10.0))
        alto = float(datos.get('alto', 10.0))
        
        # Crear contenedor y simulador vacío
        contenedor = Contenedor(ancho=ancho, alto=alto)
        simulador = Simulador(contenedor, dt=0.01, ancho_dominio=ancho, alto_dominio=alto)
        
        # Ejecutar 1 paso para inicializar históricos
        simulador.paso_simulacion()
        
        current_sim['simulador'] = simulador
        current_sim['frame'] = 0
        current_sim['paused'] = True
        current_sim['speed'] = 1.0
        
        return jsonify({
            'success': True,
            'nombre': 'Simulación Personalizada',
            'descripcion': 'Creada desde la interfaz',
            'total_frames': len(simulador.historico_posiciones),
            'num_particulas': 0,
            'dominio': {'ancho': ancho, 'alto': alto}
        })
    except Exception as e:
        print(f"❌ Error nueva_simulacion: {e}")
        return jsonify({'error': f'Error al crear simulación: {str(e)}'}), 500

@app.route('/api/ejecutar_simulacion', methods=['POST'])
def ejecutar_simulacion():
    """Ejecuta N pasos de simulación en una simulación personalizada."""
    try:
        sim = current_sim['simulador']
        if sim is None:
            return jsonify({'error': 'Crea una simulación primero'}), 400
        
        datos = request.get_json() or {}
        num_pasos = int(datos.get('num_pasos', 300))
        num_pasos = max(1, min(num_pasos, 5000))  # Entre 1 y 5000
        
        # Ejecutar pasos sin mostrar (solo calcular)
        for _ in range(num_pasos):
            sim.paso_simulacion()
        
        # Limpiar caché de frames
        from flask import current_app
        
        return jsonify({
            'success': True,
            'total_frames': len(sim.historico_posiciones),
            'num_particulas': len(sim.particulas),
            'pasos_ejecutados': num_pasos
        })
    except Exception as e:
        print(f"❌ Error ejecutar_simulacion: {e}")
        return jsonify({'error': f'Error al ejecutar: {str(e)}'}), 500

@app.route('/api/agregar_particula', methods=['POST'])
def agregar_particula():
    """Agrega una partícula a la simulación actual (requiere simulación cargada)."""
    try:
        sim = current_sim['simulador']
        if sim is None:
            return jsonify({'error': 'Crea o carga una simulación primero'}), 400
        
        datos = request.get_json()
        
        # Validar parámetros
        posicion = np.array(datos.get('posicion', [5, 5]), dtype=float)
        velocidad = np.array(datos.get('velocidad', [0, 0]), dtype=float)
        masa = float(datos.get('masa', 0.5))
        radio = float(datos.get('radio', 0.2))
        e = float(datos.get('e', 1.0))
        color = datos.get('color', 'blue')
        
        # Validar rangos
        if not (0.1 <= masa <= 100.0):
            return jsonify({'error': 'Masa debe estar entre 0.1 y 100.0 kg'}), 400
        if not (0.05 <= radio <= 2.0):
            return jsonify({'error': 'Radio debe estar entre 0.05 y 2.0 m'}), 400
        if not (0.0 <= e <= 1.0):
            return jsonify({'error': 'Coef. restitución debe estar entre 0 y 1'}), 400
        
        # Agregar partícula
        sim.agregar_particula(
            posicion=posicion,
            velocidad=velocidad,
            masa=masa,
            radio=radio,
            coef_restitution=e,
            color=color
        )
        
        # ✅ LIMPIAR CACHÉ DE FRAMES - la nueva partícula cambia todos los frames
        frame_cache.clear()
        
        return jsonify({
            'success': True,
            'num_particulas': len(sim.particulas),
            'particula': {
                'id': sim.particulas[-1].id,
                'posicion': posicion.tolist(),
                'velocidad': velocidad.tolist(),
                'masa': masa,
                'radio': radio,
                'e': e,
                'color': color
            }
        })
    except ValueError as ve:
        return jsonify({'error': f'Valor inválido: {str(ve)}'}), 400
    except Exception as e:
        print(f"❌ Error agregar_particula: {e}")
        return jsonify({'error': 'Error al agregar'}), 500


@app.route('/api/controles', methods=['POST'])
def controles():
    """Maneja controles de reproducción."""
    if current_sim['simulador'] is None:
        return jsonify({'error': 'Sin simulación cargada'}), 400
    
    action = request.json.get('action')
    
    if action == 'play':
        current_sim['paused'] = False
    elif action == 'pause':
        current_sim['paused'] = True
    elif action == 'next':
        current_sim['frame'] = min(
            current_sim['frame'] + 1,
            len(current_sim['simulador'].historico_posiciones) - 1
        )
    elif action == 'prev':
        current_sim['frame'] = max(current_sim['frame'] - 1, 0)
    elif action == 'set_frame':
        frame = request.json.get('frame', 0)
        current_sim['frame'] = min(
            max(frame, 0),
            len(current_sim['simulador'].historico_posiciones) - 1
        )
    elif action == 'speed':
        current_sim['speed'] = request.json.get('speed', 1.0)
    
    return jsonify({'status': 'ok', 'frame': current_sim['frame']})

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5002)
