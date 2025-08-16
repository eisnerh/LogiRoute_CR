import pandas as pd
import numpy as np
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
import folium
from folium import plugins
import warnings
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

class AnalizadorRutas:
    def __init__(self, archivo_excel, hoja_nombre="REP PLR"):
        """
        Inicializa el analizador de rutas
        
        Args:
            archivo_excel (str): Ruta al archivo Excel
            hoja_nombre (str): Nombre de la hoja a analizar
        """
        self.archivo_excel = archivo_excel
        self.hoja_nombre = hoja_nombre
        self.df = None
        self.centros_disponibles = []
        
    def cargar_datos(self):
        """Carga los datos del archivo Excel"""
        try:
            print("Cargando datos del archivo Excel...")
            self.df = pd.read_excel(self.archivo_excel, sheet_name=self.hoja_nombre)
            print(f"Datos cargados exitosamente. Filas: {len(self.df)}")
            print(f"Columnas disponibles: {list(self.df.columns)}")
            
            # Ordenar datos por Centro en orden ascendente
            columnas_clave = self.identificar_columnas_clave()
            if columnas_clave['centro']:
                print(f"Ordenando datos por '{columnas_clave['centro']}' en orden ascendente...")
                self.df = self.df.sort_values(columnas_clave['centro'], ascending=True)
                print("Datos ordenados exitosamente")
            
            return True
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")
            return False
    
    def explorar_datos(self):
        """Explora la estructura de los datos"""
        if self.df is None:
            print("Primero debe cargar los datos")
            return
            
        print("\n=== EXPLORACIÓN DE DATOS ===")
        print(f"Forma del dataset: {self.df.shape}")
        print(f"\nPrimeras 5 filas:")
        print(self.df.head())
        
        print(f"\nInformación de columnas:")
        print(self.df.info())
        
        print(f"\nEstadísticas descriptivas:")
        print(self.df.describe())
        
        # Buscar columnas relacionadas con centros
        columnas_centro = [col for col in self.df.columns if 'centro' in col.lower() or 'sucursal' in col.lower()]
        if columnas_centro:
            print(f"\nColumnas relacionadas con centros: {columnas_centro}")
            for col in columnas_centro:
                print(f"Valores únicos en {col}: {self.df[col].unique()}")
    
    def identificar_columnas_clave(self):
        """Identifica las columnas clave para el análisis"""
        columnas_clave = {
            'centro': None,
            'cliente': None,
            'nombre_cliente': None,
            'cajas_equiv': None,
            'latitud': None,
            'longitud': None,
            'ruta_dist': None
        }
        
        # Buscar columnas por patrones
        for col in self.df.columns:
            col_lower = col.lower()
            
            if 'centro' in col_lower or 'sucursal' in col_lower:
                columnas_clave['centro'] = col
            elif 'cliente' in col_lower and 'nombre' in col_lower:
                columnas_clave['nombre_cliente'] = col
            elif col_lower == 'cliente':
                columnas_clave['cliente'] = col
            elif 'caja' in col_lower and 'equiv' in col_lower:
                columnas_clave['cajas_equiv'] = col
            elif 'lat' in col_lower or 'latitud' in col_lower:
                columnas_clave['latitud'] = col
            elif 'lon' in col_lower or 'longitud' in col_lower:
                columnas_clave['longitud'] = col
            elif 'ruta' in col_lower and 'dist' in col_lower:
                columnas_clave['ruta_dist'] = col
        
        # Si no se encontró cliente, buscar alternativas
        if columnas_clave['cliente'] is None:
            for col in self.df.columns:
                col_lower = col.lower()
                if 'cliente' in col_lower and 'nombre' not in col_lower and '48' not in col_lower:
                    # Verificar que la columna tenga datos válidos
                    if self.df[col].notna().sum() > 0:
                        columnas_clave['cliente'] = col
                        break
        
        # Si no se encontró nombre_cliente, usar cliente como respaldo
        if columnas_clave['nombre_cliente'] is None:
            columnas_clave['nombre_cliente'] = columnas_clave['cliente']
        
        print("\n=== COLUMNAS IDENTIFICADAS ===")
        for clave, valor in columnas_clave.items():
            print(f"{clave}: {valor}")
            
        return columnas_clave
    
    def filtrar_por_centro(self, centro_seleccionado):
        """Filtra los datos por un centro específico y depura clientes frecuentes"""
        columnas_clave = self.identificar_columnas_clave()
        
        if columnas_clave['centro'] is None:
            print("No se encontró columna de centro")
            return None
            
        # Mostrar centros disponibles
        centros_disponibles = self.df[columnas_clave['centro']].unique()
        print(f"\nCentros disponibles: {centros_disponibles}")
        
        # Filtrar por centro seleccionado
        df_filtrado = self.df[self.df[columnas_clave['centro']] == centro_seleccionado].copy()
        print(f"Clientes en el centro {centro_seleccionado}: {len(df_filtrado)}")
        
        # Depurar clientes frecuentes (más de 2 veces en 8 semanas)
        df_depurado = self._depurar_clientes_frecuentes(df_filtrado, columnas_clave)
        
        return df_depurado, columnas_clave
    
    def _depurar_clientes_frecuentes(self, df, columnas_clave):
        """Depura clientes que se han procesado menos de 3 veces en las últimas 8 semanas"""
        print(f"\n=== DEPURACIÓN DE CLIENTES FRECUENTES ===")
        
        # Contar frecuencia de cada cliente
        frecuencia_clientes = df[columnas_clave['cliente']].value_counts()
        
        print(f"Total de clientes únicos: {len(frecuencia_clientes)}")
        print(f"Distribución de frecuencia:")
        print(f"  • 1 vez: {len(frecuencia_clientes[frecuencia_clientes == 1])} clientes ❌ (eliminados)")
        print(f"  • 2 veces: {len(frecuencia_clientes[frecuencia_clientes == 2])} clientes ❌ (eliminados)")
        print(f"  • 3+ veces: {len(frecuencia_clientes[frecuencia_clientes >= 3])} clientes ✅ (mantenidos)")
        
        # Mostrar algunos ejemplos de clientes frecuentes
        clientes_frecuentes = frecuencia_clientes[frecuencia_clientes >= 3].head(5)
        if len(clientes_frecuentes) > 0:
            print(f"\nEjemplos de clientes frecuentes (3+ veces):")
            for cliente, freq in clientes_frecuentes.items():
                print(f"  • {cliente}: {freq} veces")
        
        # Filtrar clientes que aparecen 3 veces o más (mantener los frecuentes)
        clientes_validos = frecuencia_clientes[frecuencia_clientes >= 3].index
        df_depurado = df[df[columnas_clave['cliente']].isin(clientes_validos)].copy()
        
        print(f"\nClientes después de depuración: {len(df_depurado)}")
        print(f"Clientes eliminados (1-2 veces): {len(df) - len(df_depurado)}")
        
        # Calcular estadísticas de cajas antes y después
        if columnas_clave['cajas_equiv']:
            cajas_antes = df[columnas_clave['cajas_equiv']].sum()
            cajas_despues = df_depurado[columnas_clave['cajas_equiv']].sum()
            print(f"Total cajas antes de depuración: {cajas_antes:,.0f}")
            print(f"Total cajas después de depuración: {cajas_despues:,.0f}")
            print(f"Cajas eliminadas: {cajas_antes - cajas_despues:,.0f}")
        
        return df_depurado
    
    def limpiar_coordenadas(self, df, columnas_clave):
        """Limpia y separa coordenadas que están concatenadas"""
        df_limpio = df.copy()
        
        # Función para extraer la primera coordenada de una cadena concatenada
        def extraer_primera_coordenada(valor):
            if pd.isna(valor) or valor == '':
                return None
            valor_str = str(valor)
            
            # Si el valor es muy largo, puede contener múltiples coordenadas concatenadas
            if len(valor_str) > 100:
                print(f"Valor de coordenada muy largo detectado ({len(valor_str)} caracteres): {valor_str[:100]}...")
                # Buscar el primer patrón de coordenada válida (número con punto decimal)
                import re
                matches = re.findall(r'-?\d+\.\d+', valor_str)
                if matches:
                    # Tomar la primera coordenada encontrada
                    primera_coord = float(matches[0])
                    print(f"  Primera coordenada extraída: {primera_coord}")
                    return primera_coord
                else:
                    print(f"  No se encontraron coordenadas válidas en el valor largo")
                    return None
            
            # Para valores normales, buscar el primer número decimal (incluyendo negativos)
            import re
            match = re.search(r'-?\d+\.\d+', valor_str)
            if match:
                coord = float(match.group())
                # Verificar que la coordenada está en el rango de Costa Rica
                if -90 <= coord <= 90:  # Rango válido para latitud/longitud
                    return coord
                else:
                    print(f"  Coordenada fuera de rango válido: {coord}")
                    return None
            return None
        
        # Limpiar latitud
        if columnas_clave['latitud']:
            print(f"Limpiando coordenadas de latitud de la columna: {columnas_clave['latitud']}")
            df_limpio['latitud_limpia'] = df_limpio[columnas_clave['latitud']].apply(extraer_primera_coordenada)
            lat_validas = df_limpio['latitud_limpia'].notna().sum()
            print(f"Coordenadas de latitud válidas: {lat_validas}/{len(df_limpio)}")
            
            # Mostrar algunas coordenadas de ejemplo
            if lat_validas > 0:
                print("Ejemplos de coordenadas de latitud:")
                for i, (idx, row) in enumerate(df_limpio.head(5).iterrows()):
                    if not pd.isna(row['latitud_limpia']):
                        print(f"  {i+1}. Original: {row[columnas_clave['latitud']]} -> Limpia: {row['latitud_limpia']}")
        
        # Limpiar longitud
        if columnas_clave['longitud']:
            print(f"Limpiando coordenadas de longitud de la columna: {columnas_clave['longitud']}")
            df_limpio['longitud_limpia'] = df_limpio[columnas_clave['longitud']].apply(extraer_primera_coordenada)
            lon_validas = df_limpio['longitud_limpia'].notna().sum()
            print(f"Coordenadas de longitud válidas: {lon_validas}/{len(df_limpio)}")
            
            # Mostrar algunas coordenadas de ejemplo
            if lon_validas > 0:
                print("Ejemplos de coordenadas de longitud:")
                for i, (idx, row) in enumerate(df_limpio.head(5).iterrows()):
                    if not pd.isna(row['longitud_limpia']):
                        print(f"  {i+1}. Original: {row[columnas_clave['longitud']]} -> Limpia: {row['longitud_limpia']}")
        
        return df_limpio
    
    def generar_sugerido_rutas(self, df_filtrado, columnas_clave, max_clientes_por_ruta=15, rutas_disponibles=None, generar_proyeccion_semanal=False, max_cajas_por_ruta=694):
        """
        Genera sugeridos de rutas optimizadas
        
        Args:
            df_filtrado: DataFrame filtrado por centro
            columnas_clave: Diccionario con nombres de columnas
            max_clientes_por_ruta: Máximo número de clientes por ruta
            rutas_disponibles: Número de rutas disponibles para asignar
            generar_proyeccion_semanal: Si True, genera proyección para toda la semana
        """
        if df_filtrado is None or len(df_filtrado) == 0:
            print("No hay datos para generar rutas")
            return
            
        # Verificar que tenemos las columnas necesarias
        columnas_requeridas = ['cliente', 'cajas_equiv', 'latitud', 'longitud']
        for col in columnas_requeridas:
            if columnas_clave[col] is None:
                print(f"Falta la columna: {col}")
                return
        
        # Limpiar datos
        df_limpio = df_filtrado.copy()
        
        # Limpiar coordenadas
        print("🧹 Limpiando coordenadas...")
        df_limpio = self.limpiar_coordenadas(df_limpio, columnas_clave)
        print(f"✅ Coordenadas limpiadas. Filas restantes: {len(df_limpio)}")
        
        # Eliminar filas sin coordenadas válidas
        print(f"🔍 Verificando coordenadas válidas...")
        print(f"   Antes de eliminar filas sin coordenadas: {len(df_limpio)} filas")
        df_limpio = df_limpio.dropna(subset=['latitud_limpia', 'longitud_limpia'])
        print(f"   Después de eliminar filas sin coordenadas: {len(df_limpio)} filas")
        
        if len(df_limpio) == 0:
            print("❌ No quedan filas después de limpiar coordenadas")
            return None
        
        # Verificar que las coordenadas son numéricas
        try:
            df_limpio['latitud_limpia'] = pd.to_numeric(df_limpio['latitud_limpia'], errors='coerce')
            df_limpio['longitud_limpia'] = pd.to_numeric(df_limpio['longitud_limpia'], errors='coerce')
            print(f"Coordenadas convertidas a numérico exitosamente")
            
            # Validar que las coordenadas están en el rango de Costa Rica
            # Costa Rica está aproximadamente entre 8° y 11° N de latitud y 82° y 86° W de longitud
            coordenadas_validas = (
                (df_limpio['latitud_limpia'] >= 8) & (df_limpio['latitud_limpia'] <= 11) &
                (df_limpio['longitud_limpia'] >= -86) & (df_limpio['longitud_limpia'] <= -82)
            )
            
            coordenadas_invalidas = ~coordenadas_validas
            if coordenadas_invalidas.sum() > 0:
                print(f"⚠️  ADVERTENCIA: {coordenadas_invalidas.sum()} coordenadas están fuera del rango de Costa Rica")
                print("Ejemplos de coordenadas inválidas:")
                for i, (idx, row) in enumerate(df_limpio[coordenadas_invalidas].head(3).iterrows()):
                    print(f"  {i+1}. Lat: {row['latitud_limpia']}, Lon: {row['longitud_limpia']}")
                
                # Filtrar solo coordenadas válidas
                df_limpio = df_limpio[coordenadas_validas].copy()
                print(f"✅ Filas restantes después de filtrar coordenadas válidas: {len(df_limpio)}")
            
        except Exception as e:
            print(f"Error al convertir coordenadas a numérico: {e}")
            # Mostrar algunos valores problemáticos
            print("Valores problemáticos en latitud:")
            for i, val in enumerate(df_limpio['latitud_limpia'].head(10)):
                print(f"  {i}: {val} (tipo: {type(val)})")
            print("Valores problemáticos en longitud:")
            for i, val in enumerate(df_limpio['longitud_limpia'].head(10)):
                print(f"  {i}: {val} (tipo: {type(val)})")
        
        # Eliminar filas sin cajas equivalentes
        print(f"📦 Verificando cajas equivalentes...")
        print(f"   Antes de eliminar filas sin cajas: {len(df_limpio)} filas")
        df_limpio = df_limpio.dropna(subset=[columnas_clave['cajas_equiv']])
        print(f"   Después de eliminar filas sin cajas: {len(df_limpio)} filas")
        
        # Convertir cajas equivalentes a numérico
        print("🔄 Convirtiendo cajas equivalentes a numérico...")
        df_limpio[columnas_clave['cajas_equiv']] = pd.to_numeric(df_limpio[columnas_clave['cajas_equiv']], errors='coerce')
        df_limpio = df_limpio.dropna(subset=[columnas_clave['cajas_equiv']])
        print(f"   Después de convertir a numérico: {len(df_limpio)} filas")
        
        if len(df_limpio) == 0:
            print("❌ No quedan filas después de procesar cajas equivalentes")
            return None
        
        print(f"\nDatos válidos para análisis: {len(df_limpio)} clientes")
        
        if len(df_limpio) == 0:
            print("❌ No hay datos válidos para generar rutas")
            return None
        
        print(f"✅ Datos válidos encontrados: {len(df_limpio)} filas")
        print(f"✅ Continuando con la generación de rutas...")
        
        # Mostrar información de rutas disponibles
        if rutas_disponibles:
            print(f"Rutas disponibles para asignar: {rutas_disponibles}")
            max_clientes_total = rutas_disponibles * max_clientes_por_ruta
            print(f"Capacidad total: {max_clientes_total} clientes ({rutas_disponibles} rutas × {max_clientes_por_ruta} clientes/ruta)")
        
        # Ordenar por volumen de cajas equivalentes (descendente)
        df_ordenado = df_limpio.sort_values(columnas_clave['cajas_equiv'], ascending=False)
        
        # Calcular centro de gravedad usando coordenadas limpias
        lat_centro = df_ordenado['latitud_limpia'].mean()
        lon_centro = df_ordenado['longitud_limpia'].mean()
        
        # Verificar que las coordenadas están en el rango de Costa Rica
        # Costa Rica está aproximadamente entre 8° y 11° N de latitud y 82° y 86° W de longitud
        if not (8 <= lat_centro <= 11) or not (-86 <= lon_centro <= -82):
            print(f"⚠️  ADVERTENCIA: Las coordenadas del centro ({lat_centro:.4f}, {lon_centro:.4f}) no parecen estar en Costa Rica")
            print("   Usando coordenadas por defecto de San José, Costa Rica")
            # Coordenadas de San José, Costa Rica (centro aproximado del país)
            lat_centro = 9.9281
            lon_centro = -84.0907
        else:
            print(f"✅ Centro de gravedad calculado: ({lat_centro:.4f}, {lon_centro:.4f}) - Costa Rica")
        
        if generar_proyeccion_semanal:
            # Generar proyección semanal
            proyeccion = self._generar_proyeccion_semanal(df_ordenado, columnas_clave, lat_centro, lon_centro, max_clientes_por_ruta, rutas_disponibles, max_cajas_por_ruta)
            # Guardar las rutas para acceso web
            self.ultima_proyeccion_generada = proyeccion
            self.ultimas_rutas_generadas = None  # Resetear si es proyección
            return proyeccion, df_ordenado, (lat_centro, lon_centro)
        else:
            # Generar rutas normales
            print("🔄 Generando rutas por proximidad...")
            rutas = self._generar_rutas_por_proximidad(df_ordenado, columnas_clave, lat_centro, lon_centro, max_clientes_por_ruta, rutas_disponibles, max_cajas_por_ruta)
            print(f"✅ Rutas generadas: {len(rutas)} rutas")
            # Guardar las rutas para acceso web
            self.ultimas_rutas_generadas = rutas
            self.ultima_proyeccion_generada = None  # Resetear si es normal
            print("💾 Rutas guardadas para acceso web")
            print(f"🔍 Verificación: self.ultimas_rutas_generadas = {len(rutas) if rutas else 0} rutas")
            print(f"✅ Método generar_sugerido_rutas completado exitosamente")
            return rutas, df_ordenado, (lat_centro, lon_centro)
    
    def _generar_rutas_por_proximidad(self, df, columnas_clave, lat_centro, lon_centro, max_clientes, rutas_disponibles=None, max_cajas_por_ruta=694):
        """Genera rutas agrupando clientes por proximidad al centro con límite de cajas por ruta"""
        # Verificar y corregir coordenadas del centro si es necesario
        if not (8 <= lat_centro <= 11) or not (-86 <= lon_centro <= -82):
            print(f"⚠️  Corrigiendo coordenadas del centro de ({lat_centro:.4f}, {lon_centro:.4f}) a San José, Costa Rica")
            lat_centro, lon_centro = 9.9281, -84.0907  # San José, Costa Rica
        
        rutas = []
        clientes_asignados = set()
        
        # Crear lista de clientes con sus coordenadas y volúmenes
        clientes = []
        for idx, row in df.iterrows():
            cliente_data = {
                'cliente': row[columnas_clave['cliente']],
                'nombre_cliente': row[columnas_clave['nombre_cliente']] if columnas_clave['nombre_cliente'] else row[columnas_clave['cliente']],
                'lat': row['latitud_limpia'],
                'lon': row['longitud_limpia'],
                'cajas': row[columnas_clave['cajas_equiv']],
                'distancia_centro': geodesic((lat_centro, lon_centro), 
                                           (row['latitud_limpia'], row['longitud_limpia'])).kilometers
            }
            
            # Agregar información de Ruta Dist si existe
            if columnas_clave['ruta_dist'] and not pd.isna(row[columnas_clave['ruta_dist']]):
                cliente_data['ruta_dist'] = row[columnas_clave['ruta_dist']]
            else:
                cliente_data['ruta_dist'] = 'Sin asignar'
            
            clientes.append(cliente_data)
        
        # Ordenar por distancia al centro
        clientes.sort(key=lambda x: x['distancia_centro'])
        
        ruta_actual = []
        volumen_ruta = 0
        ruta_numero = 1
        
        print(f"📦 Configuración de rutas:")
        print(f"   • Máximo clientes por ruta: {max_clientes}")
        print(f"   • Máximo cajas por ruta: {max_cajas_por_ruta}")
        print(f"   • Rutas disponibles: {rutas_disponibles if rutas_disponibles else 'Sin límite'}")
        
        for cliente in clientes:
            if cliente['cliente'] in clientes_asignados:
                continue
            
            # Verificar si agregar este cliente excedería los límites
            excede_clientes = len(ruta_actual) >= max_clientes
            excede_cajas = (volumen_ruta + cliente['cajas']) > max_cajas_por_ruta
            
            if excede_clientes or excede_cajas:
                if ruta_actual:
                    promedio_cajas_ruta = volumen_ruta / len(ruta_actual)
                    print(f"   Ruta {ruta_numero}: {len(ruta_actual)} clientes, {volumen_ruta:,.0f} cajas (prom: {promedio_cajas_ruta:,.1f})")
                    
                    rutas.append({
                        'ruta': ruta_numero,
                        'clientes': ruta_actual.copy(),
                        'total_cajas': volumen_ruta,
                        'total_clientes': len(ruta_actual)
                    })
                    ruta_numero += 1
                ruta_actual = []
                volumen_ruta = 0
            
            # Verificar si hemos alcanzado el límite de rutas disponibles
            if rutas_disponibles and ruta_numero > rutas_disponibles:
                print(f"⚠️  Se alcanzó el límite de {rutas_disponibles} rutas disponibles")
                break
            
            ruta_actual.append(cliente)
            volumen_ruta += cliente['cajas']
            clientes_asignados.add(cliente['cliente'])
        
        # Agregar la última ruta si tiene clientes
        if ruta_actual and (not rutas_disponibles or ruta_numero <= rutas_disponibles):
            promedio_cajas_ruta = volumen_ruta / len(ruta_actual)
            print(f"   Ruta {ruta_numero}: {len(ruta_actual)} clientes, {volumen_ruta:,.0f} cajas (prom: {promedio_cajas_ruta:,.1f})")
            
            rutas.append({
                'ruta': ruta_numero,
                'clientes': ruta_actual.copy(),
                'total_cajas': volumen_ruta,
                'total_clientes': len(ruta_actual)
            })
        
        print(f"🎯 Total de rutas generadas: {len(rutas)}")
        print(f"📊 Total de clientes asignados: {len(clientes_asignados)}")
        print(f"✅ Método _generar_rutas_por_proximidad completado exitosamente")
        return rutas
    
    def mostrar_resultados(self, rutas, df_ordenado, columnas_clave, centro_coords):
        """Muestra los resultados del análisis de rutas"""
        print("\n" + "="*60)
        print("ANÁLISIS DE RUTAS SUGERIDAS")
        print("="*60)
        
        print(f"\nCentro de distribución: {centro_coords}")
        print(f"Total de clientes analizados: {len(df_ordenado)}")
        print(f"Total de rutas generadas: {len(rutas)}")
        
        # Calcular promedios en lugar de sumatorias
        total_cajas = sum(ruta['total_cajas'] for ruta in rutas)
        total_clientes = sum(ruta['total_clientes'] for ruta in rutas)
        promedio_cajas_por_cliente = total_cajas / total_clientes if total_clientes > 0 else 0
        
        print(f"Total de cajas equivalentes: {total_cajas:,.0f}")
        print(f"Promedio de cajas por cliente: {promedio_cajas_por_cliente:,.1f}")
        
        print(f"\n{'Ruta':<6} {'Clientes':<10} {'Cajas Totales':<15} {'Promedio Cajas':<15}")
        print("-" * 50)
        
        for ruta in rutas:
            promedio_cajas = ruta['total_cajas'] / ruta['total_clientes']
            print(f"{ruta['ruta']:<6} {ruta['total_clientes']:<10} {ruta['total_cajas']:<15,.0f} {promedio_cajas:<15,.1f}")
        
        # Mostrar detalles de cada ruta
        for ruta in rutas:
            print(f"\n--- RUTA {ruta['ruta']} ---")
            print(f"Total cajas: {ruta['total_cajas']:,.0f}")
            print(f"Total clientes: {ruta['total_clientes']}")
            print(f"Promedio cajas por cliente: {ruta['total_cajas'] / ruta['total_clientes']:,.1f}")
            
            print("\nClientes en esta ruta:")
            for i, cliente in enumerate(ruta['clientes'], 1):
                print(f"{i:2d}. {cliente['cliente']:<30} {cliente['cajas']:>8,.0f} cajas "
                      f"(dist: {cliente['distancia_centro']:.1f} km)")
    
    def generar_mapa(self, rutas, centro_coords, nombre_archivo="mapa_rutas.html"):
        """Genera un mapa interactivo con las rutas"""
        # Asegurar que el directorio existe
        import os
        os.makedirs(os.path.dirname(nombre_archivo) if os.path.dirname(nombre_archivo) else '.', exist_ok=True)
        
        # Verificar y corregir coordenadas del centro si es necesario
        lat_centro, lon_centro = centro_coords
        if not (8 <= lat_centro <= 11) or not (-86 <= lon_centro <= -82):
            print(f"⚠️  Corrigiendo coordenadas del centro de ({lat_centro:.4f}, {lon_centro:.4f}) a San José, Costa Rica")
            lat_centro, lon_centro = 9.9281, -84.0907  # San José, Costa Rica
            centro_coords = (lat_centro, lon_centro)
        
        # Crear mapa centrado en el centro de distribución
        mapa = folium.Map(location=centro_coords, zoom_start=12)
        
        # Agregar marcador del centro
        folium.Marker(
            centro_coords,
            popup="Centro de Distribución",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(mapa)
        
        # Colores para las rutas
        colores = ['blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 
                  'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 
                  'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
        
        # Agregar clientes y rutas al mapa
        for i, ruta in enumerate(rutas):
            color = colores[i % len(colores)]
            
            # Crear grupo para esta ruta
            grupo_ruta = folium.FeatureGroup(name=f"Ruta {ruta['ruta']}")
            
            # Agregar clientes de esta ruta
            for cliente in ruta['clientes']:
                folium.Marker(
                    [cliente['lat'], cliente['lon']],
                    popup=f"Cliente: {cliente['cliente']}<br>Cajas: {cliente['cajas']:,.0f}",
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(grupo_ruta)
            
            grupo_ruta.add_to(mapa)
        
        # Agregar control de capas
        folium.LayerControl().add_to(mapa)
        
        # Guardar mapa
        mapa.save(nombre_archivo)
        print(f"\nMapa guardado como: {nombre_archivo}")
    
    def generar_mapa_con_waze(self, rutas, centro_coords, nombre_archivo="mapa_rutas_waze.html"):
        """Genera un mapa interactivo con las rutas e integración Waze"""
        # Asegurar que el directorio existe
        import os
        os.makedirs(os.path.dirname(nombre_archivo) if os.path.dirname(nombre_archivo) else '.', exist_ok=True)
        
        # Verificar y corregir coordenadas del centro si es necesario
        lat_centro, lon_centro = centro_coords
        if not (8 <= lat_centro <= 11) or not (-86 <= lon_centro <= -82):
            print(f"⚠️  Corrigiendo coordenadas del centro de ({lat_centro:.4f}, {lon_centro:.4f}) a San José, Costa Rica")
            lat_centro, lon_centro = 9.9281, -84.0907  # San José, Costa Rica
            centro_coords = (lat_centro, lon_centro)
        
        # Crear mapa centrado en el centro de distribución
        mapa = folium.Map(location=centro_coords, zoom_start=12)
        
        # Agregar marcador del centro
        folium.Marker(
            centro_coords,
            popup="Centro de Distribución",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(mapa)
        
        # Colores para las rutas
        colores = ['blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 
                  'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 
                  'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
        
        # Agregar clientes y rutas al mapa
        for i, ruta in enumerate(rutas):
            color = colores[i % len(colores)]
            
            # Crear grupo para esta ruta
            grupo_ruta = folium.FeatureGroup(name=f"Ruta {ruta['ruta']}")
            
            # Agregar clientes de esta ruta
            for cliente in ruta['clientes']:
                # Crear enlace Waze
                waze_url = f"https://waze.com/ul?ll={cliente['lat']},{cliente['lon']}&navigate=yes"
                
                # Crear popup con enlace Waze
                popup_html = f"""
                <div style="text-align: center;">
                    <h5>Cliente: {cliente['cliente']}</h5>
                    <p><strong>Cajas:</strong> {cliente['cajas']:,.0f}</p>
                    <p><strong>Distancia:</strong> {cliente['distancia_centro']:.1f} km</p>
                    <hr>
                    <a href="{waze_url}" target="_blank" style="
                        background-color: #33ccff; 
                        color: white; 
                        padding: 8px 16px; 
                        text-decoration: none; 
                        border-radius: 5px; 
                        display: inline-block;
                        margin-top: 5px;
                    ">
                        <i class="fas fa-car"></i> Abrir en Waze
                    </a>
                </div>
                """
                
                folium.Marker(
                    [cliente['lat'], cliente['lon']],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(grupo_ruta)
            
            grupo_ruta.add_to(mapa)
        
        # Agregar control de capas
        folium.LayerControl().add_to(mapa)
        
        # Agregar información sobre Waze
        info_html = """
        <div style="
            position: fixed; 
            top: 10px; 
            right: 10px; 
            width: 300px; 
            height: auto; 
            background-color: white; 
            border:2px solid grey; 
            z-index:9999; 
            font-size:14px;
            padding: 10px;
            border-radius: 5px;
        ">
            <h4><i class="fas fa-car"></i> Integración Waze</h4>
            <p>Haz clic en cualquier marcador de cliente y luego en "Abrir en Waze" para obtener direcciones de navegación.</p>
            <p><strong>Características:</strong></p>
            <ul>
                <li>Navegación GPS en tiempo real</li>
                <li>Alertas de tráfico</li>
                <li>Rutas optimizadas</li>
                <li>Información de tiempo de llegada</li>
            </ul>
        </div>
        """
        
        mapa.get_root().html.add_child(folium.Element(info_html))
        
        # Guardar mapa
        mapa.save(nombre_archivo)
        print(f"\nMapa con integración Waze guardado como: {nombre_archivo}")
    
    def generar_reporte_excel(self, rutas, df_ordenado, columnas_clave, nombre_archivo="reporte_rutas.xlsx"):
        """Genera un reporte en Excel con las rutas sugeridas agrupadas por cliente"""
        # Asegurar que el directorio existe
        import os
        os.makedirs(os.path.dirname(nombre_archivo) if os.path.dirname(nombre_archivo) else '.', exist_ok=True)
        
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            
            # Hoja 1: Resumen de rutas
            resumen_data = []
            total_cajas = 0
            total_clientes = 0
            
            for ruta in rutas:
                resumen_data.append({
                    'Ruta': ruta['ruta'],
                    'Total Clientes': ruta['total_clientes'],
                    'Total Cajas': ruta['total_cajas'],
                    'Promedio Cajas por Cliente': ruta['total_cajas'] / ruta['total_clientes']
                })
                total_cajas += ruta['total_cajas']
                total_clientes += ruta['total_clientes']
            
            # Agregar fila de totales
            resumen_data.append({
                'Ruta': 'TOTAL',
                'Total Clientes': total_clientes,
                'Total Cajas': total_cajas,
                'Promedio Cajas por Cliente': total_cajas / total_clientes if total_clientes > 0 else 0
            })
            
            df_resumen = pd.DataFrame(resumen_data)
            df_resumen.to_excel(writer, sheet_name='Resumen Rutas', index=False)
            
            # Hoja 2: Detalle de clientes por ruta (agrupado por cliente)
            detalle_agrupado = []
            for ruta in rutas:
                # Agrupar clientes por nombre para obtener totales
                clientes_agrupados = {}
                for cliente in ruta['clientes']:
                    nombre_cliente = cliente['cliente']
                    if nombre_cliente not in clientes_agrupados:
                        clientes_agrupados[nombre_cliente] = {
                            'ruta': ruta['ruta'],
                            'cliente': nombre_cliente,
                            'nombre_cliente': cliente.get('nombre_cliente', nombre_cliente),
                            'total_cajas': 0,
                            'latitud': cliente['lat'],
                            'longitud': cliente['lon'],
                            'distancia_centro': cliente['distancia_centro'],
                            'ruta_dist': cliente.get('ruta_dist', 'Sin asignar'),
                            'num_entregas': 0
                        }
                    clientes_agrupados[nombre_cliente]['total_cajas'] += cliente['cajas']
                    clientes_agrupados[nombre_cliente]['num_entregas'] += 1
                
                # Agregar a la lista de detalles
                for cliente_data in clientes_agrupados.values():
                    detalle_agrupado.append({
                        'Ruta': cliente_data['ruta'],
                        'Cliente': cliente_data['cliente'],
                        'Nombre del Cliente': cliente_data['nombre_cliente'],
                        'Ruta Dist.': cliente_data['ruta_dist'],
                        'Total Cajas Equivalentes': cliente_data['total_cajas'],
                        'Número de Entregas': cliente_data['num_entregas'],
                        'Promedio Cajas por Entrega': cliente_data['total_cajas'] / cliente_data['num_entregas'],
                        'Latitud': cliente_data['latitud'],
                        'Longitud': cliente_data['longitud'],
                        'Distancia al Centro (km)': cliente_data['distancia_centro']
                    })
            
            df_detalle_agrupado = pd.DataFrame(detalle_agrupado)
            df_detalle_agrupado.to_excel(writer, sheet_name='Clientes por Ruta', index=False)
            
            # Hoja 3: Datos detallados con estructura web (como en las imágenes)
            datos_detallados = []
            for ruta in rutas:
                for cliente in ruta['clientes']:
                    # Obtener datos adicionales del DataFrame original
                    cliente_id = cliente['cliente']
                    cliente_row = df_ordenado[df_ordenado[columnas_clave['cliente']] == cliente_id].iloc[0] if len(df_ordenado[df_ordenado[columnas_clave['cliente']] == cliente_id]) > 0 else None
                    
                    datos_detallados.append({
                        'Centro': cliente_row[columnas_clave['centro']] if cliente_row is not None else 'N/A',
                        'dia': cliente_row.get('dia entrega', 'N/A') if cliente_row is not None else 'N/A',
                        'Cliente': cliente_id,
                        'Nombre de': cliente.get('nombre_cliente', cliente_id),
                        'Ruta': ruta['ruta'],
                        'Viaje': cliente_row.get('Viaje', 'N/A') if cliente_row is not None else 'N/A',
                        'Latitud': cliente['lat'],
                        'Longitud': cliente['lon'],
                        'Provincia': cliente_row.get('Provincia', 'N/A') if cliente_row is not None else 'N/A',
                        'Cantón': cliente_row.get('Cantón', 'N/A') if cliente_row is not None else 'N/A',
                        'Distrito': cliente_row.get('Distrito', 'N/A') if cliente_row is not None else 'N/A',
                        'Promedio de Cajas Equiv.': cliente['cajas']
                    })
            
            df_detallado = pd.DataFrame(datos_detallados)
            df_detallado.to_excel(writer, sheet_name='Datos Detallados Web', index=False)
            
            # Hoja 3: Resumen por cliente (todos los centros)
            resumen_clientes = {}
            for ruta in rutas:
                for cliente in ruta['clientes']:
                    nombre_cliente = cliente['cliente']
                    if nombre_cliente not in resumen_clientes:
                        resumen_clientes[nombre_cliente] = {
                            'cliente': nombre_cliente,
                            'total_cajas': 0,
                            'num_entregas': 0,
                            'rutas_asignadas': set(),
                            'latitud': cliente['lat'],
                            'longitud': cliente['lon']
                        }
                    resumen_clientes[nombre_cliente]['total_cajas'] += cliente['cajas']
                    resumen_clientes[nombre_cliente]['num_entregas'] += 1
                    resumen_clientes[nombre_cliente]['rutas_asignadas'].add(ruta['ruta'])
            
            # Convertir a lista para el DataFrame
            resumen_clientes_list = []
            for cliente_data in resumen_clientes.values():
                resumen_clientes_list.append({
                    'Cliente': cliente_data['cliente'],
                    'Nombre del Cliente': cliente_data.get('nombre_cliente', cliente_data['cliente']),
                    'Total Cajas Equivalentes': cliente_data['total_cajas'],
                    'Número de Entregas': cliente_data['num_entregas'],
                    'Promedio Cajas por Entrega': cliente_data['total_cajas'] / cliente_data['num_entregas'],
                    'Rutas Asignadas': ', '.join(map(str, sorted(cliente_data['rutas_asignadas']))),
                    'Latitud': cliente_data['latitud'],
                    'Longitud': cliente_data['longitud']
                })
            
            df_resumen_clientes = pd.DataFrame(resumen_clientes_list)
            df_resumen_clientes.to_excel(writer, sheet_name='Resumen por Cliente', index=False)
            
            # Hoja 4: Datos originales filtrados
            df_ordenado.to_excel(writer, sheet_name='Datos Originales', index=False)
        
        print(f"Reporte Excel guardado como: {nombre_archivo}")
        print(f"- Hoja 1: Resumen de rutas")
        print(f"- Hoja 2: Clientes agrupados por ruta")
        print(f"- Hoja 3: Resumen total por cliente")
        print(f"- Hoja 4: Datos originales")

    def _generar_proyeccion_semanal(self, df_limpio, columnas_clave, lat_centro, lon_centro, max_clientes_por_ruta, rutas_disponibles=None, max_cajas_por_ruta=694):
        """
        Genera proyección de rutas para toda la semana
        """
        from datetime import datetime, timedelta
        
        # Verificar y corregir coordenadas del centro si es necesario
        if not (8 <= lat_centro <= 11) or not (-86 <= lon_centro <= -82):
            print(f"⚠️  Corrigiendo coordenadas del centro de ({lat_centro:.4f}, {lon_centro:.4f}) a San José, Costa Rica")
            lat_centro, lon_centro = 9.9281, -84.0907  # San José, Costa Rica
        
        # Obtener fecha actual
        fecha_actual = datetime.now()
        
        # Definir días de la semana
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        # Calcular qué día de la semana es hoy
        dia_actual = fecha_actual.weekday()  # 0=Lunes, 1=Martes, ..., 6=Domingo
        
        print(f"\n{'='*60}")
        print(f"PROYECCIÓN SEMANAL DE RUTAS - Hoy es {dias_semana[dia_actual]}")
        print(f"{'='*60}")
        
        # Crear lista de clientes con sus datos
        clientes = []
        for idx, row in df_limpio.iterrows():
            cliente_data = {
                'cliente': row[columnas_clave['cliente']],
                'nombre_cliente': row[columnas_clave['nombre_cliente']] if columnas_clave['nombre_cliente'] else row[columnas_clave['cliente']],
                'lat': row['latitud_limpia'],
                'lon': row['longitud_limpia'],
                'cajas': row[columnas_clave['cajas_equiv']],
                'distancia_centro': geodesic((lat_centro, lon_centro), 
                                           (row['latitud_limpia'], row['longitud_limpia'])).kilometers
            }
            
            # Agregar información de Ruta Dist si existe
            if columnas_clave['ruta_dist'] and not pd.isna(row[columnas_clave['ruta_dist']]):
                cliente_data['ruta_dist'] = row[columnas_clave['ruta_dist']]
            else:
                cliente_data['ruta_dist'] = 'Sin asignar'
            
            clientes.append(cliente_data)
        
        # Ordenar clientes por volumen de cajas (descendente)
        clientes.sort(key=lambda x: x['cajas'], reverse=True)
        
        # Distribuir clientes por días de la semana
        proyeccion_semanal = {}
        clientes_asignados = set()
        
        # Empezar desde el día siguiente al actual
        for i in range(7):
            dia_idx = (dia_actual + i + 1) % 7  # Siguiente día
            dia_nombre = dias_semana[dia_idx]
            
            if dia_nombre in ['Sábado', 'Domingo']:
                continue  # Saltar fines de semana
            
            proyeccion_semanal[dia_nombre] = []
            rutas_dia = []
            ruta_actual = []
            volumen_ruta = 0
            
            # Asignar clientes no asignados a este día
            for cliente in clientes:
                if cliente['cliente'] in clientes_asignados:
                    continue
                
                # Verificar si agregar este cliente excedería los límites
                excede_clientes = len(ruta_actual) >= max_clientes_por_ruta
                excede_cajas = (volumen_ruta + cliente['cajas']) > max_cajas_por_ruta
                
                if excede_clientes or excede_cajas:
                    if ruta_actual:
                        rutas_dia.append({
                            'ruta': len(rutas_dia) + 1,
                            'clientes': ruta_actual.copy(),
                            'total_cajas': volumen_ruta,
                            'total_clientes': len(ruta_actual)
                        })
                    ruta_actual = []
                    volumen_ruta = 0
                
                ruta_actual.append(cliente)
                volumen_ruta += cliente['cajas']
                clientes_asignados.add(cliente['cliente'])
            
            # Agregar la última ruta del día si tiene clientes
            if ruta_actual:
                rutas_dia.append({
                    'ruta': len(rutas_dia) + 1,
                    'clientes': ruta_actual.copy(),
                    'total_cajas': volumen_ruta,
                    'total_clientes': len(ruta_actual)
                })
            
            proyeccion_semanal[dia_nombre] = rutas_dia
            
            # Si no quedan clientes por asignar, salir del bucle
            if len(clientes_asignados) == len(clientes):
                break
        
        # Mostrar proyección semanal
        self._mostrar_proyeccion_semanal(proyeccion_semanal, dias_semana, dia_actual)
        
        # Generar reporte de proyección
        self._generar_reporte_proyeccion_semanal(proyeccion_semanal, columnas_clave)
        
        # Generar mapas por día
        self._generar_mapas_proyeccion_semanal(proyeccion_semanal, lat_centro, lon_centro)
        
        return proyeccion_semanal

    def _mostrar_proyeccion_semanal(self, proyeccion_semanal, dias_semana, dia_actual):
        """Muestra la proyección semanal de rutas"""
        print(f"\nPROYECCIÓN DE RUTAS PARA LA SEMANA:")
        print(f"Fecha de análisis: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"Día actual: {dias_semana[dia_actual]}")
        
        total_rutas_semana = 0
        total_cajas_semana = 0
        total_clientes_semana = 0
        
        for dia, rutas in proyeccion_semanal.items():
            if not rutas:
                continue
                
            print(f"\n{'='*50}")
            print(f"📅 {dia.upper()}")
            print(f"{'='*50}")
            
            total_rutas_dia = len(rutas)
            total_cajas_dia = sum(ruta['total_cajas'] for ruta in rutas)
            total_clientes_dia = sum(ruta['total_clientes'] for ruta in rutas)
            promedio_cajas_por_cliente = total_cajas_dia / total_clientes_dia if total_clientes_dia > 0 else 0
            
            print(f"📊 Resumen del día:")
            print(f"   • Rutas programadas: {total_rutas_dia}")
            print(f"   • Total clientes: {total_clientes_dia}")
            print(f"   • Total cajas: {total_cajas_dia:,.0f}")
            print(f"   • Promedio cajas por cliente: {promedio_cajas_por_cliente:,.1f}")
            print(f"   • Promedio cajas por ruta: {total_cajas_dia/total_rutas_dia:,.0f}")
            
            print(f"\n🚚 Detalle de rutas:")
            for ruta in rutas:
                promedio_ruta = ruta['total_cajas'] / ruta['total_clientes']
                print(f"   Ruta {ruta['ruta']}: {ruta['total_clientes']} clientes, {ruta['total_cajas']:,.0f} cajas (prom: {promedio_ruta:,.1f})")
            
            total_rutas_semana += total_rutas_dia
            total_cajas_semana += total_cajas_dia
            total_clientes_semana += total_clientes_dia
        
        print(f"\n{'='*60}")
        print(f"📈 RESUMEN SEMANAL")
        print(f"{'='*60}")
        print(f"Total rutas programadas: {total_rutas_semana}")
        print(f"Total clientes a atender: {total_clientes_semana}")
        print(f"Total cajas a distribuir: {total_cajas_semana:,.0f}")
        promedio_semanal = total_cajas_semana / total_clientes_semana if total_clientes_semana > 0 else 0
        print(f"Promedio cajas por cliente: {promedio_semanal:,.1f}")
        print(f"Promedio cajas por ruta: {total_cajas_semana/total_rutas_semana:,.0f}")

    def _generar_reporte_proyeccion_semanal(self, proyeccion_semanal, columnas_clave):
        """Genera reporte Excel de la proyección semanal agrupado por cliente"""
        nombre_archivo = f"proyeccion_semanal_rutas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            
            # Hoja 1: Resumen semanal
            resumen_semanal = []
            for dia, rutas in proyeccion_semanal.items():
                if not rutas:
                    continue
                    
                total_rutas = len(rutas)
                total_cajas = sum(ruta['total_cajas'] for ruta in rutas)
                total_clientes = sum(ruta['total_clientes'] for ruta in rutas)
                promedio_cajas_por_cliente = total_cajas / total_clientes if total_clientes > 0 else 0
                
                resumen_semanal.append({
                    'Día': dia,
                    'Total Rutas': total_rutas,
                    'Total Clientes': total_clientes,
                    'Total Cajas': total_cajas,
                    'Promedio Cajas por Cliente': promedio_cajas_por_cliente,
                    'Promedio Cajas por Ruta': total_cajas / total_rutas if total_rutas > 0 else 0
                })
            
            df_resumen = pd.DataFrame(resumen_semanal)
            df_resumen.to_excel(writer, sheet_name='Resumen Semanal', index=False)
            
            # Hoja 2: Datos detallados con estructura web para toda la semana
            datos_detallados_semana = []
            for dia, rutas in proyeccion_semanal.items():
                if not rutas:
                    continue
                    
                for ruta in rutas:
                    for cliente in ruta['clientes']:
                        datos_detallados_semana.append({
                            'Centro': 'N/A',  # Se puede obtener del DataFrame original si es necesario
                            'dia': dia,
                            'Cliente': cliente['cliente'],
                            'Nombre de': cliente.get('nombre_cliente', cliente['cliente']),
                            'Ruta': ruta['ruta'],
                            'Viaje': 'N/A',  # Se puede obtener del DataFrame original si es necesario
                            'Latitud': cliente['lat'],
                            'Longitud': cliente['lon'],
                            'Provincia': 'N/A',  # Se puede obtener del DataFrame original si es necesario
                            'Cantón': 'N/A',  # Se puede obtener del DataFrame original si es necesario
                            'Distrito': 'N/A',  # Se puede obtener del DataFrame original si es necesario
                            'Promedio de Cajas Equiv.': cliente['cajas']
                        })
            
            df_detallado_semana = pd.DataFrame(datos_detallados_semana)
            df_detallado_semana.to_excel(writer, sheet_name='Datos Detallados Web', index=False)
            
            # Hoja 2: Clientes agrupados por día
            for dia, rutas in proyeccion_semanal.items():
                if not rutas:
                    continue
                    
                # Agrupar clientes por nombre para obtener totales
                clientes_agrupados = {}
                for ruta in rutas:
                    for cliente in ruta['clientes']:
                        nombre_cliente = cliente['cliente']
                        if nombre_cliente not in clientes_agrupados:
                                                    clientes_agrupados[nombre_cliente] = {
                            'dia': dia,
                            'cliente': nombre_cliente,
                            'total_cajas': 0,
                            'num_entregas': 0,
                            'rutas_asignadas': set(),
                            'latitud': cliente['lat'],
                            'longitud': cliente['lon'],
                            'distancia_centro': cliente['distancia_centro'],
                            'ruta_dist': cliente.get('ruta_dist', 'Sin asignar')
                        }
                        clientes_agrupados[nombre_cliente]['total_cajas'] += cliente['cajas']
                        clientes_agrupados[nombre_cliente]['num_entregas'] += 1
                        clientes_agrupados[nombre_cliente]['rutas_asignadas'].add(ruta['ruta'])
                
                # Convertir a lista para el DataFrame
                detalle_dia_agrupado = []
                for cliente_data in clientes_agrupados.values():
                    detalle_dia_agrupado.append({
                        'Día': cliente_data['dia'],
                        'Cliente': cliente_data['cliente'],
                        'Ruta Dist.': cliente_data['ruta_dist'],
                        'Total Cajas Equivalentes': cliente_data['total_cajas'],
                        'Número de Entregas': cliente_data['num_entregas'],
                        'Promedio Cajas por Entrega': cliente_data['total_cajas'] / cliente_data['num_entregas'],
                        'Rutas Asignadas': ', '.join(map(str, sorted(cliente_data['rutas_asignadas']))),
                        'Latitud': cliente_data['latitud'],
                        'Longitud': cliente_data['longitud'],
                        'Distancia al Centro (km)': cliente_data['distancia_centro']
                    })
                
                df_detalle = pd.DataFrame(detalle_dia_agrupado)
                df_detalle.to_excel(writer, sheet_name=f'Clientes_{dia}', index=False)
            
            # Hoja 3: Resumen total por cliente (toda la semana)
            resumen_clientes_semana = {}
            for dia, rutas in proyeccion_semanal.items():
                if not rutas:
                    continue
                    
                for ruta in rutas:
                    for cliente in ruta['clientes']:
                        nombre_cliente = cliente['cliente']
                        if nombre_cliente not in resumen_clientes_semana:
                            resumen_clientes_semana[nombre_cliente] = {
                                'cliente': nombre_cliente,
                                'total_cajas': 0,
                                'num_entregas': 0,
                                'dias_asignados': set(),
                                'rutas_asignadas': set(),
                                'latitud': cliente['lat'],
                                'longitud': cliente['lon']
                            }
                        resumen_clientes_semana[nombre_cliente]['total_cajas'] += cliente['cajas']
                        resumen_clientes_semana[nombre_cliente]['num_entregas'] += 1
                        resumen_clientes_semana[nombre_cliente]['dias_asignados'].add(dia)
                        resumen_clientes_semana[nombre_cliente]['rutas_asignadas'].add(f"{dia}-R{ruta['ruta']}")
            
            # Convertir a lista para el DataFrame
            resumen_clientes_list = []
            for cliente_data in resumen_clientes_semana.values():
                resumen_clientes_list.append({
                    'Cliente': cliente_data['cliente'],
                    'Total Cajas Equivalentes': cliente_data['total_cajas'],
                    'Número de Entregas': cliente_data['num_entregas'],
                    'Promedio Cajas por Entrega': cliente_data['total_cajas'] / cliente_data['num_entregas'],
                    'Días Asignados': ', '.join(sorted(cliente_data['dias_asignados'])),
                    'Rutas Asignadas': ', '.join(sorted(cliente_data['rutas_asignadas'])),
                    'Latitud': cliente_data['latitud'],
                    'Longitud': cliente_data['longitud']
                })
            
            df_resumen_clientes = pd.DataFrame(resumen_clientes_list)
            df_resumen_clientes.to_excel(writer, sheet_name='Resumen_Clientes_Semana', index=False)
        
        print(f"\n📄 Reporte de proyección semanal guardado como: {nombre_archivo}")
        print(f"- Hoja 1: Resumen semanal")
        print(f"- Hoja 2: Clientes agrupados por día")
        print(f"- Hoja 3: Resumen total por cliente (toda la semana)")

    def _generar_mapas_proyeccion_semanal(self, proyeccion_semanal, lat_centro, lon_centro):
        """Genera mapas interactivos para cada día de la proyección"""
        for dia, rutas in proyeccion_semanal.items():
            if not rutas:
                continue
                
            nombre_archivo = f"mapa_proyeccion_{dia.lower()}.html"
            
            # Crear mapa
            mapa = folium.Map(location=(lat_centro, lon_centro), zoom_start=12)
            
            # Agregar marcador del centro
            folium.Marker(
                (lat_centro, lon_centro),
                popup="Centro de Distribución",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(mapa)
            
            # Colores para las rutas
            colores = ['blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 
                      'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 
                      'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
            
            # Agregar rutas al mapa
            for i, ruta in enumerate(rutas):
                color = colores[i % len(colores)]
                
                # Crear coordenadas de la ruta
                coordenadas = [(lat_centro, lon_centro)]  # Empezar desde el centro
                for cliente in ruta['clientes']:
                    coordenadas.append((cliente['lat'], cliente['lon']))
                coordenadas.append((lat_centro, lon_centro))  # Volver al centro
                
                # Agregar línea de la ruta
                folium.PolyLine(
                    coordenadas,
                    weight=3,
                    color=color,
                    opacity=0.8,
                    popup=f"Ruta {ruta['ruta']}: {ruta['total_clientes']} clientes, {ruta['total_cajas']:,.0f} cajas"
                ).add_to(mapa)
                
                # Agregar marcadores de clientes
                for j, cliente in enumerate(ruta['clientes']):
                    folium.Marker(
                        (cliente['lat'], cliente['lon']),
                        popup=f"Cliente: {cliente['cliente']}<br>Cajas: {cliente['cajas']:,.0f}<br>Ruta: {ruta['ruta']}",
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(mapa)
            
            # Guardar mapa
            mapa.save(nombre_archivo)
            print(f"🗺️  Mapa para {dia} guardado como: {nombre_archivo}")

def main():
    """Función principal para ejecutar el análisis"""
    # Inicializar analizador
    analizador = AnalizadorRutas("Data/REP PLR ESTATUS ENTREGAS v25.xlsx")
    
    # Cargar datos
    if not analizador.cargar_datos():
        return
    
    # Explorar datos
    analizador.explorar_datos()
    
    # Identificar columnas clave
    columnas_clave = analizador.identificar_columnas_clave()
    
    # Solicitar centro al usuario
    print("\n" + "="*50)
    print("ANÁLISIS DE RUTAS")
    print("="*50)
    
    # Mostrar centros disponibles si se encontró la columna
    if columnas_clave['centro']:
        centros = analizador.df[columnas_clave['centro']].unique()
        print(f"Centros disponibles: {centros}")
        
        # Por ahora, usar el primer centro disponible
        centro_seleccionado = centros[0]
        print(f"Usando centro: {centro_seleccionado}")
    else:
        print("No se encontró columna de centro. Analizando todos los datos.")
        centro_seleccionado = None
    
    # Filtrar por centro
    if centro_seleccionado:
        resultado = analizador.filtrar_por_centro(centro_seleccionado)
        if resultado is None:
            return
        df_filtrado, columnas_clave = resultado
    else:
        df_filtrado = analizador.df
        columnas_clave = analizador.identificar_columnas_clave()
    
    # Generar sugeridos de rutas
    resultado_rutas = analizador.generar_sugerido_rutas(df_filtrado, columnas_clave)
    if resultado_rutas is None:
        return
    
    rutas, df_ordenado, centro_coords = resultado_rutas
    
    # Mostrar resultados
    analizador.mostrar_resultados(rutas, df_ordenado, columnas_clave, centro_coords)
    
    # Generar mapa
    analizador.generar_mapa(rutas, centro_coords)
    
    # Generar reporte Excel
    analizador.generar_reporte_excel(rutas, df_ordenado, columnas_clave)
    
    print("\n¡Análisis completado exitosamente!")

if __name__ == "__main__":
    main()
