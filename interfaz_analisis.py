import pandas as pd
from analisis_rutas import AnalizadorRutas
import os

def mostrar_menu_centros(centros):
    """Muestra un menú para seleccionar el centro"""
    print("\n" + "="*50)
    print("CENTROS DISPONIBLES")
    print("="*50)
    
    for i, centro in enumerate(centros, 1):
        print(f"{i}. {centro}")
    
    print(f"{len(centros) + 1}. Analizar todos los centros")
    print("0. Salir")
    
    while True:
        try:
            opcion = int(input(f"\nSeleccione un centro (0-{len(centros) + 1}): "))
            if 0 <= opcion <= len(centros) + 1:
                if opcion == 0:
                    return None
                elif opcion == len(centros) + 1:
                    return "TODOS"
                else:
                    return centros[opcion - 1]
            else:
                print("Opción inválida. Intente de nuevo.")
        except ValueError:
            print("Por favor ingrese un número válido.")

def mostrar_menu_tipo_analisis():
    """Muestra un menú para seleccionar el tipo de análisis"""
    print("\n" + "="*50)
    print("TIPO DE ANÁLISIS")
    print("="*50)
    print("1. Análisis de rutas normal")
    print("2. Proyección semanal de rutas")
    print("0. Salir")
    
    while True:
        try:
            opcion = int(input(f"\nSeleccione el tipo de análisis (0-2): "))
            if 0 <= opcion <= 2:
                return opcion
            else:
                print("Opción inválida. Intente nuevamente.")
        except ValueError:
            print("Por favor ingrese un número válido.")

def configurar_parametros():
    """Permite configurar parámetros del análisis"""
    print("\n" + "="*50)
    print("CONFIGURACIÓN DE PARÁMETROS")
    print("="*50)
    
    # Máximo clientes por ruta
    while True:
        try:
            max_clientes = int(input("Máximo número de clientes por ruta (default: 15): ") or "15")
            if max_clientes > 0:
                break
            else:
                print("El número debe ser mayor a 0.")
        except ValueError:
            print("Por favor ingrese un número válido.")
    
    # Máximo número de cajas por ruta
    while True:
        try:
            max_cajas_input = input("Máximo número de cajas por ruta (default: 694): ") or "694"
            max_cajas_por_ruta = int(max_cajas_input)
            if max_cajas_por_ruta > 0:
                break
            else:
                print("El número debe ser mayor a 0.")
        except ValueError:
            print("Por favor ingrese un número válido.")
    
    # Número de rutas disponibles
    while True:
        try:
            rutas_disponibles_input = input("¿Cuántas rutas tiene disponibles? (dejar vacío para sin límite): ").strip()
            if rutas_disponibles_input == "":
                rutas_disponibles = None
                break
            else:
                rutas_disponibles = int(rutas_disponibles_input)
                if rutas_disponibles > 0:
                    break
                else:
                    print("El número debe ser mayor a 0.")
        except ValueError:
            print("Por favor ingrese un número válido.")
    
    # Nombre del archivo de salida
    nombre_archivo = input("Nombre del archivo de reporte (default: reporte_rutas): ") or "reporte_rutas"
    
    return {
        'max_clientes_por_ruta': max_clientes,
        'max_cajas_por_ruta': max_cajas_por_ruta,
        'rutas_disponibles': rutas_disponibles,
        'nombre_archivo': nombre_archivo
    }

def main_interactivo():
    """Función principal con interfaz interactiva"""
    print("="*60)
    print("ANÁLISIS DE RUTAS - SISTEMA DE SUGERIDOS")
    print("="*60)
    print("Este sistema analiza el archivo Excel y genera sugeridos de rutas")
    print("optimizadas basándose en volúmenes y ubicaciones geográficas.")
    
    # Verificar que el archivo existe
    archivo_excel = "Data/REP PLR ESTATUS ENTREGAS v25.xlsx"
    if not os.path.exists(archivo_excel):
        print(f"\nError: No se encontró el archivo {archivo_excel}")
        print("Asegúrese de que el archivo esté en la carpeta Data/")
        return
    
    # Inicializar analizador
    analizador = AnalizadorRutas(archivo_excel)
    
    # Cargar datos
    print("\nCargando datos del archivo Excel...")
    if not analizador.cargar_datos():
        print("Error al cargar los datos. Verifique el archivo.")
        return
    
    # Explorar datos
    analizador.explorar_datos()
    
    # Identificar columnas clave
    columnas_clave = analizador.identificar_columnas_clave()
    
    # Verificar que tenemos las columnas necesarias
    columnas_faltantes = []
    for clave, valor in columnas_clave.items():
        if valor is None and clave in ['cliente', 'cajas_equiv', 'latitud', 'longitud']:
            columnas_faltantes.append(clave)
    
    if columnas_faltantes:
        print(f"\nADVERTENCIA: No se encontraron las siguientes columnas: {columnas_faltantes}")
        print("El análisis puede no funcionar correctamente.")
        continuar = input("¿Desea continuar de todas formas? (s/n): ").lower()
        if continuar != 's':
            return
    
    # Seleccionar centro
    if columnas_clave['centro']:
        centros = analizador.df[columnas_clave['centro']].unique()
        centro_seleccionado = mostrar_menu_centros(centros)
        
        if centro_seleccionado is None:
            print("Análisis cancelado.")
            return
    else:
        print("\nNo se encontró columna de centro. Analizando todos los datos.")
        centro_seleccionado = "TODOS"
    
    # Seleccionar tipo de análisis
    tipo_analisis = mostrar_menu_tipo_analisis()
    if tipo_analisis == 0:
        print("Análisis cancelado.")
        return
    
    # Configurar parámetros
    parametros = configurar_parametros()
    
    # Ejecutar análisis
    print("\n" + "="*50)
    print("EJECUTANDO ANÁLISIS")
    print("="*50)
    
    if centro_seleccionado == "TODOS":
        df_filtrado = analizador.df
        print("Analizando todos los centros...")
    else:
        resultado = analizador.filtrar_por_centro(centro_seleccionado)
        if resultado is None:
            return
        df_filtrado, columnas_clave = resultado
        print(f"Analizando centro: {centro_seleccionado}")
    
    # Generar sugeridos de rutas
    generar_proyeccion = (tipo_analisis == 2)
    resultado_rutas = analizador.generar_sugerido_rutas(
        df_filtrado, 
        columnas_clave, 
        parametros['max_clientes_por_ruta'],
        parametros['rutas_disponibles'],
        generar_proyeccion,
        parametros['max_cajas_por_ruta']
    )
    
    if resultado_rutas is None:
        print("No se pudieron generar rutas. Verifique los datos.")
        return
    
    resultado, df_ordenado, centro_coords = resultado_rutas
    
    if generar_proyeccion:
        # Proyección semanal
        proyeccion_semanal = resultado
        print("\n" + "="*60)
        print("PROYECCIÓN SEMANAL COMPLETADA")
        print("="*60)
        print("Se han generado los siguientes archivos:")
        
        # Contar totales de la proyección
        total_rutas_semana = 0
        total_cajas_semana = 0
        total_clientes_semana = 0
        
        for dia, rutas in proyeccion_semanal.items():
            if rutas:
                total_rutas_semana += len(rutas)
                total_cajas_semana += sum(ruta['total_cajas'] for ruta in rutas)
                total_clientes_semana += sum(ruta['total_clientes'] for ruta in rutas)
        
        print(f"- Reporte Excel de proyección semanal")
        print(f"- Mapas interactivos por día de la semana")
        print(f"- Total de rutas programadas: {total_rutas_semana}")
        print(f"- Total de clientes a atender: {total_clientes_semana}")
        print(f"- Total de cajas a distribuir: {total_cajas_semana:,.0f}")
        
    else:
        # Análisis normal
        rutas = resultado
        
        # Mostrar resultados
        analizador.mostrar_resultados(rutas, df_ordenado, columnas_clave, centro_coords)
        
        # Generar archivos de salida
        print("\n" + "="*50)
        print("GENERANDO ARCHIVOS DE SALIDA")
        print("="*50)
        
        # Mapa interactivo
        nombre_mapa = f"{parametros['nombre_archivo']}_mapa.html"
        analizador.generar_mapa(rutas, centro_coords, nombre_mapa)
        
        # Reporte Excel
        nombre_excel = f"{parametros['nombre_archivo']}.xlsx"
        analizador.generar_reporte_excel(rutas, df_ordenado, columnas_clave, nombre_excel)
        
        print("\n" + "="*60)
        print("ANÁLISIS COMPLETADO EXITOSAMENTE")
        print("="*60)
        print(f"Archivos generados:")
        print(f"- Mapa interactivo: {nombre_mapa}")
        print(f"- Reporte Excel: {nombre_excel}")
        print(f"- Total de rutas generadas: {len(rutas)}")
        print(f"- Total de clientes analizados: {len(df_ordenado)}")
        
        # Mostrar resumen de rutas
        total_cajas = sum(ruta['total_cajas'] for ruta in rutas)
        print(f"- Total de cajas equivalentes: {total_cajas:,.0f}")
        print(f"- Promedio de cajas por ruta: {total_cajas/len(rutas):,.0f}")

if __name__ == "__main__":
    main_interactivo()
