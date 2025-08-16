#!/usr/bin/env python3
"""
Script para iniciar la aplicación web del Sistema de Análisis de Rutas
"""

import os
import sys
import webbrowser
import time
from threading import Timer

def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas"""
    try:
        import pandas
        import numpy
        import geopy
        import matplotlib
        import folium
        import openpyxl
        import flask
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Falta la dependencia: {e}")
        print("Instale las dependencias con: pip install -r requirements.txt")
        return False

def verificar_archivo_datos():
    """Verifica que el archivo de datos exista"""
    archivo_excel = "Data/REP PLR ESTATUS ENTREGAS v25.xlsx"
    if os.path.exists(archivo_excel):
        print(f"✅ Archivo de datos encontrado: {archivo_excel}")
        return True
    else:
        print(f"❌ No se encontró el archivo de datos: {archivo_excel}")
        print("Asegúrese de que el archivo esté en la carpeta Data/")
        return False

def abrir_navegador():
    """Abre el navegador web automáticamente"""
    time.sleep(2)  # Esperar a que Flask se inicie
    webbrowser.open('http://localhost:5000')

def main():
    """Función principal"""
    print("="*60)
    print("🚀 LOGIROUTE COSTA RICA - SISTEMA DE OPTIMIZACIÓN DE RUTAS")
    print("="*60)
    
    # Verificar dependencias
    if not verificar_dependencias():
        return
    
    # Verificar archivo de datos
    if not verificar_archivo_datos():
        return
    
    print("\n📋 Iniciando aplicación web...")
    print("🌐 La aplicación estará disponible en: http://localhost:5000")
    print("📱 Presione Ctrl+C para detener la aplicación")
    print("\n" + "="*60)
    
    # Programar apertura del navegador
    Timer(3.0, abrir_navegador).start()
    
    # Importar y ejecutar la aplicación Flask
    try:
        from app_web import app
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n🛑 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar la aplicación: {e}")

if __name__ == "__main__":
    main()
