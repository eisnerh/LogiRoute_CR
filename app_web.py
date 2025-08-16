from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import json
import pandas as pd
from datetime import datetime
from analisis_rutas import AnalizadorRutas
from organizador_archivos import OrganizadorArchivos
import threading
import time

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Variables globales para el estado del análisis
analizador = None
organizador = OrganizadorArchivos()
estado_analisis = {
    'en_proceso': False,
    'progreso': 0,
    'mensaje': '',
    'resultado': None,
    'error': None
}

def verificar_archivo_datos():
    """Verifica si existe el archivo de datos"""
    archivo_excel = "Data/REP PLR ESTATUS ENTREGAS v25.xlsx"
    return os.path.exists(archivo_excel)

def obtener_centros_disponibles():
    """Obtiene la lista de centros disponibles"""
    global analizador
    if analizador is None:
        return []
    
    try:
        columnas_clave = analizador.identificar_columnas_clave()
        if columnas_clave['centro']:
            return list(analizador.df[columnas_clave['centro']].unique())
        return []
    except:
        return []

@app.route('/')
def index():
    """Página principal"""
    archivo_existe = verificar_archivo_datos()
    return render_template('index.html', archivo_existe=archivo_existe)

@app.route('/cargar_datos', methods=['POST'])
def cargar_datos():
    """Carga los datos del archivo Excel"""
    global analizador, estado_analisis
    
    try:
        estado_analisis['en_proceso'] = True
        estado_analisis['progreso'] = 10
        estado_analisis['mensaje'] = 'Inicializando analizador...'
        
        archivo_excel = "Data/REP PLR ESTATUS ENTREGAS v25.xlsx"
        analizador = AnalizadorRutas(archivo_excel)
        
        estado_analisis['progreso'] = 30
        estado_analisis['mensaje'] = 'Cargando datos del archivo Excel...'
        
        if not analizador.cargar_datos():
            estado_analisis['error'] = 'Error al cargar los datos del archivo Excel'
            estado_analisis['en_proceso'] = False
            return jsonify({'success': False, 'error': estado_analisis['error']})
        
        estado_analisis['progreso'] = 50
        estado_analisis['mensaje'] = 'Explorando datos...'
        
        analizador.explorar_datos()
        
        estado_analisis['progreso'] = 70
        estado_analisis['mensaje'] = 'Identificando columnas...'
        
        columnas_clave = analizador.identificar_columnas_clave()
        
        estado_analisis['progreso'] = 100
        estado_analisis['mensaje'] = 'Datos cargados exitosamente'
        estado_analisis['en_proceso'] = False
        
        centros = obtener_centros_disponibles()
        
        return jsonify({
            'success': True,
            'mensaje': 'Datos cargados exitosamente',
            'centros': centros,
            'total_filas': len(analizador.df),
            'columnas_clave': columnas_clave
        })
        
    except Exception as e:
        estado_analisis['error'] = f'Error: {str(e)}'
        estado_analisis['en_proceso'] = False
        return jsonify({'success': False, 'error': estado_analisis['error']})

@app.route('/ejecutar_analisis', methods=['POST'])
def ejecutar_analisis():
    """Ejecuta el análisis de rutas"""
    global analizador, organizador, estado_analisis
    
    try:
        data = request.get_json()
        centro = data.get('centro')
        tipo_analisis = data.get('tipo_analisis', 'normal')
        max_clientes = int(data.get('max_clientes', 15))
        max_cajas = int(data.get('max_cajas', 694))
        rutas_disponibles = data.get('rutas_disponibles')
        if rutas_disponibles:
            rutas_disponibles = int(rutas_disponibles)
        dia_semana = data.get('dia_semana', '')
        generar_proyeccion = data.get('generar_proyeccion', False)
        waze_integration = data.get('waze_integration', False)
        
        # Crear carpeta para el reporte
        carpeta_reporte = organizador.crear_carpeta_reporte(centro, tipo_analisis)
        
        # Ejecutar análisis en un hilo separado
        thread = threading.Thread(target=ejecutar_analisis_thread, args=(
            centro, tipo_analisis, max_clientes, rutas_disponibles, max_cajas, dia_semana, generar_proyeccion, waze_integration
        ))
        thread.start()
        
        return jsonify({
            'success': True,
            'mensaje': 'Análisis iniciado',
            'carpeta_reporte': carpeta_reporte
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def ejecutar_analisis_thread(centro, tipo_analisis, max_clientes, rutas_disponibles, max_cajas, dia_semana, generar_proyeccion, waze_integration):
    """Ejecuta el análisis en un hilo separado"""
    global analizador, organizador, estado_analisis
    
    try:
        estado_analisis['en_proceso'] = True
        estado_analisis['progreso'] = 0
        estado_analisis['mensaje'] = 'Iniciando análisis...'
        
        # Filtrar por centro
        if centro and centro != "TODOS":
            estado_analisis['progreso'] = 20
            estado_analisis['mensaje'] = f'Filtrando datos del centro {centro}...'
            
            resultado = analizador.filtrar_por_centro(centro)
            if resultado is None:
                estado_analisis['error'] = f'Error al filtrar el centro {centro}'
                return
            
            df_filtrado, columnas_clave = resultado
        else:
            estado_analisis['progreso'] = 20
            estado_analisis['mensaje'] = 'Analizando todos los centros...'
            
            df_filtrado = analizador.df
            columnas_clave = analizador.identificar_columnas_clave()
        
        # Filtrar por día de la semana si se especifica
        if dia_semana:
            estado_analisis['progreso'] = 30
            estado_analisis['mensaje'] = f'Filtrando por día: {dia_semana}...'
            
            # Buscar columna de fecha de entrega
            if 'Fe.Entrega' in df_filtrado.columns:
                # Extraer el día de la semana de la fecha de entrega
                df_filtrado['dia_semana'] = df_filtrado['Fe.Entrega'].dt.day_name()
                
                # Mapear nombres de días en español
                mapeo_dias = {
                    'Monday': 'Lunes',
                    'Tuesday': 'Martes', 
                    'Wednesday': 'Miércoles',
                    'Thursday': 'Jueves',
                    'Friday': 'Viernes',
                    'Saturday': 'Sábado',
                    'Sunday': 'Domingo'
                }
                
                # Aplicar el mapeo
                df_filtrado['dia_semana'] = df_filtrado['dia_semana'].map(mapeo_dias)
                
                # Filtrar por el día especificado
                df_filtrado = df_filtrado[df_filtrado['dia_semana'] == dia_semana].copy()
                
                if len(df_filtrado) == 0:
                    estado_analisis['error'] = f'No se encontraron datos para el día {dia_semana}'
                    return
                else:
                    print(f"✅ Filtrado por día {dia_semana}: {len(df_filtrado)} registros encontrados")
            else:
                estado_analisis['error'] = 'No se encontró la columna Fe.Entrega para filtrar por día de la semana'
                return
        
        # Generar rutas
        estado_analisis['progreso'] = 40
        estado_analisis['mensaje'] = 'Generando rutas optimizadas...'
        
        resultado_rutas = analizador.generar_sugerido_rutas(
            df_filtrado, columnas_clave, max_clientes, rutas_disponibles, generar_proyeccion, max_cajas
        )
        
        if resultado_rutas is None:
            estado_analisis['error'] = 'No se pudieron generar rutas'
            return
        
        resultado, df_ordenado, centro_coords = resultado_rutas
        
        # Generar archivos
        estado_analisis['progreso'] = 60
        estado_analisis['mensaje'] = 'Generando archivos de salida...'
        
        if generar_proyeccion:
            # Proyección semanal
            proyeccion_semanal = resultado
            
            # Mover archivos de proyección
            archivos_proyeccion = [f for f in os.listdir('.') if f.startswith('proyeccion_semanal')]
            for archivo in archivos_proyeccion:
                organizador.mover_archivo(archivo, "excel")
            
            # Mover mapas de proyección
            archivos_mapas = [f for f in os.listdir('.') if f.startswith('mapa_proyeccion')]
            for archivo in archivos_mapas:
                organizador.mover_archivo(archivo, "mapa")
                
        else:
            # Análisis normal
            rutas = resultado
            
            # Generar mapa con integración Waze si se solicita
            nombre_mapa = organizador.obtener_ruta_archivo("mapa_rutas.html", "mapa")
            if waze_integration:
                analizador.generar_mapa_con_waze(rutas, centro_coords, nombre_mapa)
            else:
                analizador.generar_mapa(rutas, centro_coords, nombre_mapa)
            
            # Generar reporte Excel
            nombre_excel = organizador.obtener_ruta_archivo("reporte_rutas.xlsx", "excel")
            analizador.generar_reporte_excel(rutas, df_ordenado, columnas_clave, nombre_excel)
        
        # Limpiar archivos temporales
        estado_analisis['progreso'] = 80
        estado_analisis['mensaje'] = 'Organizando archivos...'
        
        organizador.limpiar_archivos_temporales()
        
        # Generar resumen
        estado_analisis['progreso'] = 90
        estado_analisis['mensaje'] = 'Generando resumen...'
        
        organizador.generar_reporte_resumen()
        
        # Completar
        estado_analisis['progreso'] = 100
        estado_analisis['mensaje'] = 'Análisis completado exitosamente'
        estado_analisis['resultado'] = {
            'carpeta_reporte': organizador.carpeta_actual,
            'archivos_generados': organizador.archivos_generados
        }
        
    except Exception as e:
        estado_analisis['error'] = f'Error durante el análisis: {str(e)}'
    finally:
        estado_analisis['en_proceso'] = False

@app.route('/estado_analisis')
def obtener_estado():
    """Obtiene el estado actual del análisis"""
    return jsonify(estado_analisis)

@app.route('/centros')
def obtener_centros():
    """Obtiene la lista de centros disponibles"""
    centros = obtener_centros_disponibles()
    return jsonify({'centros': centros})

@app.route('/descargar_archivo/<path:ruta_archivo>')
def descargar_archivo(ruta_archivo):
    """Descarga un archivo específico"""
    try:
        return send_file(ruta_archivo, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/abrir_carpeta/<path:carpeta>')
def abrir_carpeta(carpeta):
    """Abre la carpeta del reporte en el explorador de archivos"""
    try:
        os.startfile(carpeta)  # Windows
        return jsonify({'success': True})
    except:
        try:
            os.system(f'open "{carpeta}"')  # macOS
            return jsonify({'success': True})
        except:
            try:
                os.system(f'xdg-open "{carpeta}"')  # Linux
                return jsonify({'success': True})
            except:
                return jsonify({'error': 'No se pudo abrir la carpeta'})

@app.route('/datos_web')
def datos_web():
    """Muestra los datos de las últimas rutas generadas en formato web con filtros."""
    global analizador
    
    # Información de debug
    debug_info = {
        'analizador_existe': analizador is not None,
        'ultimas_rutas_generadas': hasattr(analizador, 'ultimas_rutas_generadas') if analizador else False,
        'ultima_proyeccion_generada': hasattr(analizador, 'ultima_proyeccion_generada') if analizador else False,
        'rutas_valor': analizador.ultimas_rutas_generadas if analizador and hasattr(analizador, 'ultimas_rutas_generadas') else None,
        'proyeccion_valor': analizador.ultima_proyeccion_generada if analizador and hasattr(analizador, 'ultima_proyeccion_generada') else None
    }
    
    # Logging adicional para debug
    print(f"🔍 DEBUG /datos_web:")
    print(f"   analizador existe: {analizador is not None}")
    if analizador:
        print(f"   tiene ultimas_rutas_generadas: {hasattr(analizador, 'ultimas_rutas_generadas')}")
        print(f"   tiene ultima_proyeccion_generada: {hasattr(analizador, 'ultima_proyeccion_generada')}")
        if hasattr(analizador, 'ultimas_rutas_generadas'):
            print(f"   ultimas_rutas_generadas: {len(analizador.ultimas_rutas_generadas) if analizador.ultimas_rutas_generadas else 0}")
            if analizador.ultimas_rutas_generadas:
                print(f"   Primera ruta: {analizador.ultimas_rutas_generadas[0] if len(analizador.ultimas_rutas_generadas) > 0 else 'No hay rutas'}")
        if hasattr(analizador, 'ultima_proyeccion_generada'):
            print(f"   ultima_proyeccion_generada: {len(analizador.ultima_proyeccion_generada) if analizador.ultima_proyeccion_generada else 0}")
    
    if analizador is None or (analizador.ultimas_rutas_generadas is None and analizador.ultima_proyeccion_generada is None):
        # Mostrar datos sin procesar como alternativa
        datos_raw = []
        if analizador and hasattr(analizador, 'df') and len(analizador.df) > 0:
            # Tomar las primeras 100 filas como muestra
            muestra = analizador.df.head(100)
            for idx, row in muestra.iterrows():
                datos_raw.append({
                    'Centro': str(row.get('Centro', 'N/A')),
                    'Cliente': str(row.get('Cliente', 'N/A')),
                    'Nombre de': str(row.get('Nombre del Cliente', 'N/A')),
                    'Cajas Equiv.': str(row.get('Cajas Equiv.', 'N/A')),
                    'Latitud': str(row.get('Latitud', 'N/A')),
                    'Longitud': str(row.get('Longitud', 'N/A')),
                    'Provincia': str(row.get('Provincia', 'N/A')),
                    'Cantón': str(row.get('Cantón', 'N/A')),
                    'Distrito': str(row.get('Distrito', 'N/A'))
                })
        
        return f"""
        <h2>Error: No hay datos de rutas generados</h2>
        <h3>Información de Debug:</h3>
        <pre>{debug_info}</pre>
        <h3>Datos Sin Procesar (Primeras 100 filas):</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr>
                <th>Centro</th><th>Cliente</th><th>Nombre</th><th>Cajas</th><th>Lat</th><th>Lon</th><th>Provincia</th><th>Cantón</th><th>Distrito</th>
            </tr>
            {''.join([f'<tr><td>{d["Centro"]}</td><td>{d["Cliente"]}</td><td>{d["Nombre de"]}</td><td>{d["Cajas Equiv."]}</td><td>{d["Latitud"]}</td><td>{d["Longitud"]}</td><td>{d["Provincia"]}</td><td>{d["Cantón"]}</td><td>{d["Distrito"]}</td></tr>' for d in datos_raw])}
        </table>
        <p>Por favor, ejecute un análisis primero.</p>
        """, 404

    datos_para_web = []
    print(f"🔍 Procesando datos para web...")
    if analizador.ultimas_rutas_generadas:
        print(f"   Procesando {len(analizador.ultimas_rutas_generadas)} rutas normales")
        for ruta_info in analizador.ultimas_rutas_generadas:
            for cliente in ruta_info['clientes']:
                # Obtener datos del DataFrame y convertir tipos numpy a Python nativos
                cliente_row = analizador.df[analizador.df[analizador.columnas_clave['cliente']] == cliente['cliente']]
                provincia = 'N/A'
                canton = 'N/A'
                distrito = 'N/A'
                
                if len(cliente_row) > 0:
                    if 'Provincia' in analizador.df.columns:
                        provincia_val = cliente_row['Provincia'].iloc[0]
                        provincia = str(provincia_val) if not pd.isna(provincia_val) else 'N/A'
                    if 'Cantón' in analizador.df.columns:
                        canton_val = cliente_row['Cantón'].iloc[0]
                        canton = str(canton_val) if not pd.isna(canton_val) else 'N/A'
                    if 'Distrito' in analizador.df.columns:
                        distrito_val = cliente_row['Distrito'].iloc[0]
                        distrito = str(distrito_val) if not pd.isna(distrito_val) else 'N/A'
                    
                    # Obtener el día de la semana de la fecha de entrega
                    dia_semana = 'N/A'
                    if len(cliente_row) > 0 and 'Fe.Entrega' in cliente_row.columns:
                        try:
                            fecha_entrega = cliente_row['Fe.Entrega'].iloc[0]
                            if pd.notna(fecha_entrega):
                                # Extraer día de la semana
                                dia_ingles = fecha_entrega.strftime('%A')
                                mapeo_dias = {
                                    'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                                    'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                                }
                                dia_semana = mapeo_dias.get(dia_ingles, 'N/A')
                        except:
                            dia_semana = 'N/A'
                    
                    datos_para_web.append({
                        'Centro': str(cliente_row[analizador.columnas_clave['centro']].iloc[0]) if len(cliente_row) > 0 else 'N/A',
                        'dia': dia_semana,
                        'Cliente': str(cliente['cliente']),
                        'Nombre de': str(cliente['nombre_cliente']),
                        'Ruta': str(ruta_info['ruta']),
                        'Viaje': 'N/A', # No disponible en la estructura actual
                        'Latitud': float(cliente['lat']),
                        'Longitud': float(cliente['lon']),
                        'Provincia': provincia,
                        'Cantón': canton,
                        'Distrito': distrito,
                        'Promedio de Cajas Equiv.': float(cliente['cajas'])
                    })
    elif analizador.ultima_proyeccion_generada:
        print(f"   Procesando proyección semanal")
        for dia, rutas_dia in analizador.ultima_proyeccion_generada.items():
            for ruta_info in rutas_dia:
                for cliente in ruta_info['clientes']:
                    # Obtener datos del DataFrame y convertir tipos numpy a Python nativos
                    cliente_row = analizador.df[analizador.df[analizador.columnas_clave['cliente']] == cliente['cliente']]
                    provincia = 'N/A'
                    canton = 'N/A'
                    distrito = 'N/A'
                    
                    if len(cliente_row) > 0:
                        if 'Provincia' in analizador.df.columns:
                            provincia_val = cliente_row['Provincia'].iloc[0]
                            provincia = str(provincia_val) if not pd.isna(provincia_val) else 'N/A'
                        if 'Cantón' in analizador.df.columns:
                            canton_val = cliente_row['Cantón'].iloc[0]
                            canton = str(canton_val) if not pd.isna(canton_val) else 'N/A'
                        if 'Distrito' in analizador.df.columns:
                            distrito_val = cliente_row['Distrito'].iloc[0]
                            distrito = str(distrito_val) if not pd.isna(distrito_val) else 'N/A'
                    
                    datos_para_web.append({
                        'Centro': str(cliente_row[analizador.columnas_clave['centro']].iloc[0]) if len(cliente_row) > 0 else 'N/A',
                        'dia': dia,
                        'Cliente': str(cliente['cliente']),
                        'Nombre de': str(cliente['nombre_cliente']),
                        'Ruta': str(ruta_info['ruta']),
                        'Viaje': 'N/A',
                        'Latitud': float(cliente['lat']),
                        'Longitud': float(cliente['lon']),
                        'Provincia': provincia,
                        'Cantón': canton,
                        'Distrito': distrito,
                        'Promedio de Cajas Equiv.': float(cliente['cajas'])
                    })

    print(f"   Total de datos procesados: {len(datos_para_web)}")
    
    # Obtener valores únicos para los filtros
    centros = sorted(list(set(d['Centro'] for d in datos_para_web if d['Centro'] != 'N/A')))
    dias = sorted(list(set(d['dia'] for d in datos_para_web if d['dia'] != 'N/A')))
    rutas_unicas = sorted(list(set(d['Ruta'] for d in datos_para_web if d['Ruta'] != 'N/A')))
    provincias = sorted(list(set(d['Provincia'] for d in datos_para_web if d['Provincia'] != 'N/A')))
    cantones = sorted(list(set(d['Cantón'] for d in datos_para_web if d['Cantón'] != 'N/A')))
    distritos = sorted(list(set(d['Distrito'] for d in datos_para_web if d['Distrito'] != 'N/A')))

    return render_template('datos_web.html',
                           datos=datos_para_web,
                           centros=centros,
                           dias=dias,
                           rutas=rutas_unicas,
                           provincias=provincias,
                           cantones=cantones,
                           distritos=distritos)

@app.route('/api/datos_filtrados')
def datos_filtrados():
    """API para obtener datos filtrados"""
    global analizador
    if analizador is None:
        return jsonify({'error': 'No hay datos cargados'})
    
    # Obtener parámetros de filtro
    centro = request.args.get('centro', '')
    dia = request.args.get('dia', '')
    ruta = request.args.get('ruta', '')
    provincia = request.args.get('provincia', '')
    canton = request.args.get('canton', '')
    distrito = request.args.get('distrito', '')
    
    # Crear datos filtrados
    datos_filtrados = []
    if hasattr(analizador, 'ultimas_rutas') and analizador.ultimas_rutas:
        columnas_clave = analizador.identificar_columnas_clave()
        
        for ruta_data in analizador.ultimas_rutas:
            for cliente in ruta_data['clientes']:
                cliente_id = cliente['cliente']
                cliente_row = analizador.df[analizador.df[columnas_clave['cliente']] == cliente_id].iloc[0] if len(analizador.df[analizador.df[columnas_clave['cliente']] == cliente_id]) > 0 else None
                
                if cliente_row is not None:
                    # Aplicar filtros
                    if centro and cliente_row[columnas_clave['centro']] != centro:
                        continue
                    if dia and cliente_row.get('dia entrega', '') != dia:
                        continue
                    if ruta and ruta_data['ruta'] != int(ruta) if ruta.isdigit() else True:
                        continue
                    if provincia and cliente_row.get('Provincia', '') != provincia:
                        continue
                    if canton and cliente_row.get('Cantón', '') != canton:
                        continue
                    if distrito and cliente_row.get('Distrito', '') != distrito:
                        continue
                    
                    datos_filtrados.append({
                        'Centro': cliente_row[columnas_clave['centro']],
                        'dia': cliente_row.get('dia entrega', 'N/A'),
                        'Cliente': cliente_id,
                        'Nombre de': cliente.get('nombre_cliente', cliente_id),
                        'Ruta': ruta_data['ruta'],
                        'Viaje': cliente_row.get('Viaje', 'N/A'),
                        'Latitud': cliente['lat'],
                        'Longitud': cliente['lon'],
                        'Provincia': cliente_row.get('Provincia', 'N/A'),
                        'Cantón': cliente_row.get('Cantón', 'N/A'),
                        'Distrito': cliente_row.get('Distrito', 'N/A'),
                        'Promedio de Cajas Equiv.': cliente['cajas']
                    })
    
    return jsonify({'datos': datos_filtrados})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
