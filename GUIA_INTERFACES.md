# Guía - Dual Interface (Terminal + Navegador)

## ¿Qué cambió?

Se agregó una **segunda interfaz** (navegador) mientras se mantiene la interfaz por terminal. Ahora el programa ofrece dos opciones según tus recursos disponibles.

---

## 📱 OPCIÓN 1 & 2: INTERFAZ TERMINAL (RECOMENDADA PARA PC BAJO RECURSOS)

### Ventajas:
✓ **Muy fluida** - Sin latencia de requests HTTP  
✓ **Bajo consumo de recursos** - Ideal para PC viejas o limitadas  
✓ **Responsive** - Actualizaciones instantáneas  
✓ **Sin dependencias gráficas** - Solo texto en terminal  

### Cómo usar:
```bash
python main.py
```

Luego selecciona:
- **Opción 1**: Crear simulación personalizada ingresando datos
- **Opción 2**: Cargar escenario predefinido desde JSON

---

## 🌐 OPCIÓN 3: INTERFAZ DEL NAVEGADOR (RECOMENDADA PARA PC CON BUENOS RECURSOS)

### Ventajas:
✓ **Interfaz moderna y visual**  
✓ **Gráficos en tiempo real**  
✓ **Panel de control profesional**  
✓ **Reproducción con controles multimedia**  
✓ **Mejor presentación para demostraciones**  

### Cómo usar:
```bash
python main.py
```

Luego selecciona:
- **Opción 3**: Interfaz del navegador

Se abrirá automáticamente en: `http://127.0.0.1:5002`

### Controles en el navegador:
- ⏵ **Reproducir** - Inicia la animación
- ⏸ **Pausar** - Pausa la animación
- 🎚️ **Velocidad** - Ajusta velocidad de reproducción
- 📊 **Panel derecho** - Carga escenarios predefinidos
- 📋 **Información** - Datos de partículas en tiempo real

---

## 🚪 OPCIÓN 4: SALIR

Cierra el programa correctamente.

---

## ¿Cuál elegir?

| Situación | Interfaz |
|-----------|----------|
| PC antigua/lenta | Terminal (Opción 1-2) |
| PC moderna/rápida | Navegador (Opción 3) |
| Demostraciones profesionales | Navegador (Opción 3) |
| Cálculos rápidos | Terminal (Opción 1-2) |
| Bajo ancho de banda | Terminal (Opción 1-2) |

---

## Flujo Completo

```
┌─ python main.py
│
├─ Menú Principal
│  ├─ 1: Simulación terminal personalizada → Fluida, sin requests
│  ├─ 2: Escenarios JSON → Fluida, sin requests
│  ├─ 3: Interfaz navegador → Abre http://127.0.0.1:5002
│  └─ 4: Salir → Cierra programa
```

---

## Resolución de Problemas

### Opción 3 no abre el navegador
```bash
# Abre manualmente en tu navegador:
http://127.0.0.1:5002
```

### Puerto 5002 ya está en uso
```bash
# Modifica el puerto en src/web_server.py
app.run(port=5003)  # Cambia a otro puerto
```

### Terminal se comporta raro
```bash
# Usa terminal nativa (no IDE integrado)
cd TIF-Fisica
python main.py
```

---

## Notas Técnicas

- **Terminal**: Uso directo de clases Python, sin latencia HTTP
- **Navegador**: Servidor Flask + HTML/CSS/JavaScript
- **Puerto**: 127.0.0.1:5002 (solo accesible localmente)
- **Sin dependencias externas de UI**: Funciona en cualquier SO

---

**Creado**: Mayo 2026  
**Para**: TIF Física - Ingenería en Informática
