# Instrumentos de Deuda Gubernamental en México
## Guía Técnica Completa: Características, Valuación, y Factores de Riesgo

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Conceptos Fundamentales](#2-conceptos-fundamentales)
   - [Yield (Rendimiento) vs. Tasa de Interés](#21-yield-rendimiento-vs-tasa-de-interés)
   - [Spread (Diferencial)](#22-spread-diferencial)
   - [Bid-Ask Spread](#23-bid-ask-spread)
   - [Duración](#24-duración)
   - [Convexidad](#25-convexidad)
3. [CETES - Certificados de la Tesorería de la Federación](#3-cetes---certificados-de-la-tesorería-de-la-federación)
4. [Bonos M - Bonos de Desarrollo con Tasa Fija](#4-bonos-m---bonos-de-desarrollo-con-tasa-fija)
5. [Bondes - Bonos de Desarrollo a Tasa Flotante](#5-bondes---bonos-de-desarrollo-a-tasa-flotante)
6. [Udibonos - Bonos Indexados a la Inflación](#6-udibonos---bonos-indexados-a-la-inflación)
7. [Tabla Comparativa de Instrumentos](#7-tabla-comparativa-de-instrumentos)
8. [Factores de Riesgo](#8-factores-de-riesgo)
9. [Mercados Financieros en México](#9-mercados-financieros-en-méxico)
   - [Mercado de Dinero](#91-mercado-de-dinero)
   - [Mercado de Capitales](#92-mercado-de-capitales)
   - [Mercado Cambiario](#93-mercado-cambiario)
   - [Mercado de Derivados](#94-mercado-de-derivados)
10. [Clasificación Integral de Riesgos Financieros](#10-clasificación-integral-de-riesgos-financieros)
11. [Administración de Riesgos en Instituciones Financieras](#11-administración-de-riesgos-en-instituciones-financieras)
    - [Estructura Organizacional](#111-estructura-organizacional)
    - [Gestión del Riesgo de Mercado](#112-gestión-del-riesgo-de-mercado)
    - [Gestión del Riesgo de Crédito](#113-gestión-del-riesgo-de-crédito)
    - [Gestión del Riesgo de Liquidez](#114-gestión-del-riesgo-de-liquidez)
    - [Gestión del Riesgo Operacional](#115-gestión-del-riesgo-operacional)
    - [Marco Regulatorio](#116-marco-regulatorio)
12. [Referencias Oficiales](#12-referencias-oficiales)

---

## 1. Introducción

El Gobierno Federal de México emite y coloca actualmente **cuatro instrumentos principales** en el mercado de deuda local:

1. **CETES** (Certificados de la Tesorería de la Federación)
2. **Bonos M** (Bonos de Desarrollo del Gobierno Federal con Tasa de Interés Fija)
3. **Bondes** (Bonos de Desarrollo del Gobierno Federal - Tasa Flotante)
4. **Udibonos** (Bonos de Desarrollo del Gobierno Federal denominados en Unidades de Inversión)

Adicionalmente, el **Instituto para la Protección al Ahorro Bancario (IPAB)** coloca los Bonos de Protección al Ahorro (BPAs), que cuentan con garantía de crédito del Gobierno Federal.

**Banco de México** funge como agente financiero en la colocación de estos valores, tanto del Gobierno Federal como del IPAB.

> **Fuente oficial**: Toda la información técnica y fórmulas presentadas en este documento provienen de las **Descripciones Técnicas** publicadas por Banco de México en su sitio web oficial.

---

## 2. Conceptos Fundamentales

### 2.1 Yield (Rendimiento) vs. Tasa de Interés

#### Definiciones

| Concepto | Definición |
|----------|------------|
| **Tasa de Cupón** | Tasa de interés anual que el bono paga sobre su **valor nominal**, fijada al momento de la emisión. Permanece constante durante toda la vida del instrumento. |
| **Yield (Rendimiento al Vencimiento / YTM)** | Tasa de rendimiento total que un inversionista obtendría si mantiene el bono hasta su vencimiento, considerando: cupones, precio de compra, valor nominal, y el tiempo restante. |

#### Diferencia Clave

- La **tasa de cupón** se calcula sobre el valor nominal y es fija.
- El **yield** se calcula sobre el **precio de mercado** actual e incluye la ganancia o pérdida de capital.

#### Relación entre Precio y Yield

| Condición | Relación Precio-Valor Nominal | Relación Yield-Cupón |
|-----------|------------------------------|----------------------|
| A la par | Precio = Valor Nominal | Yield = Tasa Cupón |
| Con descuento | Precio < Valor Nominal | Yield > Tasa Cupón |
| Con prima | Precio > Valor Nominal | Yield < Tasa Cupón |

#### Ejemplo Conceptual

Un bono con valor nominal de $100 y cupón del 5%:
- Si se compra a $98: el yield será **mayor** al 5% (se paga menos pero se recibe lo mismo)
- Si se compra a $102: el yield será **menor** al 5% (se paga más pero se recibe lo mismo)

---

### 2.2 Spread (Diferencial)

El **spread** es la diferencia entre dos valores relacionados. En el contexto de renta fija, puede referirse a:

#### Tipos de Spread

| Tipo | Definición | Ejemplo |
|------|------------|---------|
| **Spread de Crédito** | Diferencial de rendimiento entre un bono corporativo/soberano y un bono libre de riesgo del mismo plazo | Bono México 10 años vs Bono Alemania 10 años |
| **Spread de Curva** | Diferencial entre rendimientos de bonos de diferentes plazos del mismo emisor | Bono 10 años - Bono 2 años |
| **Sobretasa** | Prima adicional sobre una tasa de referencia que compensa por riesgo o iliquidez | TIIE + 0.10% en Bondes F |

#### Interpretación del Spread

- **Spread amplio**: Mayor riesgo percibido o menor liquidez
- **Spread estrecho**: Menor riesgo percibido o mayor liquidez

> **Nota**: En el mercado mexicano, los **Bondes** utilizan el concepto de "sobretasa" (spread) para su valuación, que representa la prima sobre la tasa de referencia.

---

### 2.3 Bid-Ask Spread (Diferencial Compra-Venta)

#### Definición

El **Bid-Ask Spread** es la diferencia entre:
- **Bid (Precio de compra)**: Precio al que un comprador está dispuesto a adquirir el activo
- **Ask/Offer (Precio de venta)**: Precio al que un vendedor está dispuesto a vender el activo

#### Fórmula

```
Bid-Ask Spread = Precio Ask - Precio Bid
```

#### Características

| Factor | Impacto en Spread |
|--------|-------------------|
| **Alta liquidez** | Spread estrecho (bajo) |
| **Baja liquidez** | Spread amplio (alto) |
| **Alta volatilidad** | Spread amplio |
| **Mayor volumen negociado** | Spread estrecho |

#### Importancia

- Representa el **costo implícito de transacción** para el inversionista
- Es la **ganancia del creador de mercado** (market maker)
- Sirve como **indicador de liquidez** del instrumento

#### Ejemplo

Si el Bono M a 10 años tiene:
- Precio Bid: $98.50
- Precio Ask: $98.55

El Bid-Ask Spread = $0.05 (o 5 centavos por título)

---

### 2.4 Duración

#### Definición

La **duración** mide la **sensibilidad del precio de un bono ante cambios en las tasas de interés**. Es el cambio porcentual aproximado en el precio del bono por cada cambio de 1% en las tasas de interés.

> **Nota importante**: La duración NO es simplemente el plazo del bono, sino una medida de riesgo de tasa de interés.

#### Tipos de Duración

| Tipo | Descripción | Unidad |
|------|-------------|--------|
| **Duración de Macaulay** | Promedio ponderado del tiempo hasta recibir cada flujo de efectivo, donde los pesos son los valores presentes de cada flujo | Años |
| **Duración Modificada** | Derivada de Macaulay; mide directamente la sensibilidad del precio a cambios en tasas | Porcentaje |

#### Fórmula de Duración de Macaulay

```
         K
        Σ  t_j × VP(FC_j)
       j=1
D_Mac = ───────────────────
              P
```

Donde:
- **t_j** = Tiempo hasta el flujo de efectivo j (en años)
- **VP(FC_j)** = Valor presente del flujo de efectivo j
- **P** = Precio del bono
- **K** = Número total de flujos de efectivo

#### Fórmula de Duración Modificada

```
              D_Mac
D_Mod = ─────────────────
         (1 + r/m)
```

Donde:
- **r** = Yield del bono
- **m** = Número de pagos de cupón por año

#### Interpretación Práctica

**Regla del 1%**: Por cada 1% de cambio en las tasas de interés, el precio del bono cambia aproximadamente en un porcentaje igual a su duración modificada.

| Duración | Cambio en tasas +1% | Cambio en precio |
|----------|---------------------|------------------|
| 3 años | +1% | ≈ -3% |
| 10 años | +1% | ≈ -10% |
| 20 años | +1% | ≈ -20% |

#### Factores que Afectan la Duración

| Factor | Efecto en Duración |
|--------|-------------------|
| Mayor plazo | Mayor duración |
| Mayor tasa cupón | Menor duración |
| Mayor yield | Menor duración |
| Cupón cero (como CETES) | Duración = Plazo |

---

### 2.5 Convexidad

#### Definición

La **convexidad** mide **cómo cambia la duración** (la sensibilidad del precio) cuando las tasas de interés cambian. Es la **curvatura** de la relación precio-rendimiento.

> La duración proporciona una aproximación **lineal** del cambio en precio, mientras que la convexidad captura el efecto **no lineal** (cuadrático).

#### ¿Por qué es importante?

La duración por sí sola es precisa solo para cambios pequeños en tasas. Para cambios grandes, se requiere el ajuste por convexidad:

```
ΔP/P ≈ -D_Mod × Δr + ½ × Convexidad × (Δr)²
```

Donde:
- **ΔP/P** = Cambio porcentual en el precio
- **D_Mod** = Duración modificada
- **Δr** = Cambio en el rendimiento (en decimales)

#### Interpretación

| Convexidad | Significado | Implicación |
|------------|-------------|-------------|
| **Positiva** | La curva precio-rendimiento es convexa hacia arriba | Cuando tasas bajan, el precio sube más de lo que la duración predice; cuando suben, el precio baja menos |
| **Alta** | Mayor curvatura | Beneficia al tenedor en ambos escenarios (mayor ganancia si tasas bajan, menor pérdida si suben) |
| **Baja** | Menor curvatura | Menor protección ante movimientos grandes de tasas |

#### Ejemplo Numérico

Para un bono con:
- Duración Modificada = 5 años
- Convexidad = 30

Si las tasas suben 2% (Δr = 0.02):

```
ΔP/P ≈ -5 × 0.02 + ½ × 30 × (0.02)²
     ≈ -0.10 + 0.006
     ≈ -9.4%
```

Sin el ajuste de convexidad, se habría estimado una caída de -10%.

---

## 3. CETES - Certificados de la Tesorería de la Federación

### 3.1 Características Generales

| Característica | Descripción |
|----------------|-------------|
| **Nombre** | Certificados de la Tesorería de la Federación (CETES) |
| **Primera emisión** | Enero de 1978 |
| **Valor nominal** | $10 pesos |
| **Plazos** | 28, 91, 182, 364 y hasta 728 días |
| **Tipo** | Bono cupón cero |
| **Pago de intereses** | No paga intereses explícitos; se colocan a descuento |
| **Colocación** | Mediante subastas semanales |
| **Fungibilidad** | Fungibles entre sí si vencen en la misma fecha |
| **Identificación** | Clave de 8 caracteres: "BI" + fecha de vencimiento (AAMMDD) |

### 3.2 Metodología de Valuación Oficial (Banxico)

#### Fórmula a partir de la Tasa de Rendimiento

```
              VN
P = ─────────────────────
     1 + (r × t / 360)
```

Donde:
- **P** = Precio del CETE (redondeado a 7 decimales)
- **VN** = Valor nominal del título en pesos ($10)
- **r** = Tasa de rendimiento (en decimales)
- **t** = Plazo en días del CETE

#### Relación entre Tasa de Rendimiento y Tasa de Descuento

Para convertir la tasa de rendimiento (**r**) a tasa de descuento (**b**):

```
              r
b = ─────────────────────
     1 + (r × t / 360)
```

Para convertir la tasa de descuento (**b**) a tasa de rendimiento (**r**):

```
              b
r = ─────────────────────
     1 - (b × t / 360)
```

#### Fórmula a partir de la Tasa de Descuento

```
P = VN × [1 - (b × t / 360)]
```

### 3.3 Ejemplo Práctico (Fuente: Banxico)

**Datos:**
- Valor Nominal: $10.00 pesos
- Fecha de Colocación: 31 de agosto de 2000
- Fecha de Vencimiento: 28 de septiembre de 2000
- Plazo: 28 días
- Rendimiento anual: 15.50%

**Cálculo del precio a partir del rendimiento:**

```
P = 10 / [1 + (0.1550 × 28 / 360)]
P = 10 / 1.01205555556
P = $9.8808805
```

**Cálculo de la tasa de descuento equivalente:**

```
b = 0.1550 / 1.01205555556
b = 0.1532 = 15.32%
```

### 3.4 Factores de Riesgo Específicos

| Riesgo | Descripción | Nivel |
|--------|-------------|-------|
| **Riesgo de tasa de interés** | Por su corto plazo, el riesgo de precio es limitado | Bajo |
| **Riesgo de reinversión** | Riesgo de reinvertir a tasas menores al vencimiento | Medio |
| **Riesgo de crédito** | Respaldados por el Gobierno Federal | Muy bajo |
| **Riesgo de liquidez** | Mercado secundario muy líquido | Muy bajo |

---

## 4. Bonos M - Bonos de Desarrollo con Tasa Fija

### 4.1 Características Generales

| Característica | Descripción |
|----------------|-------------|
| **Nombre** | Bonos de Desarrollo del Gobierno Federal con Tasa de Interés Fija (BONOS) |
| **Primera emisión** | Enero de 2000 |
| **Valor nominal** | $100 pesos |
| **Plazos** | 3, 5, 10, 20 y 30 años (múltiplos de 182 días) |
| **Período de interés** | Cada 182 días (semestral) |
| **Tasa de interés** | Fija, determinada en la emisión |
| **Colocación** | Subasta a precio único |
| **Fungibilidad** | No fungibles (cada emisión tiene tasa diferente) |
| **Identificación** | "M " + fecha de vencimiento (AAMMDD) |
| **Segregación** | Susceptibles de segregarse en cupones y principal |

### 4.2 Metodología de Valuación Oficial (Banxico)

#### Fórmula General

```
        K                           1
P = [ Σ C_j × F_j ] + F_K × VN - C × ─────────
       j=1                         N₁^(d)
```

Donde:
- **P** = Precio limpio del BONO (redondeado a 5 decimales)
- **VN** = Valor nominal del título ($100)
- **K** = Número de cupones por liquidar, incluyendo el vigente
- **d** = Número de días transcurridos del cupón vigente
- **N_j** = Plazo en días del cupón j

#### Cálculo del Cupón

```
C_j = VN × TC × N_j / 360
```

Donde:
- **TC** = Tasa de interés anual del cupón (fija)

#### Factor de Descuento

```
F_j = 1 / [1 + (r_j × N_j / 360)]^[(N_j - d) / N_j]
```

Donde:
- **r_j** = Tasa de interés relevante para descontar el cupón j

### 4.3 Valuación mediante Rendimiento al Vencimiento (YTM)

Cuando se conoce el rendimiento al vencimiento, la fórmula se simplifica (asumiendo cupones de igual plazo):

```
           C        1 - (1 + R)^(-K)        VN              C
P = ───────────── × ──────────────── + ─────────── - ─────────────
     1 + R^(d/182)         R           (1 + R)^K     1 + R^(d/182)
```

Donde:
- **R** = r × 182 / 360 (rendimiento ajustado al período de cupón)
- **C** = VN × TC × 182 / 360 (cupón periódico)

### 4.4 Cálculo de Intereses Devengados

```
I_dev = VN × d × TC / 360
```

Donde:
- **d** = Días transcurridos desde el último pago de cupón

**Precio Sucio = Precio Limpio + Intereses Devengados**

### 4.5 Ejemplo Práctico (Fuente: Banxico)

**Datos del bono:**
- Valor Nominal: $100 pesos
- Tasa Cupón: 18% anual
- Plazo del cupón: 182 días
- Días transcurridos del primer cupón: 21
- Rendimiento al vencimiento esperado: 19%

**Cálculo:**

```
R = 0.19 × 182 / 360 = 0.09605

C = 100 × 0.18 × 182 / 360 = $9.10

P = [9.1 × (1 - (1.09605)^(-6)) / 0.09605 + 100 / (1.09605)^6] / (1.09605)^(21/182) - 9.1
P = $97.76269 (precio limpio)

Intereses devengados = 100 × 21 × 0.18 / 360 = $1.05

Precio Sucio = 97.76269 + 1.05 = $98.81269
```

### 4.6 Factores de Riesgo Específicos

| Riesgo | Descripción | Nivel |
|--------|-------------|-------|
| **Riesgo de tasa de interés** | Alta sensibilidad por plazos largos y tasa fija | Alto |
| **Duración** | Aumenta significativamente con el plazo | Variable |
| **Riesgo de reinversión** | Riesgo de reinvertir cupones a tasas menores | Medio |
| **Riesgo de crédito** | Respaldados por el Gobierno Federal | Muy bajo |
| **Riesgo de liquidez** | Alta liquidez, especialmente en plazos de 10 y 20 años | Bajo |

---

## 5. Bondes - Bonos de Desarrollo a Tasa Flotante

### 5.1 Variantes Actuales

| Instrumento | Tasa de Referencia | Pago de Interés | Primera Emisión |
|-------------|-------------------|-----------------|-----------------|
| **Bondes D** | Tasa ponderada de fondeo bancario | Cada 28 días | Agosto 2006 |
| **Bondes F** | TIIE de Fondeo a un día | Cada 28 días | Julio 2021 |
| **Bondes G** | TIIE de Fondeo a un día (criterios ESG) | Cada 28 días | 2021 |

### 5.2 Características Generales (Bondes D)

| Característica | Descripción |
|----------------|-------------|
| **Nombre** | Bonos de Desarrollo del Gobierno Federal (BONDES D) |
| **Valor nominal** | $100 pesos |
| **Plazos** | 1 a 7 años (múltiplos de 28 días) |
| **Período de interés** | Cada 28 días |
| **Tasa de interés** | Flotante, basada en tasa de fondeo bancario |
| **Colocación** | Subasta a precio múltiple |
| **Fungibilidad** | Fungibles si vencen en la misma fecha |
| **Identificación** | "LD" + fecha de vencimiento (AAMMDD) |

### 5.3 Metodología de Valuación Oficial (Banxico)

#### Cálculo de la Tasa de Interés del Cupón

La tasa de cada cupón se calcula mediante composición diaria de la tasa de fondeo:

```
        ⎡  N_j         ⎤
        ⎢  Π  (1 + r_i/36000)  ⎥ - 1
        ⎣ i=1          ⎦
TC_j = ────────────────────────────── × 36000
                   N_j
```

Donde:
- **TC_j** = Tasa de interés anual del cupón j (porcentaje, 2 decimales)
- **N_j** = Plazo en días del cupón j
- **r_i** = Tasa ponderada de fondeo bancario del día i

#### Fórmula General de Precio

```
        K
P = [ Σ C_j × F_j ] + F_K × VN - I_dev
       j=1
```

Donde:
- **P** = Precio limpio (redondeado a 5 decimales)
- **I_dev** = Intereses devengados del cupón vigente

#### Cálculo del Cupón

```
C_j = VN × TC_j × N_j / 36000
```

Para cupones futuros (j = 2, 3, ..., K), se usa un cupón estimado:

```
C = VN × TC × 28 / 36000
```

Donde **TC** es la tasa esperada basada en la última tasa de fondeo conocida.

#### Factor de Descuento con Sobretasa

```
F_j = 1 / (1 + R_j)^[(N_j - d) / N_j]
```

Donde:

```
R_j = [1 + (r + s) × N_j / 36000] - 1
```

- **r** = Tasa de fondeo bancario del día hábil anterior
- **s** = Sobretasa (spread)

### 5.4 Fórmula Simplificada con Sobretasa

Asumiendo parámetros constantes:

```
           C₁        1 - (1 + R)^(-(K-1))        VN
P = ────────────── + C × ─────────────────── + ─────────── - I_dev
     (1 + R)^(d/28)    R × (1 + R)^(d/28)      (1 + R)^K
```

Donde:

```
R = [1 + (r + s) / 36000]^28 - 1
```

### 5.5 Ejemplo de Cálculo de Intereses (Fuente: Banxico)

**Datos:**
- Período: 27 de julio al 23 de agosto de 2006 (28 días)
- Tasas de fondeo diarias observadas: 7.03%, 7.02%, 7.04%, etc.

**Cálculo de TC:**

```
TC = [(1 + 7.03/36000)(1 + 7.02/36000)...(1 + 7.01/36000)]^(1/28) × 36000 - 36000
TC = 7.03%
```

**Intereses del cupón:**

```
Intereses = 100 × 7.03 × 28 / 36000 = $0.5468
```

### 5.6 Factores de Riesgo Específicos

| Riesgo | Descripción | Nivel |
|--------|-------------|-------|
| **Riesgo de tasa de interés** | Bajo, ya que la tasa se ajusta frecuentemente | Bajo |
| **Riesgo de spread (sobretasa)** | Cambios en la sobretasa afectan el precio | Medio |
| **Riesgo de base** | Diferencia entre tasa de referencia y costo de fondeo propio | Bajo |
| **Riesgo de crédito** | Respaldados por el Gobierno Federal | Muy bajo |
| **Duración efectiva** | Cercana al plazo del siguiente cupón (≈28 días) | Muy baja |

---

## 6. Udibonos - Bonos Indexados a la Inflación

### 6.1 Características Generales

| Característica | Descripción |
|----------------|-------------|
| **Nombre** | Bonos de Desarrollo del Gobierno Federal denominados en Unidades de Inversión (UDIBONOS) |
| **Primera emisión** | 1996 |
| **Valor nominal** | 100 UDIS |
| **Plazos** | 3, 5, 10, 20 y 30 años (múltiplos de 182 días) |
| **Período de interés** | Cada 182 días (semestral) |
| **Tasa de interés** | Fija, en términos reales |
| **Moneda** | Denominados en UDIS, pagaderos en pesos |
| **Colocación** | Subasta a precio único |
| **Fungibilidad** | No fungibles (cada emisión tiene tasa diferente) |
| **Identificación** | "S " + fecha de vencimiento (AAMMDD) |
| **Segregación** | Susceptibles de segregarse |

### 6.2 Unidades de Inversión (UDIS)

Las **UDIS** son unidades de cuenta que se actualizan diariamente con base en la inflación (INPC), de conformidad con el procedimiento publicado por Banco de México.

- **Objetivo**: Proteger el poder adquisitivo del capital invertido
- **Actualización**: Diaria, publicada por Banxico

### 6.3 Metodología de Valuación Oficial (Banxico)

#### Fórmula General

```
        K                           1
P = [ Σ C_j × F_j ] + F_K × VN - C × ─────────
       j=1                         N₁^(d)
```

Donde:
- **P** = Precio limpio en UDIS (redondeado a 5 decimales)
- **VN** = Valor nominal en UDIS (100 UDIS)
- **K** = Número de cupones por liquidar
- **d** = Días transcurridos del cupón vigente

#### Cálculo del Cupón

```
C_j = VN × TC × N_j / 360
```

Donde:
- **TC** = Tasa de interés real anual del cupón (fija)
- **N_j** = Plazo en días del cupón j (típicamente 182)

#### Factor de Descuento

```
F_j = 1 / [1 + (r_j × N_j / 360)]^[(N_j - d) / N_j]
```

Donde:
- **r_j** = Tasa de interés real relevante para descontar el cupón j

### 6.4 Valuación mediante Rendimiento Real al Vencimiento

```
           C        1 - (1 + R)^(-K)        VN              C
P = ───────────── × ──────────────── + ─────────── - ─────────────
     1 + R^(d/182)         R           (1 + R)^K     1 + R^(d/182)
```

Donde:
- **R** = r × 182 / 360 (rendimiento real ajustado al período)
- **C** = VN × TC × 182 / 360

### 6.5 Conversión a Moneda Nacional

Para liquidación, pagos y amortización:

```
Monto en Pesos = Monto en UDIS × Valor UDI vigente
```

El **valor de la UDI** se publica diariamente por Banco de México.

### 6.6 Ejemplo Práctico (Fuente: Banxico)

**Datos del bono:**
- Valor Nominal: 100 UDIS
- Tasa Cupón: 8% anual (real)
- Plazo del cupón: 182 días
- Días transcurridos: 21
- Rendimiento real esperado: 8.25%

**Cálculo:**

```
R = 0.0825 × 182 / 360 = 0.04170

C = 100 × 0.08 × 182 / 360 = 4.04444 UDIS

P = [4.04444 × (1 - (1.04170)^(-20)) / 0.04170 + 100 / (1.04170)^20] / (1.04170)^(21/182) - ...
P = 98.30596 UDIS (precio limpio)

Intereses devengados = 100 × 21 × 0.08 / 360 = 0.4667 UDIS

Precio Sucio = 98.30596 + 0.4667 = 98.77262 UDIS
```

### 6.7 Factores de Riesgo Específicos

| Riesgo | Descripción | Nivel |
|--------|-------------|-------|
| **Riesgo de tasa real** | Cambios en tasas reales afectan el precio | Alto |
| **Riesgo de inflación** | Protegidos contra inflación por diseño | Muy bajo |
| **Duración** | Similar a bonos de tasa fija del mismo plazo | Alta |
| **Riesgo de crédito** | Respaldados por el Gobierno Federal | Muy bajo |
| **Riesgo de liquidez** | Menor liquidez que Bonos M nominales | Medio |

---

## 7. Tabla Comparativa de Instrumentos

| Característica | CETES | Bonos M | Bondes (F) | Udibonos |
|----------------|-------|---------|------------|----------|
| **Tipo** | Cupón cero | Tasa fija | Tasa flotante | Tasa real fija |
| **Valor Nominal** | $10 | $100 | $100 | 100 UDIS |
| **Plazos típicos** | 28-364 días | 3-30 años | 1-10 años | 3-30 años |
| **Frecuencia de pago** | Al vencimiento | Semestral | Mensual (28 días) | Semestral |
| **Referencia de tasa** | Descuento implícito | Fija desde emisión | TIIE de Fondeo | Fija real |
| **Protección inflación** | No | No | No | Sí |
| **Duración** | = Plazo | Alta | Muy baja | Alta |
| **Riesgo de tasa** | Bajo | Alto | Muy bajo | Medio (real) |
| **Liquidez** | Muy alta | Alta | Media-Alta | Media |
| **Identificación** | BI + AAMMDD | M + AAMMDD | LF + AAMMDD | S + AAMMDD |

---

## 8. Factores de Riesgo

### 8.1 Riesgo de Tasa de Interés

**Definición**: Pérdida potencial por variaciones adversas en las tasas de interés de mercado.

**Impacto por instrumento:**

| Instrumento | Sensibilidad | Explicación |
|-------------|-------------|-------------|
| CETES | Baja | Corto plazo minimiza exposición |
| Bonos M | Alta | Tasa fija + largo plazo = alta duración |
| Bondes | Muy baja | Tasa flotante se ajusta frecuentemente |
| Udibonos | Media | Sensible a tasas reales, no nominales |

**Mitigación**: Diversificación de plazos, uso de instrumentos de tasa flotante.

### 8.2 Riesgo de Crédito (Soberano)

**Definición**: Posibilidad de que el emisor (Gobierno Federal) no cumpla con sus obligaciones de pago.

**Características en México:**
- Calificación soberana determinada por agencias (S&P, Moody's, Fitch, HR Ratings)
- Históricamente bajo para deuda en moneda local
- Afectado por política fiscal, nivel de deuda, y condiciones macroeconómicas

### 8.3 Riesgo de Inflación

**Definición**: Pérdida de poder adquisitivo del rendimiento nominal.

| Instrumento | Exposición | Comentario |
|-------------|-----------|------------|
| CETES | Alta | Rendimiento nominal no ajustado |
| Bonos M | Alta | Cupón y principal en términos nominales |
| Bondes | Alta | Aunque tasa flotante, no indexada a inflación |
| Udibonos | Muy baja | Protegidos por indexación a UDIS |

### 8.4 Riesgo de Liquidez

**Definición**: Dificultad para comprar o vender el instrumento sin afectar significativamente su precio.

**Indicadores:**
- Bid-Ask spread
- Volumen de operación diario
- Profundidad del mercado

**Jerarquía típica de liquidez (mayor a menor):**
1. CETES (corto plazo)
2. Bonos M (especialmente 10 años)
3. Bondes
4. Udibonos

### 8.5 Riesgo de Reinversión

**Definición**: Riesgo de no poder reinvertir los flujos intermedios (cupones) a la misma tasa.

**Impacto:**
- Mayor en instrumentos con cupones frecuentes
- Mayor en entornos de tasas decrecientes
- Los CETES (cupón cero) no tienen este riesgo durante su vida

### 8.6 Riesgo País

**Definición**: Prima adicional exigida por inversionistas extranjeros por invertir en deuda soberana mexicana vs. activos "libres de riesgo".

**Factores:**
- Política monetaria de Banxico
- Situación fiscal
- Condiciones políticas y económicas globales
- Diferencial de tasas con EE.UU.

---

## 9. Mercados Financieros en México

Los mercados financieros en México permiten la intermediación entre oferentes y demandantes de recursos, canalizando el ahorro hacia actividades productivas. El sistema está regulado principalmente por la **Comisión Nacional Bancaria y de Valores (CNBV)**, el **Banco de México** y la **Secretaría de Hacienda y Crédito Público (SHCP)**.

### 9.1 Mercado de Dinero

#### Definición

Es el mercado donde se negocian instrumentos de **corto plazo** (generalmente menos de un año). Sirve para que los participantes cubran sus necesidades de liquidez y financiamiento de capital de trabajo.

#### Características

| Característica | Descripción |
|----------------|-------------|
| **Plazo** | Corto plazo (< 1 año) |
| **Liquidez** | Alta |
| **Riesgo** | Generalmente bajo |
| **Participantes** | Gobierno, bancos, empresas, inversionistas institucionales |

#### Instrumentos del Mercado de Dinero

| Instrumento | Emisor | Características |
|-------------|--------|-----------------|
| **CETES** | Gobierno Federal | Cupón cero, 28-364 días |
| **Papel Comercial** | Empresas privadas | Pagaré a corto plazo |
| **Pagarés Bancarios** | Instituciones de crédito | Rendimiento a descuento o con interés |
| **Certificados Bursátiles CP** | Empresas/Bancos | Corto plazo, mercado bursátil |
| **Aceptaciones Bancarias** | Bancos | Letras de cambio aceptadas |
| **Reportos** | Diversos | Operaciones con pacto de recompra |

#### Riesgos Principales

- Riesgo de tasa de interés de corto plazo
- Riesgo de crédito (dependiendo del emisor)
- Riesgo de reinversión
- Riesgo de liquidez (en instrumentos menos negociados)

---

### 9.2 Mercado de Capitales

#### Definición

Mercado donde se negocian instrumentos de **largo plazo**, tanto de renta fija (deuda) como de renta variable (acciones). Permite financiar proyectos de inversión de largo plazo.

#### Subdivisiones

| Segmento | Instrumentos | Características |
|----------|--------------|-----------------|
| **Renta Fija (Deuda)** | Bonos M, Udibonos, Bondes, Certificados Bursátiles | Pagos predeterminados |
| **Renta Variable (Accionario)** | Acciones, ETFs, Fibras | Rendimiento variable |

#### Infraestructura

| Entidad | Función |
|---------|---------|
| **Bolsa Mexicana de Valores (BMV)** | Principal bolsa de valores de México |
| **Bolsa Institucional de Valores (BIVA)** | Segunda bolsa de valores (desde 2018) |
| **Indeval** | Depósito central de valores |
| **Contraparte Central de Valores** | Compensación y liquidación |

#### Instrumentos de Deuda (Largo Plazo)

| Instrumento | Emisor | Plazo | Características |
|-------------|--------|-------|-----------------|
| **Bonos M** | Gobierno Federal | 3-30 años | Tasa fija |
| **Udibonos** | Gobierno Federal | 3-30 años | Indexados a inflación |
| **Bondes F/G** | Gobierno Federal | 1-10 años | Tasa flotante |
| **Certificados Bursátiles** | Empresas/Bancos/Estados | Variable | Diversos tipos |
| **Obligaciones** | Empresas | Largo plazo | Con o sin garantía |

#### Instrumentos de Renta Variable

| Instrumento | Descripción |
|-------------|-------------|
| **Acciones** | Representan capital de empresas |
| **ETFs** | Fondos que replican índices |
| **Fibras** | Fideicomisos de inversión en bienes raíces |
| **CKDs** | Certificados de Capital de Desarrollo |
| **CerPIs** | Certificados de Proyectos de Inversión |

#### Riesgos Principales

- Riesgo de mercado (variaciones de precios)
- Riesgo de tasa de interés (duración)
- Riesgo de crédito del emisor
- Riesgo de liquidez
- Riesgo cambiario (valores en otras divisas)
- Riesgo de negocio (renta variable)

---

### 9.3 Mercado Cambiario (Divisas)

#### Definición

Mercado donde se negocian las diferentes monedas extranjeras. Es el mercado más líquido del mundo.

#### Características en México

| Aspecto | Descripción |
|---------|-------------|
| **Régimen** | Tipo de cambio flotante (desde 1994) |
| **Principal par** | USD/MXN |
| **Regulador** | Banco de México |
| **Participantes** | Bancos, casas de cambio, empresas, Banxico |

#### Tipos de Operaciones

| Operación | Descripción | Plazo |
|-----------|-------------|-------|
| **Spot** | Liquidación inmediata | T+2 |
| **Forward** | Tipo de cambio pactado para fecha futura | Variable |
| **Swap de divisas** | Intercambio de flujos en diferentes monedas | Variable |

#### Riesgos Principales

- Riesgo cambiario (variaciones en tipo de cambio)
- Riesgo de contraparte
- Riesgo de liquidez
- Riesgo país
- Riesgo de intervención regulatoria

---

### 9.4 Mercado de Derivados

#### Definición

Mercado donde se negocian instrumentos cuyo valor depende ("deriva") del precio de un activo subyacente. Permiten cobertura de riesgos y especulación.

#### Infraestructura en México

| Entidad | Función | Inicio |
|---------|---------|--------|
| **MexDer** | Bolsa Mexicana de Derivados | Diciembre 1998 |
| **Asigna** | Cámara de Compensación | 1998 |

#### Tipos de Mercados

| Mercado | Características | Ejemplos |
|---------|-----------------|----------|
| **Listado (MexDer)** | Contratos estandarizados, cámara de compensación | Futuros, opciones listadas |
| **OTC (Extrabursátil)** | Contratos a la medida, bilateral | Forwards, swaps, opciones OTC |

#### Instrumentos Derivados

| Instrumento | Definición | Uso Principal |
|-------------|------------|---------------|
| **Futuro** | Contrato estandarizado para comprar/vender un activo en fecha futura a precio determinado | Cobertura, especulación |
| **Forward** | Similar al futuro pero OTC (a la medida) | Cobertura personalizada |
| **Opción** | Derecho (no obligación) de comprar (Call) o vender (Put) a un precio determinado | Cobertura, apalancamiento |
| **Swap** | Intercambio de flujos de efectivo entre dos partes | Gestión de tasas/divisas |
| **Warrant** | Opción emitida por una institución, negociada en bolsa | Inversión, cobertura |

#### Subyacentes Disponibles en MexDer

| Categoría | Subyacentes |
|-----------|-------------|
| **Tasas de Interés** | TIIE 28 días, CETES 91 días, Bonos M (10 y 3 años), Swaps TIIE |
| **Divisas** | Dólar estadounidense (DEUA), Euro |
| **Índices** | IPC (Índice de Precios y Cotizaciones) |
| **Acciones** | Acciones de emisoras listadas |

#### Beneficios de los Derivados

- Transferencia de riesgos (cobertura)
- Descubrimiento de precios
- Apalancamiento (con menor capital)
- Diversificación de estrategias
- Acceso a mercados sin poseer el subyacente

#### Riesgos Principales

| Riesgo | Descripción |
|--------|-------------|
| **Riesgo de mercado** | Movimientos adversos en el subyacente |
| **Riesgo de contraparte** | Incumplimiento de la otra parte (principalmente OTC) |
| **Riesgo de base** | Diferencia entre precio del derivado y subyacente |
| **Riesgo de liquidez** | Dificultad para cerrar posiciones |
| **Riesgo operacional** | Errores en valuación, ejecución o documentación |
| **Riesgo de apalancamiento** | Pérdidas amplificadas por el efecto multiplicador |

---

## 10. Clasificación Integral de Riesgos Financieros

Los riesgos financieros se clasifican en dos grandes categorías: **cuantificables** y **no cuantificables**.

### 10.1 Riesgos Cuantificables

Son aquellos susceptibles de medirse mediante modelos matemáticos y estadísticos.

| Tipo de Riesgo | Definición | Factores de Riesgo |
|----------------|------------|-------------------|
| **Riesgo de Mercado** | Pérdida potencial por movimientos adversos en factores de mercado | Tasas de interés, tipos de cambio, precios de acciones, volatilidad |
| **Riesgo de Crédito** | Pérdida potencial por incumplimiento de contrapartes | Probabilidad de incumplimiento, exposición, severidad |
| **Riesgo de Liquidez** | Pérdida por venta forzosa de activos o incapacidad de fondeo | Brechas de liquidez, profundidad de mercado |

### 10.2 Riesgos No Cuantificables (o Difícilmente Cuantificables)

| Tipo de Riesgo | Definición | Ejemplos |
|----------------|------------|----------|
| **Riesgo Operacional** | Pérdida por fallas en procesos, personas, sistemas o eventos externos | Fraude, errores humanos, fallas de sistemas, desastres naturales |
| **Riesgo Legal** | Pérdida por incumplimiento de disposiciones legales | Contratos no ejecutables, multas regulatorias |
| **Riesgo Reputacional** | Pérdida por deterioro de la percepción pública | Noticias negativas, escándalos |
| **Riesgo Tecnológico** | Pérdida por fallas o vulnerabilidades en tecnología | Ciberataques, obsolescencia |
| **Riesgo Estratégico** | Pérdida por decisiones de negocio inadecuadas | Mal posicionamiento, cambios en el entorno |

### 10.3 Matriz de Riesgos por Mercado

| Mercado | Riesgo Mercado | Riesgo Crédito | Riesgo Liquidez | Riesgo Operacional |
|---------|----------------|----------------|-----------------|-------------------|
| **Dinero** | Medio | Bajo-Medio | Bajo | Bajo |
| **Capitales (Deuda)** | Alto | Bajo-Medio | Medio | Medio |
| **Capitales (Acciones)** | Muy Alto | Bajo | Medio | Medio |
| **Cambiario** | Alto | Medio | Bajo | Medio |
| **Derivados** | Muy Alto | Medio-Alto | Medio | Alto |

---

## 11. Administración de Riesgos en Instituciones Financieras

### 11.1 Estructura Organizacional

Las instituciones financieras en México deben contar con una estructura de **Administración Integral de Riesgos (AIR)** conforme a las disposiciones de la CNBV.

#### Órganos de Gobierno

| Órgano | Responsabilidades |
|--------|-------------------|
| **Consejo de Administración** | Aprobar perfil de riesgo, límites de exposición, marco de AIR |
| **Comité de Riesgos** | Supervisar implementación de políticas, revisar límites, aprobar metodologías |
| **Unidad de Administración de Riesgos (UAIR)** | Identificar, medir, vigilar, limitar, controlar e informar los riesgos |
| **Director de Riesgos (CRO)** | Responsable de la función de riesgos, reporta al Comité y Consejo |

#### Principios de la AIR

1. **Independencia**: La UAIR debe ser independiente de las áreas de negocio
2. **Segregación de funciones**: Separación entre originación, riesgos y contabilidad
3. **Límites**: Establecimiento de límites por tipo de riesgo y línea de negocio
4. **Monitoreo continuo**: Vigilancia diaria de exposiciones vs. límites
5. **Revelación**: Información oportuna a órganos de gobierno y reguladores

---

### 11.2 Gestión del Riesgo de Mercado

#### Definición Regulatoria

Es la pérdida potencial por cambios en los factores de riesgo que inciden sobre la valuación de las posiciones: tasas de interés, tipos de cambio, índices de precios, etc.

#### Metodología: Valor en Riesgo (VaR)

El **VaR** es la métrica estándar para medir el riesgo de mercado.

| Parámetro | Descripción | Valores Típicos |
|-----------|-------------|-----------------|
| **Nivel de confianza** | Probabilidad de que la pérdida no exceda el VaR | 95% o 99% |
| **Horizonte temporal** | Período de tenencia de la posición | 1 día, 10 días |
| **Metodología** | Forma de calcular el VaR | Histórico, Paramétrico, Monte Carlo |

#### Fórmula VaR Paramétrico (para un activo)

```
VaR = Valor de la Posición × σ × Z × √t
```

Donde:
- **σ** = Volatilidad del activo
- **Z** = Estadístico Z para el nivel de confianza (1.65 para 95%, 2.33 para 99%)
- **t** = Horizonte temporal en días

#### Herramientas de Gestión

| Herramienta | Descripción | Frecuencia |
|-------------|-------------|------------|
| **Cálculo de VaR** | Estimación de pérdida máxima esperada | Diario |
| **Límites de VaR** | Topes máximos por portafolio/mesa | Continuo |
| **Sensibilidades** | Duración, convexidad, delta, gamma, vega | Diario |
| **Stress Testing** | Escenarios extremos pero plausibles | Mensual/Trimestral |
| **Backtesting** | Validación del modelo VaR vs. P&L real | Diario |
| **Análisis de escenarios** | Impacto de movimientos específicos | Ad hoc |

#### Acciones del Área de Riesgos

1. Monitorear posiciones y exposiciones diariamente
2. Comparar exposiciones contra límites aprobados
3. Escalar excesos de límites
4. Proponer ajustes a límites según condiciones de mercado
5. Validar modelos de valuación
6. Reportar al Comité de Riesgos y reguladores

---

### 11.3 Gestión del Riesgo de Crédito

#### Definición Regulatoria

Es la pérdida potencial por el incumplimiento de pago de un acreditado o contraparte.

#### Componentes del Riesgo de Crédito

| Componente | Sigla | Definición |
|------------|-------|------------|
| **Probabilidad de Incumplimiento** | PD | Probabilidad de que el deudor no pague |
| **Exposición al Incumplimiento** | EAD | Monto expuesto en caso de incumplimiento |
| **Severidad de la Pérdida** | LGD | Porcentaje de la exposición que se pierde |
| **Pérdida Esperada** | PE | PD × EAD × LGD |

#### Metodologías de Medición

| Metodología | Descripción | Uso |
|-------------|-------------|-----|
| **Scoring de crédito** | Modelo estadístico para evaluar probabilidad de pago | Créditos al consumo |
| **Rating interno** | Calificación interna de contrapartes | Créditos comerciales |
| **Modelos de portafolio** | CreditMetrics, CreditRisk+ | Concentración y correlación |
| **Provisiones** | Reservas para pérdidas esperadas | Contabilidad |

#### Herramientas de Gestión

| Herramienta | Descripción |
|-------------|-------------|
| **Límites de concentración** | Por deudor, sector, geografía |
| **Calificación de cartera** | Clasificación por nivel de riesgo |
| **Garantías y colateral** | Mitigantes de riesgo |
| **Covenants** | Condiciones contractuales de vigilancia |
| **Provisiones preventivas** | Reservas regulatorias (metodología CNBV) |
| **Stress testing** | Impacto de escenarios adversos en cartera |

#### Acciones del Área de Riesgos

1. Evaluar y calificar solicitudes de crédito
2. Establecer y monitorear límites de exposición
3. Vigilar la calidad de la cartera (índice de morosidad)
4. Calcular provisiones según metodología CNBV
5. Identificar créditos deteriorados
6. Proponer estrategias de recuperación
7. Reportar al Comité de Riesgos

---

### 11.4 Gestión del Riesgo de Liquidez

#### Definición Regulatoria

Es la pérdida potencial por la venta anticipada o forzosa de activos a descuentos inusuales para hacer frente a obligaciones, o por la incapacidad de renovar pasivos.

#### Tipos de Riesgo de Liquidez

| Tipo | Descripción |
|------|-------------|
| **Liquidez de mercado** | Dificultad para vender activos sin afectar el precio |
| **Liquidez de fondeo** | Incapacidad de obtener recursos para cumplir obligaciones |

#### Métricas Regulatorias (Basilea III / CNBV)

| Métrica | Sigla | Definición | Mínimo |
|---------|-------|------------|--------|
| **Coeficiente de Cobertura de Liquidez** | CCL/LCR | Activos líquidos / Salidas netas a 30 días | 100% |
| **Coeficiente de Financiamiento Estable Neto** | CFEN/NSFR | Financiamiento estable disponible / requerido | 100% |

#### Herramientas de Gestión

| Herramienta | Descripción |
|-------------|-------------|
| **Análisis de brechas (gap)** | Diferencia entre activos y pasivos por plazo |
| **Proyección de flujos** | Estimación de entradas y salidas de efectivo |
| **Activos líquidos de alta calidad** | Reserva de activos fácilmente convertibles |
| **Líneas de crédito contingente** | Acceso a fondeo de emergencia |
| **Plan de Financiamiento de Contingencia** | Acciones ante escenarios de estrés |
| **Diversificación de fuentes** | Evitar dependencia de pocas fuentes de fondeo |

#### Acciones del Área de Riesgos

1. Monitorear indicadores de liquidez (CCL, CFEN)
2. Realizar análisis de brechas de liquidez
3. Coordinar con Tesorería la gestión de flujos
4. Diseñar y actualizar el Plan de Financiamiento de Contingencia
5. Realizar pruebas de estrés de liquidez
6. Reportar al Comité de Riesgos y reguladores

---

### 11.5 Gestión del Riesgo Operacional

#### Definición Regulatoria

Es la pérdida potencial por fallas o deficiencias en los controles internos, errores en el procesamiento de operaciones, fallas en sistemas, eventos externos, o conducta inapropiada del personal.

#### Categorías de Eventos de Pérdida (Basilea II)

| Categoría | Ejemplos |
|-----------|----------|
| **Fraude interno** | Robo por empleados, manipulación de información |
| **Fraude externo** | Robo, falsificación, ataques cibernéticos |
| **Relaciones laborales** | Discriminación, seguridad laboral |
| **Clientes, productos y prácticas** | Abuso de información, venta inadecuada |
| **Daños a activos físicos** | Desastres naturales, vandalismo |
| **Fallas en sistemas** | Caídas de sistemas, errores de software |
| **Ejecución y administración de procesos** | Errores de captura, documentación incompleta |

#### Metodologías de Medición (Capital Regulatorio)

| Método | Descripción | Sofisticación |
|--------|-------------|---------------|
| **Indicador Básico (BIA)** | Capital = 15% × Ingreso bruto promedio | Básico |
| **Estándar (SA)** | Capital por línea de negocio × factores | Intermedio |
| **Medición Avanzada (AMA)** | Modelos internos con datos de pérdida | Avanzado |

#### Herramientas de Gestión

| Herramienta | Descripción |
|-------------|-------------|
| **Autoevaluación de riesgos y controles (RCSA)** | Identificación y evaluación de riesgos por proceso |
| **Base de datos de eventos de pérdida** | Registro histórico de pérdidas operacionales |
| **Indicadores clave de riesgo (KRIs)** | Métricas de alerta temprana |
| **Plan de Continuidad de Negocio (BCP)** | Procedimientos para operar ante disrupciones |
| **Auditoría interna** | Revisión independiente de controles |
| **Capacitación** | Formación en gestión de riesgos |

#### Acciones del Área de Riesgos

1. Identificar y documentar riesgos operacionales
2. Evaluar controles existentes
3. Registrar eventos de pérdida
4. Monitorear indicadores clave de riesgo (KRIs)
5. Coordinar planes de continuidad
6. Promover cultura de riesgo operacional
7. Reportar al Comité de Riesgos

---

### 11.6 Marco Regulatorio

#### Principales Reguladores

| Regulador | Ámbito |
|-----------|--------|
| **SHCP** | Política financiera, normatividad general |
| **CNBV** | Supervisión de bancos, casas de bolsa, Afores |
| **Banxico** | Política monetaria, sistema de pagos, estabilidad financiera |
| **CONSAR** | Supervisión de Afores y Siefores |
| **CNSF** | Supervisión de aseguradoras y afianzadoras |

#### Normatividad Aplicable

| Disposición | Contenido |
|-------------|-----------|
| **Disposiciones de Carácter General Aplicables a las Instituciones de Crédito (CUB)** | Reglas para bancos: capitalización, liquidez, riesgos |
| **Circular Única de Bancos** | Detalle de metodologías y reportes |
| **Disposiciones de Casas de Bolsa** | Reglas para intermediarios bursátiles |
| **Acuerdos de Basilea** | Estándares internacionales (Basilea II, III, IV) |

#### Requerimientos de Capital

| Tipo de Riesgo | Requerimiento |
|----------------|---------------|
| **Riesgo de Crédito** | Activos ponderados por riesgo × 8% |
| **Riesgo de Mercado** | VaR × multiplicador × 8% |
| **Riesgo Operacional** | Según metodología (BIA, SA, AMA) |

#### Índice de Capitalización (ICAP)

```
ICAP = Capital Neto / Activos Ponderados Sujetos a Riesgo Totales
```

| Categoría | ICAP Mínimo |
|-----------|-------------|
| **Categoría I (Adecuadamente capitalizado)** | ≥ 10.5% |
| **Categoría II** | 8% - 10.5% |
| **Categoría III** | 7% - 8% |
| **Categoría IV** | 4% - 7% |
| **Categoría V** | < 4% |

#### Reportes Regulatorios

| Reporte | Frecuencia | Contenido |
|---------|------------|-----------|
| **R01 - Capitalización** | Mensual | ICAP, capital neto, activos ponderados |
| **R04 - Riesgo de Crédito** | Mensual | Cartera, provisiones, concentración |
| **R08 - Riesgo de Mercado** | Mensual | VaR, sensibilidades, límites |
| **R27 - Riesgo de Liquidez** | Diario/Mensual | CCL, CFEN, brechas |
| **R28 - Riesgo Operacional** | Trimestral | Eventos de pérdida, capital |

---

## 12. Referencias Oficiales

### Documentos Técnicos de Banco de México

1. **CETES**: "Descripción Técnica de los Certificados de la Tesorería de la Federación"
   - URL: https://www.banxico.org.mx/mercados/

2. **Bonos M**: "Descripción Técnica de los Bonos de Desarrollo del Gobierno Federal con Tasa de Interés Fija"
   - URL: https://www.banxico.org.mx/mercados/

3. **Bondes D**: "Descripción Técnica de los Bonos de Desarrollo del Gobierno Federal BONDES D"
   - URL: https://www.banxico.org.mx/mercados/

4. **Bondes F**: "Descripción Técnica de los Bonos de Desarrollo del Gobierno Federal BONDES F"
   - URL: https://www.banxico.org.mx/mercados/

5. **Udibonos**: "Descripción Técnica de los Bonos de Desarrollo del Gobierno Federal denominados en Unidades de Inversión"
   - URL: https://www.banxico.org.mx/mercados/

### Regulación y Normatividad

6. **Disposiciones de Carácter General Aplicables a las Instituciones de Crédito**
   - URL: https://www.cnbv.gob.mx/Normatividad/

7. **CNBV - Sector Bursátil**
   - URL: https://www.cnbv.gob.mx/SECTORES-SUPERVISADOS/BURSÁTIL/

8. **Acuerdos de Basilea**
   - URL: https://www.bis.org/bcbs/

### Otros Recursos

- **Cetesdirecto**: https://www.cetesdirecto.com
- **Sistema de Información Económica (SIE) de Banxico**: https://www.banxico.org.mx/SieInternet/
- **Libro electrónico "El Mercado de Valores Gubernamentales en México"**: https://www.banxico.org.mx/elib/mercado-valores-gub/
- **Bolsa Mexicana de Valores (BMV)**: https://www.bmv.com.mx
- **MexDer (Mercado Mexicano de Derivados)**: https://www.mexder.com.mx
- **Educación Financiera Banxico**: https://educa.banxico.org.mx

---

## Anexo: Glosario de Términos

| Término | Definición |
|---------|------------|
| **AIR** | Administración Integral de Riesgos |
| **Ask/Offer** | Precio al que un vendedor está dispuesto a vender |
| **Asigna** | Cámara de compensación del MexDer |
| **Backtesting** | Validación de modelos comparando estimaciones vs. resultados reales |
| **Bid** | Precio al que un comprador está dispuesto a comprar |
| **BIVA** | Bolsa Institucional de Valores |
| **BMV** | Bolsa Mexicana de Valores |
| **BPA** | Bono de Protección al Ahorro (IPAB) |
| **CCL/LCR** | Coeficiente de Cobertura de Liquidez |
| **CFEN/NSFR** | Coeficiente de Financiamiento Estable Neto |
| **CNBV** | Comisión Nacional Bancaria y de Valores |
| **Convexidad** | Medida de curvatura de la relación precio-rendimiento |
| **CRO** | Chief Risk Officer (Director de Riesgos) |
| **Cupón** | Pago periódico de intereses de un bono |
| **Delta** | Sensibilidad del precio de una opción ante cambios en el subyacente |
| **Derivado** | Instrumento cuyo valor depende de un activo subyacente |
| **Descuento** | Cuando el precio es menor al valor nominal |
| **Duración** | Sensibilidad del precio ante cambios en tasas |
| **EAD** | Exposición al momento del incumplimiento |
| **Forward** | Contrato a plazo no estandarizado (OTC) |
| **Fungible** | Intercambiable con otros títulos de la misma clase |
| **Futuro** | Contrato a plazo estandarizado (bolsa) |
| **Gamma** | Sensibilidad del delta ante cambios en el subyacente |
| **ICAP** | Índice de Capitalización |
| **Indeval** | Institución para el Depósito de Valores |
| **INPC** | Índice Nacional de Precios al Consumidor |
| **IPAB** | Instituto para la Protección al Ahorro Bancario |
| **KRI** | Indicador Clave de Riesgo |
| **LGD** | Severidad de la pérdida dado el incumplimiento |
| **MexDer** | Mercado Mexicano de Derivados |
| **Opción** | Derecho (no obligación) de comprar o vender |
| **OTC** | Over-the-Counter (mercado extrabursátil) |
| **Par** | Precio igual al valor nominal |
| **PD** | Probabilidad de incumplimiento |
| **PE** | Pérdida esperada |
| **Prima** | Cuando el precio es mayor al valor nominal |
| **Precio Limpio** | Precio sin incluir intereses devengados |
| **Precio Sucio** | Precio incluyendo intereses devengados |
| **RCSA** | Autoevaluación de riesgos y controles |
| **Reporto** | Operación de compraventa con pacto de recompra |
| **SHCP** | Secretaría de Hacienda y Crédito Público |
| **Sobretasa/Spread** | Prima adicional sobre una tasa de referencia |
| **Stress Testing** | Pruebas de estrés bajo escenarios adversos |
| **Swap** | Intercambio de flujos de efectivo |
| **TIIE** | Tasa de Interés Interbancaria de Equilibrio |
| **UAIR** | Unidad de Administración Integral de Riesgos |
| **UDI** | Unidad de Inversión (indexada a inflación) |
| **VaR** | Valor en Riesgo |
| **Vega** | Sensibilidad del precio de una opción ante cambios en volatilidad |
| **Yield/YTM** | Rendimiento al vencimiento |

---

*Documento elaborado con información oficial de Banco de México, la Secretaría de Hacienda y Crédito Público, y la Comisión Nacional Bancaria y de Valores.*

*Última actualización: Enero 2026*

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/theory
