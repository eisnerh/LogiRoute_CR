import pandas as pd
import os
from datetime import datetime

def verificar_reportes():
    """Verifica y muestra un resumen de los reportes generados"""
    print("="*60)
    print("VERIFICACIÓN DE REPORTES GENERADOS")
    print("="*60)
    
    # Buscar archivos de reporte
    archivos_excel = [f for f in os.listdir('.') if f.endswith('.xlsx') and 'proyeccion' in f.lower()]
    archivos_html = [f for f in os.listdir('.') if f.endswith('.html') and 'mapa' in f.lower()]
    
    print(f"\n📊 ARCHIVOS EXCEL ENCONTRADOS ({len(archivos_excel)}):")
    for archivo in sorted(archivos_excel):
        tamaño = os.path.getsize(archivo) / 1024  # KB
        print(f"   • {archivo} ({tamaño:.1f} KB)")
        
        # Intentar leer y mostrar resumen del archivo
        try:
            if 'proyeccion' in archivo.lower():
                # Leer resumen semanal
                df_resumen = pd.read_excel(archivo, sheet_name='Resumen Semanal')
                print(f"     - Resumen semanal: {len(df_resumen)} días programados")
                
                # Leer resumen de clientes
                df_clientes = pd.read_excel(archivo, sheet_name='Resumen_Clientes_Semana')
                print(f"     - Total clientes únicos: {len(df_clientes)}")
                
                total_cajas = df_clientes['Total Cajas Equivalentes'].sum()
                print(f"     - Total cajas a distribuir: {total_cajas:,.0f}")
                
        except Exception as e:
            print(f"     - Error al leer archivo: {e}")
    
    print(f"\n🗺️ ARCHIVOS DE MAPAS ENCONTRADOS ({len(archivos_html)}):")
    for archivo in sorted(archivos_html):
        tamaño = os.path.getsize(archivo) / 1024  # KB
        print(f"   • {archivo} ({tamaño:.1f} KB)")
    
    print(f"\n📋 RESUMEN DE ARCHIVOS:")
    print(f"   • Archivos Excel: {len(archivos_excel)}")
    print(f"   • Archivos de mapas: {len(archivos_html)}")
    print(f"   • Total archivos generados: {len(archivos_excel) + len(archivos_html)}")
    
    # Mostrar información del archivo más reciente
    if archivos_excel:
        archivo_reciente = max(archivos_excel, key=os.path.getctime)
        print(f"\n📅 ARCHIVO MÁS RECIENTE: {archivo_reciente}")
        
        try:
            # Mostrar hojas disponibles
            xl_file = pd.ExcelFile(archivo_reciente)
            print(f"   Hojas disponibles:")
            for hoja in xl_file.sheet_names:
                df = pd.read_excel(archivo_reciente, sheet_name=hoja)
                print(f"     - {hoja}: {len(df)} filas")
        except Exception as e:
            print(f"   Error al leer archivo: {e}")

def mostrar_ejemplo_datos(archivo_excel):
    """Muestra un ejemplo de los datos en el archivo Excel"""
    print(f"\n" + "="*60)
    print(f"EJEMPLO DE DATOS EN {archivo_excel}")
    print("="*60)
    
    try:
        # Leer resumen de clientes
        df_clientes = pd.read_excel(archivo_excel, sheet_name='Resumen_Clientes_Semana')
        
        print(f"\n📊 RESUMEN POR CLIENTE (primeros 10):")
        print(df_clientes.head(10).to_string(index=False))
        
        # Leer resumen semanal
        df_resumen = pd.read_excel(archivo_excel, sheet_name='Resumen Semanal')
        
        print(f"\n📅 RESUMEN SEMANAL:")
        print(df_resumen.to_string(index=False))
        
        # Estadísticas generales
        print(f"\n📈 ESTADÍSTICAS GENERALES:")
        print(f"   • Total clientes únicos: {len(df_clientes)}")
        print(f"   • Total cajas a distribuir: {df_clientes['Total Cajas Equivalentes'].sum():,.0f}")
        print(f"   • Promedio cajas por cliente: {df_clientes['Total Cajas Equivalentes'].mean():,.0f}")
        print(f"   • Cliente con más cajas: {df_clientes.loc[df_clientes['Total Cajas Equivalentes'].idxmax(), 'Cliente']}")
        print(f"   • Máximo cajas por cliente: {df_clientes['Total Cajas Equivalentes'].max():,.0f}")
        
    except Exception as e:
        print(f"Error al leer archivo: {e}")

if __name__ == "__main__":
    verificar_reportes()
    
    # Buscar el archivo de proyección más reciente
    archivos_proyeccion = [f for f in os.listdir('.') if f.endswith('.xlsx') and 'proyeccion' in f.lower()]
    
    if archivos_proyeccion:
        archivo_reciente = max(archivos_proyeccion, key=os.path.getctime)
        mostrar_ejemplo_datos(archivo_reciente)
        
        print(f"\n💡 INSTRUCCIONES:")
        print(f"   1. Abre el archivo '{archivo_reciente}' en Excel")
        print(f"   2. Revisa la hoja 'Resumen_Clientes_Semana' para ver el total por cliente")
        print(f"   3. Revisa las hojas 'Clientes_[Día]' para ver clientes agrupados por día")
        print(f"   4. Abre los archivos HTML para ver los mapas interactivos")
    else:
        print(f"\n❌ No se encontraron archivos de proyección. Ejecuta primero el análisis.")
