import os
import shutil
from datetime import datetime
import pandas as pd

class OrganizadorArchivos:
    def __init__(self, carpeta_base="Reportes"):
        """
        Inicializa el organizador de archivos
        
        Args:
            carpeta_base (str): Nombre de la carpeta base para los reportes
        """
        self.carpeta_base = carpeta_base
        self.carpeta_actual = None
        self.archivos_generados = []
        
    def crear_carpeta_reporte(self, centro=None, tipo_analisis="normal"):
        """
        Crea una carpeta para el reporte actual con nombre automático
        
        Args:
            centro (str): Nombre del centro analizado
            tipo_analisis (str): Tipo de análisis ('normal' o 'proyeccion')
        """
        # Crear timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear nombre de carpeta
        if centro:
            nombre_carpeta = f"{centro}_{tipo_analisis}_{timestamp}"
        else:
            nombre_carpeta = f"analisis_{tipo_analisis}_{timestamp}"
        
        # Crear ruta completa
        self.carpeta_actual = os.path.join(self.carpeta_base, nombre_carpeta)
        
        # Crear carpetas si no existen
        os.makedirs(self.carpeta_actual, exist_ok=True)
        
        # Crear subcarpetas
        subcarpetas = ['Mapas', 'Reportes_Excel', 'Datos_Originales']
        for subcarpeta in subcarpetas:
            os.makedirs(os.path.join(self.carpeta_actual, subcarpeta), exist_ok=True)
        
        print(f"📁 Carpeta creada: {self.carpeta_actual}")
        return self.carpeta_actual
    
    def mover_archivo(self, archivo_origen, tipo="excel"):
        """
        Mueve un archivo a la carpeta correspondiente
        
        Args:
            archivo_origen (str): Ruta del archivo original
            tipo (str): Tipo de archivo ('excel', 'mapa', 'datos')
        """
        if not os.path.exists(archivo_origen):
            print(f"⚠️  Archivo no encontrado: {archivo_origen}")
            return None
        
        # Determinar subcarpeta según el tipo
        if tipo == "excel":
            subcarpeta = "Reportes_Excel"
        elif tipo == "mapa":
            subcarpeta = "Mapas"
        elif tipo == "datos":
            subcarpeta = "Datos_Originales"
        else:
            subcarpeta = ""
        
        # Crear ruta de destino
        nombre_archivo = os.path.basename(archivo_origen)
        if subcarpeta:
            archivo_destino = os.path.join(self.carpeta_actual, subcarpeta, nombre_archivo)
        else:
            archivo_destino = os.path.join(self.carpeta_actual, nombre_archivo)
        
        # Mover archivo
        try:
            shutil.move(archivo_origen, archivo_destino)
            self.archivos_generados.append({
                'tipo': tipo,
                'archivo': archivo_destino,
                'nombre': nombre_archivo
            })
            print(f"✅ Archivo movido: {nombre_archivo}")
            return archivo_destino
        except Exception as e:
            print(f"❌ Error al mover archivo {archivo_origen}: {e}")
            return None
    
    def generar_reporte_resumen(self):
        """
        Genera un reporte resumen de todos los archivos creados
        """
        if not self.archivos_generados:
            return
        
        # Crear DataFrame con información de archivos
        datos_resumen = []
        for archivo_info in self.archivos_generados:
            datos_resumen.append({
                'Tipo': archivo_info['tipo'].upper(),
                'Nombre Archivo': archivo_info['nombre'],
                'Ruta': archivo_info['archivo'],
                'Tamaño (KB)': round(os.path.getsize(archivo_info['archivo']) / 1024, 2)
            })
        
        df_resumen = pd.DataFrame(datos_resumen)
        
        # Guardar resumen
        archivo_resumen = os.path.join(self.carpeta_actual, "RESUMEN_ARCHIVOS_GENERADOS.xlsx")
        df_resumen.to_excel(archivo_resumen, index=False)
        
        print(f"📋 Resumen de archivos guardado: {archivo_resumen}")
        
        # Crear archivo de texto con información
        archivo_info = os.path.join(self.carpeta_actual, "INFORMACION_REPORTE.txt")
        with open(archivo_info, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("REPORTE DE ANÁLISIS DE RUTAS\n")
            f.write("="*60 + "\n\n")
            f.write(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Carpeta del reporte: {self.carpeta_actual}\n\n")
            f.write("ARCHIVOS GENERADOS:\n")
            f.write("-" * 40 + "\n")
            
            for archivo_info in self.archivos_generados:
                f.write(f"• {archivo_info['tipo'].upper()}: {archivo_info['nombre']}\n")
            
            f.write(f"\nTotal de archivos: {len(self.archivos_generados)}\n")
        
        print(f"📝 Información del reporte guardada: {archivo_info}")
    
    def obtener_ruta_archivo(self, nombre_archivo, tipo="excel"):
        """
        Obtiene la ruta completa donde se debe guardar un archivo
        
        Args:
            nombre_archivo (str): Nombre del archivo
            tipo (str): Tipo de archivo
        """
        if tipo == "excel":
            subcarpeta = "Reportes_Excel"
        elif tipo == "mapa":
            subcarpeta = "Mapas"
        elif tipo == "datos":
            subcarpeta = "Datos_Originales"
        else:
            subcarpeta = ""
        
        if subcarpeta:
            return os.path.join(self.carpeta_actual, subcarpeta, nombre_archivo)
        else:
            return os.path.join(self.carpeta_actual, nombre_archivo)
    
    def limpiar_archivos_temporales(self):
        """
        Limpia archivos temporales que puedan haber quedado en el directorio principal
        """
        archivos_temporales = [
            "reporte_rutas.xlsx",
            "reporte_rutas_mapa.html",
            "mapa_rutas.html"
        ]
        
        for archivo in archivos_temporales:
            if os.path.exists(archivo):
                try:
                    os.remove(archivo)
                    print(f"🗑️  Archivo temporal eliminado: {archivo}")
                except Exception as e:
                    print(f"⚠️  No se pudo eliminar {archivo}: {e}")
