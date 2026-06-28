# Dashboard de Exposición por Riesgo Físico en Excel

## Estructura General del Libro de Excel

```
📊 Libro Excel
├── Hoja "Dashboard"      → Tabla resumen con filtros
├── Hoja "Datos"          → Base completa de exposiciones
├── Hoja "Metricas"       → Variables financieras de referencia
└── Hoja "Catalogos"      → Listas para validación de filtros
```

---

## Paso 1: Preparar la Hoja de Datos

### 1.1 Estructura de la tabla base

Tu tabla de datos debe estar en formato "tidy" (un registro por fila):

| clave_mpio | nombre_mpio | fenomeno | escenario | año | nivel_riesgo | industria | saldo_expuesto | activos_totales | capital_reg | utilidad_neta |
|------------|-------------|----------|-----------|-----|--------------|-----------|----------------|-----------------|-------------|---------------|
| 09001 | Azcapotzalco | Ciclón | SSP2-4.5 | 2030 | R1 | Manufactura | 150000 | 5000000 | 800000 | 120000 |

### 1.2 Convertir rango a Tabla de Excel

1. Selecciona todo el rango de datos (incluyendo encabezados)
2. `Ctrl + T` o `Insertar → Tabla`
3. Nombra la tabla como **"TblDatos"**:
   - Con la tabla seleccionada, ve a `Diseño de tabla → Nombre de la tabla`

> **Importante**: Usar tablas estructuradas permite que las fórmulas se actualicen automáticamente al agregar datos.

---

## Paso 2: Crear la Hoja de Catálogos

En una hoja llamada "Catalogos", crea listas únicas:

| Fenomenos | Escenarios | Años | Niveles | Industrias |
|-----------|------------|------|---------|------------|
| Ciclón Tropical | SSP2-4.5 | 2030 | R1 | Manufactura |
| Inundación | SSP5-8.5 | 2050 | R2 | Comercio |
| Sequía | | 2100 | R3 | Servicios |
| Onda de Calor | | | R4 | Agropecuario |

Nombra cada columna como rango:
- Selecciona la columna de fenómenos → `Fórmulas → Definir nombre` → **"Lista_Fenomenos"**
- Repite para las demás listas

---

## Paso 3: Crear la Hoja de Métricas

### 3.1 Tabla de métricas financieras por industria

| industria | activos_totales | capital_regulatorio | utilidad_neta | var_95 |
|-----------|-----------------|---------------------|---------------|--------|
| Manufactura | 50000000 | 8000000 | 1200000 | 3500000 |
| Comercio | 35000000 | 5500000 | 800000 | 2100000 |

Convierte a tabla y nómbrala **"TblMetricas"**

---

## Paso 4: Configurar el Dashboard

### 4.1 Crear celdas de filtro

En la parte superior de la hoja "Dashboard", reserva un área para filtros:

```
┌─────────────────────────────────────────────────┐
│  FILTROS                                        │
│  ┌──────────────────┐  ┌──────────────────────┐ │
│  │ Fenómeno: [▼]    │  │ Métrica base: [▼]    │ │
│  │      B2          │  │        D2            │ │
│  └──────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 4.2 Agregar validación de datos (listas desplegables)

Para la celda **B2** (filtro de fenómeno):
1. Selecciona la celda B2
2. `Datos → Validación de datos`
3. Permitir: **Lista**
4. Origen: `=Lista_Fenomenos` (o selecciona el rango directamente)

Para la celda **D2** (métrica de denominador):
1. Crea una lista con opciones: `Valor Absoluto, % Activos, % Capital, % Utilidad`
2. Aplica validación similar

### 4.3 Nombrar las celdas de filtro

Selecciona B2 → `Fórmulas → Definir nombre` → **"Filtro_Fenomeno"**
Selecciona D2 → `Fórmulas → Definir nombre` → **"Filtro_Metrica"**

---

## Paso 5: Construir la Tabla Dinámica del Dashboard

### 5.1 Estructura de encabezados (fila 5 en adelante)

Construye manualmente los encabezados anidados:

```
Fila 5:  |          | SSP2-4.5                              | SSP5-8.5                              |
Fila 6:  | Industria| 2030        | 2050        | 2100      | 2030        | 2050        | 2100      |
Fila 7:  |          | R1|R2|R3|R4 | R1|R2|R3|R4 | R1|R2|R3|R4| R1|R2|R3|R4 | R1|R2|R3|R4 | R1|R2|R3|R4|
```

Columnas sugeridas:
- A: Industria
- B-E: SSP2-4.5, 2030, R1-R4
- F-I: SSP2-4.5, 2050, R1-R4
- J-M: SSP2-4.5, 2100, R1-R4
- N-Q: SSP5-8.5, 2030, R1-R4
- R-U: SSP5-8.5, 2050, R1-R4
- V-Y: SSP5-8.5, 2100, R1-R4

---

## Paso 6: Fórmulas para Poblar el Dashboard

### 6.1 Fórmula base con SUMAR.SI.CONJUNTO

Para la celda **B8** (primera celda de datos, Industria en A8):

```excel
=SUMAR.SI.CONJUNTO(
    TblDatos[saldo_expuesto],
    TblDatos[fenomeno], Filtro_Fenomeno,
    TblDatos[industria], $A8,
    TblDatos[escenario], B$5,
    TblDatos[año], B$6,
    TblDatos[nivel_riesgo], B$7
)
```

### 6.2 Fórmula con denominador dinámico (para expresar como %)

Crea una fórmula que ajuste el denominador según el filtro de métrica:

```excel
=LET(
    _suma, SUMAR.SI.CONJUNTO(
        TblDatos[saldo_expuesto],
        TblDatos[fenomeno], Filtro_Fenomeno,
        TblDatos[industria], $A8,
        TblDatos[escenario], B$5,
        TblDatos[año], B$6,
        TblDatos[nivel_riesgo], B$7
    ),
    _metrica, Filtro_Metrica,
    _denom, SI(
        _metrica="Valor Absoluto", 1,
        SI(_metrica="% Activos", 
            BUSCARX($A8, TblMetricas[industria], TblMetricas[activos_totales]),
        SI(_metrica="% Capital",
            BUSCARX($A8, TblMetricas[industria], TblMetricas[capital_regulatorio]),
        SI(_metrica="% Utilidad",
            BUSCARX($A8, TblMetricas[industria], TblMetricas[utilidad_neta]),
        1)))
    ),
    _suma / _denom
)
```

**Versión simplificada sin LET** (para Excel más antiguos):

```excel
=SUMAR.SI.CONJUNTO(TblDatos[saldo_expuesto],TblDatos[fenomeno],Filtro_Fenomeno,TblDatos[industria],$A8,TblDatos[escenario],B$5,TblDatos[año],B$6,TblDatos[nivel_riesgo],B$7)
/
SI(Filtro_Metrica="Valor Absoluto",1,
SI(Filtro_Metrica="% Activos",BUSCARX($A8,TblMetricas[industria],TblMetricas[activos_totales]),
SI(Filtro_Metrica="% Capital",BUSCARX($A8,TblMetricas[industria],TblMetricas[capital_regulatorio]),
SI(Filtro_Metrica="% Utilidad",BUSCARX($A8,TblMetricas[industria],TblMetricas[utilidad_neta]),1))))
```

### 6.3 Copiar la fórmula

1. Escribe la fórmula en B8
2. Copia hacia la derecha (hasta la última columna de nivel de riesgo)
3. Copia hacia abajo (para todas las industrias)

> Las referencias mixtas (`$A8`, `B$5`, `B$6`, `B$7`) aseguran que al copiar:
> - La industria se fije por fila
> - El escenario, año y nivel de riesgo se fijen por columna

---

## Paso 7: Formato Condicional (Opcional pero Recomendado)

### 7.1 Escala de colores por concentración

1. Selecciona todas las celdas de datos del dashboard
2. `Inicio → Formato condicional → Escalas de color`
3. Usa una escala de verde (bajo) a rojo (alto)

### 7.2 Resaltar valores críticos

```
Formato condicional → Nueva regla → Usar fórmula:
=B8>0.1  (si >10% se considera concentración alta)
Formato: Relleno rojo
```

---

## Paso 8: Agregar Totales por Escenario/Tiempo

### 8.1 Fila de totales por industria

Debajo de la última industria, agrega una fila "TOTAL":

```excel
=SUMA(B8:B15)  (ajusta el rango según tus industrias)
```

### 8.2 Columna de total por industria

Puedes agregar una columna al final que sume todos los niveles de riesgo:

```excel
=SUMA(B8:Y8)
```

---

## Estructura Final del Dashboard

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  DASHBOARD DE EXPOSICIÓN POR RIESGO FÍSICO                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│  Fenómeno: [Ciclón Tropical ▼]     Expresar como: [% Activos ▼]             │
├──────────────────────────────────────────────────────────────────────────────┤
│           │           SSP2-4.5                │          SSP5-8.5            │
│           │   2030    │   2050    │   2100    │   2030   │   2050  │  2100   │
│ Industria │R1│R2│R3│R4│R1│R2│R3│R4│R1│R2│R3│R4│R1│R2│R3│R4│R1│R2│R3│R4│...  │
├───────────┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼─────┤
│Manufactura│2%│5%│3%│1%│3%│6%│4%│2%│4%│8%│5%│2%│...                          │
│Comercio   │1%│3%│2%│1%│...                                                   │
│Servicios  │...                                                               │
├───────────┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴─────┤
│TOTAL      │  │  │  │  │...                                                   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Tips Adicionales

### Uso de ELEGIR o INDICE para métricas múltiples

Si quieres más flexibilidad con las métricas, puedes crear una tabla de mapeo:

| ID | Nombre_Metrica | Columna_Datos |
|----|----------------|---------------|
| 1 | Valor Absoluto | saldo_expuesto |
| 2 | % Activos | activos_totales |
| 3 | % Capital | capital_regulatorio |

### Proteger el dashboard

1. Desbloquea solo las celdas de filtro (B2, D2)
2. `Revisar → Proteger hoja`
3. Permite solo "Seleccionar celdas desbloqueadas"

### Actualización automática

Si tus datos vienen de una fuente externa:
1. `Datos → Obtener datos → De archivo/base de datos`
2. Configura la actualización automática
3. Las tablas y fórmulas se actualizarán al refrescar

---

## Checklist de Implementación

- [ ] Crear hoja "Datos" con tabla TblDatos
- [ ] Crear hoja "Metricas" con tabla TblMetricas  
- [ ] Crear hoja "Catalogos" con listas nombradas
- [ ] Crear hoja "Dashboard"
- [ ] Configurar celdas de filtro con validación
- [ ] Nombrar celdas de filtro
- [ ] Construir encabezados anidados
- [ ] Escribir fórmula SUMAR.SI.CONJUNTO con referencias mixtas
- [ ] Copiar fórmula a todo el rango
- [ ] Aplicar formato condicional
- [ ] Agregar filas/columnas de totales
- [ ] Probar cambiando filtros
