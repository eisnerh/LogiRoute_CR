# Sistema de Análisis de Rutas - Sugeridos de Distribución

Este sistema analiza archivos Excel con datos de entregas y genera sugeridos de rutas optimizadas basándose en volúmenes de cajas equivalentes y ubicaciones geográficas de los clientes.

## 🚀 Características Principales

- **🌐 Interfaz Web Moderna**: Interfaz gráfica web con Flask para una experiencia de usuario superior
- **📁 Organización Automática**: Archivos organizados automáticamente en carpetas con nombres descriptivos
- **🏢 Análisis por Centro**: Permite filtrar y analizar datos por centro de distribución específico
- **🗺️ Optimización de Rutas**: Genera rutas sugeridas basándose en proximidad geográfica y volúmenes
- **📊 Visualización Interactiva**: Crea mapas interactivos con las rutas generadas
- **📋 Reportes Detallados**: Genera reportes en Excel con resúmenes y detalles de cada ruta
- **📅 Proyección Semanal**: Genera proyecciones de rutas para toda la semana laboral
- **🔍 Depuración de Clientes**: Filtra clientes por frecuencia de procesamiento (mantiene clientes frecuentes)
- **👥 Agrupación por Cliente**: Agrupa datos por cliente y ruta de distribución
- **📈 Cálculo de Promedios**: Calcula promedios en lugar de sumatorias para mejor análisis
- **⚙️ Configuración Flexible**: Permite configurar rutas disponibles y parámetros personalizados

## Requisitos

- Python 3.7 o superior
- Dependencias listadas en `requirements.txt`

## Instalación

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verificar archivo de datos**:
   - Asegúrese de que el archivo `REP PLR ESTATUS ENTREGAS v25.xlsx` esté en la carpeta `Data/`
   - El archivo debe contener una hoja llamada "REP PLR"

## 🚀 Uso

### Opción 1: Interfaz Web (Recomendada) 🌐

Ejecute la aplicación web para una experiencia moderna y fácil de usar:

```bash
python iniciar_web.py
```

O directamente:

```bash
python app_web.py
```

**Características de la interfaz web:**
- ✅ Interfaz gráfica moderna y responsiva
- ✅ Progreso en tiempo real del análisis
- ✅ Organización automática de archivos
- ✅ Apertura automática de carpetas de resultados
- ✅ Validación de datos en tiempo real

### Opción 2: Interfaz de Consola

Ejecute el script interactivo que le guiará paso a paso:

```bash
python interfaz_analisis.py
```

Este script le permitirá:
- Seleccionar el centro de distribución a analizar
- Elegir entre análisis normal o proyección semanal
- Configurar el máximo número de clientes por ruta
- Personalizar el nombre de los archivos de salida

### Opción 3: Ejecución Directa

Ejecute el análisis directamente:

```bash
python analisis_rutas.py
```

### Opción 4: Verificar Reportes

Para revisar los archivos generados:

```bash
python verificar_reportes.py
```

## Tipos de Análisis

### Análisis Normal
- Genera rutas optimizadas para un día específico
- Reporte con resumen de rutas y detalles por cliente
- Mapa interactivo con todas las rutas

### Proyección Semanal
- Genera proyecciones para toda la semana (excluyendo fines de semana)
- Considera el día actual y proyecta hacia adelante
- Reportes agrupados por cliente con totales de ruta y viaje
- Mapas separados por día de la semana

## Estructura de Datos Esperada

El archivo Excel debe contener las siguientes columnas (o similares):

- **Centro/Sucursal**: Columna que identifica el centro de distribución
- **Cliente/Nombre**: Nombre o identificador del cliente
- **Cajas Equivalentes**: Volumen de cajas equivalentes a entregar
- **Latitud**: Coordenada de latitud del cliente
- **Longitud**: Coordenada de longitud del cliente

## 📁 Organización de Archivos

### Estructura de Carpetas Automática

El sistema organiza automáticamente todos los archivos generados en una estructura de carpetas:

```
Reportes/
└── [Centro]_[Tipo]_[Timestamp]/
    ├── Mapas/
    │   ├── mapa_rutas.html
    │   └── mapa_proyeccion_*.html
    ├── Reportes_Excel/
    │   ├── reporte_rutas.xlsx
    │   ├── proyeccion_semanal_*.xlsx
    │   └── RESUMEN_ARCHIVOS_GENERADOS.xlsx
    ├── Datos_Originales/
    │   └── (archivos de datos originales)
    ├── RESUMEN_ARCHIVOS_GENERADOS.xlsx
    └── INFORMACION_REPORTE.txt
```

### Archivos Generados

1. **🗺️ Mapas Interactivos**:
   - Mapa con marcadores de clientes agrupados por ruta
   - Marcador rojo para el centro de distribución
   - Control de capas para mostrar/ocultar rutas
   - Mapas separados por día para proyección semanal

2. **📊 Reportes Excel**:
   - **Hoja "Resumen Rutas"**: Estadísticas generales de cada ruta
   - **Hoja "Clientes por Ruta"**: Clientes agrupados por ruta con totales
   - **Hoja "Resumen por Cliente"**: Resumen total por cliente (todas las rutas)
   - **Hoja "Datos Originales"**: Datos filtrados utilizados en el análisis

3. **📅 Reporte de Proyección Semanal**:
   - **Hoja "Resumen Semanal"**: Estadísticas por día de la semana
   - **Hoja "Clientes_[Día]"**: Clientes agrupados por día con totales
   - **Hoja "Resumen_Clientes_Semana"**: Resumen total por cliente (toda la semana)

4. **📋 Archivos de Resumen**:
   - **RESUMEN_ARCHIVOS_GENERADOS.xlsx**: Lista detallada de todos los archivos creados
   - **INFORMACION_REPORTE.txt**: Información general del análisis realizado

## Algoritmo de Optimización

El sistema utiliza un algoritmo de agrupación por proximidad que:

1. **Calcula el centro de gravedad** de todos los clientes
2. **Ordena los clientes** por distancia al centro de gravedad
3. **Agrupa clientes** en rutas respetando el límite máximo de clientes por ruta
4. **Optimiza la distribución** considerando volúmenes de cajas equivalentes

## Parámetros Configurables

- **Máximo clientes por ruta**: Controla el tamaño de cada ruta (default: 15)
- **Centro de distribución**: Permite analizar un centro específico o todos
- **Nombre de archivos**: Personalización de nombres de salida

## Ejemplo de Uso

```
============================================================
ANÁLISIS DE RUTAS - SISTEMA DE SUGERIDOS
============================================================

Cargando datos del archivo Excel...
Datos cargados exitosamente. Filas: 1,250
Columnas disponibles: ['Centro', 'Cliente', 'Cajas_Equiv', 'Latitud', 'Longitud', ...]

==================================================
CENTROS DISPONIBLES
==================================================
1. CENTRO NORTE
2. CENTRO SUR
3. CENTRO ESTE
4. Analizar todos los centros
0. Salir

Seleccione un centro (0-4): 1

==================================================
CONFIGURACIÓN DE PARÁMETROS
==================================================
Máximo número de clientes por ruta (default: 15): 12
Nombre del archivo de reporte (default: reporte_rutas): rutas_norte

==================================================
EJECUTANDO ANÁLISIS
==================================================
Analizando centro: CENTRO NORTE
Datos válidos para análisis: 156 clientes

============================================================
ANÁLISIS DE RUTAS SUGERIDAS
============================================================

Centro de distribución: (19.4326, -99.1332)
Total de clientes analizados: 156
Total de rutas generadas: 13
Total de cajas equivalentes: 45,230

Ruta   Clientes   Cajas Totales    Promedio Cajas
--------------------------------------------------
1      12         3,450            287.5
2      12         3,120            260.0
...
```

## Solución de Problemas

### Error al cargar el archivo Excel
- Verifique que el archivo existe en la carpeta `Data/`
- Asegúrese de que el archivo no esté abierto en Excel
- Verifique que la hoja "REP PLR" existe

### No se encuentran columnas clave
- El sistema busca columnas por patrones de nombres
- Si las columnas tienen nombres muy diferentes, puede que no las identifique
- Revise los nombres de las columnas en el archivo Excel

### Datos faltantes
- El sistema elimina automáticamente filas sin coordenadas o volúmenes
- Verifique la calidad de los datos en el archivo original

## Personalización

Para personalizar el análisis, puede modificar:

- **Algoritmo de optimización**: Edite la función `_generar_rutas_por_proximidad`
- **Criterios de agrupación**: Modifique los parámetros en `generar_sugerido_rutas`
- **Visualización**: Personalice el mapa en `generar_mapa`

## Soporte

Para reportar problemas o solicitar mejoras, revise:
1. Los mensajes de error en la consola
2. La estructura de datos del archivo Excel
3. Los parámetros de configuración utilizados
