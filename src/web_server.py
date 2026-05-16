"""Servidor web Flask para interfaz gráfica de la simulación."""

import json
import numpy as np
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from src.modelo.contenedor import Contenedor
from src.controlador.simulador import Simulador
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI - DEBE IR ANTES de importar pyplot
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
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

def cargar_escenario(nombre_archivo):
    """Carga un escenario JSON y retorna simulador."""
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
        pasos = datos.get("pasos", 300)
        simulador.ejecutar(pasos, mostrar=False)
        
        return simulador, datos
    
    except Exception as e:
        return None, f"Error al cargar escenario: {str(e)}\n{traceback.format_exc()}"

def generar_frame_base64(simulador, frame_num):
    """Genera imagen Base64 del frame actual."""
    try:
        if not simulador or frame_num >= len(simulador.historico_posiciones):
            return None
        
        plt.ioff()  # Desactivar modo interactivo
        
        # Crear figura con backend sin GUI
        fig = plt.figure(figsize=(8, 6), dpi=100)
        fig.patch.set_facecolor('white')
        
        ax = fig.add_subplot(111)
        
        # Dibujar partículas
        historico = simulador.historico_posiciones[frame_num]
        for i, p in enumerate(simulador.particulas):
            circle = Circle(
                historico[i],
                p.radio,
                facecolor=p.color,
                alpha=0.7,
                edgecolor='black',
                linewidth=2
            )
            ax.add_patch(circle)
            ax.text(
                historico[i][0],
                historico[i][1],
                str(p.id),
                ha='center',
                va='center',
                fontsize=10,
                color='white',
                fontweight='bold'
            )
        
        ax.set_xlim(0, simulador.contenedor.ancho)
        ax.set_ylim(0, simulador.contenedor.alto)
        ax.set_aspect('equal')
        ax.set_xlabel('x (m)')
        ax.set_ylabel('y (m)')
        ax.set_title(f'Simulación 2D - Paso {frame_num + 1}/{len(simulador.historico_posiciones)}')
        ax.grid(True, alpha=0.3)
        
        fig.tight_layout()
        
        # Convertir a Base64
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0.2)
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        # Limpiar memoria
        buf.close()
        plt.close('all')  # Cerrar todas las figuras
        
        return image_base64
    
    except Exception as e:
        print(f"❌ Error al generar frame {frame_num}: {e}")
        print(traceback.format_exc())
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
    """Carga una simulación."""
    try:
        simulador, datos = cargar_escenario(nombre_archivo)
        
        if simulador is None:
            return jsonify({'error': datos}), 400
        
        current_sim['simulador'] = simulador
        current_sim['frame'] = 0
        current_sim['paused'] = True
        current_sim['speed'] = 1.0
        
        return jsonify({
            'nombre': datos.get('nombre'),
            'descripcion': datos.get('descripcion'),
            'total_frames': len(simulador.historico_posiciones),
            'num_particulas': len(simulador.particulas)
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
    app.run(debug=True, host='127.0.0.1', port=5000)
