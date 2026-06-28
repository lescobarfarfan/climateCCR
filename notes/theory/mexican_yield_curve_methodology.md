# Construcción de la Curva de Rendimientos de Valores Gubernamentales Mexicanos

## Guía Técnica de Implementación

---

## 1. Introducción

La curva de rendimientos (yield curve) es la representación gráfica de las tasas de interés observadas en un momento dado para instrumentos de deuda con diferentes plazos al vencimiento pero con la misma calidad crediticia. En el caso de México, la curva de referencia se construye a partir de instrumentos de deuda gubernamental emitidos por el Gobierno Federal, operados a través de Banco de México.

La curva es una **fotografía del mercado en un instante específico**: cada día de operación produce una curva distinta. Su utilidad principal es servir como base para la valuación de instrumentos de renta fija, la estimación de tasas forward implícitas y la gestión de riesgos de mercado.

---

## 2. Instrumentos de Deuda Gubernamental Mexicana

### 2.1 CETES (Certificados de la Tesorería de la Federación)

Los CETES son instrumentos de descuento puro (cupón cero). No pagan intereses periódicos; el rendimiento proviene de la diferencia entre el precio de compra (con descuento) y el valor nominal de redención.

- **Valor Nominal (VN):** $10 MXN
- **Plazos de emisión estándar:** 28, 91, 182 y 364 días
- **Convención de días:** Actual/360
- **Mercado primario:** Subastas semanales conducidas por Banco de México

#### 2.1.1 Cálculo del Precio a partir de la Tasa de Descuento

El precio de un CETE se calcula a partir de su **tasa de descuento** $d$ (expresada en términos anuales, base 360):

$$P = VN \times \left(1 - d \times \frac{t}{360}\right)$$

Donde:

- $P$ = precio del CETE
- $VN$ = valor nominal ($10 MXN)
- $d$ = tasa de descuento anualizada (decimal)
- $t$ = plazo al vencimiento en días

**Ejemplo:** Un CETE a 91 días con tasa de descuento del 10.50%:

$$P = 10 \times \left(1 - 0.1050 \times \frac{91}{360}\right) = 10 \times (1 - 0.02654) = \$9.7346$$

#### 2.1.2 Cálculo del Rendimiento (Yield) a partir del Precio

La **tasa de rendimiento** $r$ (yield) de un CETE se calcula como el retorno efectivo sobre la inversión:

$$r = \frac{VN - P}{P} \times \frac{360}{t}$$

Donde:

- $r$ = tasa de rendimiento anualizada, base 360
- $VN$ = valor nominal
- $P$ = precio de compra
- $t$ = plazo al vencimiento en días

Esta fórmula refleja que el inversionista desembolsa $P$ y recibe $VN$ al vencimiento, obteniendo una ganancia de $(VN - P)$, la cual se anualiza multiplicando por $\frac{360}{t}$.

**Ejemplo (continuación):** Con $P = 9.7346$ y $t = 91$:

$$r = \frac{10 - 9.7346}{9.7346} \times \frac{91}{360} = 0.02727 \times 3.956 = 0.10789 = 10.789\%$$

Nótese que $r > d$. La tasa de rendimiento siempre es mayor que la tasa de descuento porque el rendimiento se calcula sobre la inversión real (el precio pagado), mientras que el descuento se calcula sobre el valor nominal.

#### 2.1.3 Conversión a Tasa Cupón Cero Continua

Para fines de modelación (especialmente Nelson-Siegel), es común expresar la tasa en términos continuos:

$$z_t = -\frac{\ln(P / VN)}{\tau}$$

Donde:

- $z_t$ = tasa cupón cero continua al plazo $\tau$
- $\tau$ = plazo al vencimiento expresado en **años** (i.e., $\tau = t / 360$ o $t / 365$ dependiendo de la convención adoptada)
- $P$ = precio observado del CETE
- $VN$ = valor nominal

En esta expresión, $z_t$ es la tasa que, compuesta continuamente durante $\tau$ años, iguala una inversión de $P$ con un pago final de $VN$:

$$P = VN \times e^{-z_t \cdot \tau} \quad \Longrightarrow \quad z_t = -\frac{\ln(P/VN)}{\tau}$$

### 2.2 Bonos de Desarrollo del Gobierno Federal (Bondes)

Bonos de tasa flotante referenciados a la tasa de fondeo bancario (Bondes F) o a la tasa de interés interbancaria de equilibrio TIIE (Bondes G).

- **Valor nominal:** $100 MXN
- **Plazos:** 3 y 5 años
- **Cupones:** Pagos cada 28 días, tasa variable
- **Uso en la curva:** Se utilizan con precaución ya que son instrumentos de tasa flotante. Para la curva de rendimientos cupón cero se requiere un ajuste o se excluyen.

### 2.3 Bonos de Desarrollo del Gobierno Federal a Tasa Fija (Bonos M)

Bonos con tasa de interés fija y pago de cupones semestrales. Son el instrumento principal para la parte media y larga de la curva.

- **Valor nominal:** $100 MXN
- **Plazos de emisión:** 3, 5, 10, 20 y 30 años
- **Cupones:** Semestrales (cada 182 días), tasa fija
- **Convención de días:** Actual/360 para devengamiento

#### 2.3.1 Valuación de un Bono M

El precio limpio de un Bono M es el valor presente de todos sus flujos futuros descontados:

$$P = \sum_{i=1}^{n} \frac{C}{(1 + z_{t_i})^{t_i}} + \frac{VN}{(1 + z_{t_n})^{t_n}}$$

Donde:

- $P$ = precio del bono
- $C$ = pago de cupón semestral = $VN \times \frac{\text{tasa cupón}}{2}$
- $z_{t_i}$ = tasa cupón cero correspondiente al plazo $t_i$
- $t_i$ = plazo en años hasta el $i$-ésimo flujo
- $n$ = número total de cupones pendientes

### 2.4 UDIBONOS

Bonos de tasa fija indexados a la inflación (denominados en UDIs, Unidades de Inversión).

- **Valor nominal:** 100 UDIs
- **Plazos:** 3, 10 y 30 años
- **Uso en la curva:** Permiten construir una curva real separada. La diferencia entre la curva nominal (Bonos M) y la real (UDIBONOS) da una medida del *breakeven inflation*.

---

## 3. Construcción de la Curva Cupón Cero (Bootstrapping)

### 3.1 Principio General

El bootstrapping es un procedimiento iterativo que extrae tasas cupón cero implícitas a partir de instrumentos observados en el mercado. Se avanza desde los plazos más cortos (donde los CETES ya son instrumentos cupón cero) hacia los plazos más largos (donde se necesita descomponer bonos con cupón).

### 3.2 Paso 1 — Parte Corta (CETES)

Como los CETES son instrumentos de descuento puro, sus rendimientos **son directamente** tasas cupón cero:

$$z_{t} = \frac{VN - P}{P} \times \frac{360}{t}$$

Para cada CETE disponible (28, 91, 182, 364 días), se obtiene un punto de la curva directamente.

### 3.3 Paso 2 — Parte Media y Larga (Bonos M)

Para un Bono M con $n$ cupones pendientes, se conoce el precio $P$ observado en el mercado. Se utilizan las tasas cupón cero ya estimadas para descontar todos los flujos excepto el último, y se despeja la tasa cupón cero del plazo más largo:

$$P = \sum_{i=1}^{n-1} \frac{C}{(1 + z_{t_i})^{t_i}} + \frac{C + VN}{(1 + z_{t_n})^{t_n}}$$

Despejando $z_{t_n}$:

$$z_{t_n} = \left( \frac{C + VN}{P - \sum_{i=1}^{n-1} \frac{C}{(1 + z_{t_i})^{t_i}}} \right)^{1/t_n} - 1$$

**Requisitos:**

1. Las tasas $z_{t_1}, z_{t_2}, \ldots, z_{t_{n-1}}$ deben estar disponibles previamente (ya sea directamente de CETES o de bonos con vencimiento anterior).
2. Para plazos intermedios donde no hay un instrumento exacto, se utiliza interpolación (lineal, log-lineal, o spline cúbica) sobre las tasas ya bootstrapeadas.

### 3.4 Paso 3 — Interpolación entre Nodos

Los puntos directos obtenidos del bootstrapping producen una curva discreta. Para obtener tasas a cualquier plazo se requiere interpolación. Las opciones comunes son:

- **Interpolación lineal sobre tasas:** Simple pero puede producir tasas forward no suaves.
- **Interpolación log-lineal sobre factores de descuento:** $\ln(DF(\tau))$ se interpola linealmente.
- **Spline cúbica natural:** Produce una curva suave y diferenciable.
- **Ajuste paramétrico (Nelson-Siegel / Svensson):** Abordado en la sección 4.

---

## 4. Modelo Nelson-Siegel

### 4.1 Formulación

El modelo propuesto por Nelson y Siegel (1987) parametriza la curva de rendimientos cupón cero como función del plazo $\tau$:

$$y(\tau) = \beta_0 + \beta_1 \left( \frac{1 - e^{-\lambda\tau}}{\lambda\tau} \right) + \beta_2 \left( \frac{1 - e^{-\lambda\tau}}{\lambda\tau} - e^{-\lambda\tau} \right)$$

Donde:

| Parámetro | Interpretación | Comportamiento |
|-----------|----------------|----------------|
| $\beta_0$ | **Nivel** (factor de largo plazo) | $\lim_{\tau \to \infty} y(\tau) = \beta_0$. Representa la tasa asintótica de largo plazo. |
| $\beta_1$ | **Pendiente** (factor de corto plazo) | Su carga comienza en 1 y decae exponencialmente a 0. $y(0) = \beta_0 + \beta_1$. Un $\beta_1 < 0$ indica curva con pendiente positiva. |
| $\beta_2$ | **Curvatura** (factor de mediano plazo) | Su carga comienza en 0, alcanza un máximo y decae a 0. Captura la "joroba" o concavidad de la curva. |
| $\lambda$ | **Velocidad de decaimiento** | Controla la rapidez con que los factores de corto y mediano plazo convergen a cero. Determina en qué plazo $\beta_2$ alcanza su efecto máximo. |

### 4.2 Interpretación Económica

Los tres factores tienen correspondencia con variables macroeconómicas (Diebold y Li, 2006):

- $\beta_0$ (Nivel) ↔ Expectativas de inflación de largo plazo
- $\beta_1$ (Pendiente) ↔ Postura de política monetaria (diferencial entre tasas cortas y largas)
- $\beta_2$ (Curvatura) ↔ Incertidumbre o primas de plazo en el mediano plazo

### 4.3 Extensión de Svensson (1994)

Svensson añade un segundo término de curvatura para mayor flexibilidad:

$$y(\tau) = \beta_0 + \beta_1 \left( \frac{1 - e^{-\lambda_1\tau}}{\lambda_1\tau} \right) + \beta_2 \left( \frac{1 - e^{-\lambda_1\tau}}{\lambda_1\tau} - e^{-\lambda_1\tau} \right) + \beta_3 \left( \frac{1 - e^{-\lambda_2\tau}}{\lambda_2\tau} - e^{-\lambda_2\tau} \right)$$

Esto permite capturar curvas con dos jorobas o inflexiones más complejas. El costo es la adición de dos parámetros ($\beta_3$, $\lambda_2$), que dificulta la estimación.

### 4.4 Estimación de Parámetros

#### Método 1: $\lambda$ fijo + OLS

Diebold y Li (2006) proponen fijar $\lambda$ a priori (por ejemplo, $\lambda = 0.0609$ para datos mensuales, que maximiza la carga de $\beta_2$ a 30 meses). Con $\lambda$ fijo, el modelo es lineal en $(\beta_0, \beta_1, \beta_2)$ y puede estimarse por Mínimos Cuadrados Ordinarios:

$$\min_{\beta_0, \beta_1, \beta_2} \sum_{i=1}^{N} \left[ y_i^{\text{obs}} - y(\tau_i; \beta_0, \beta_1, \beta_2, \lambda) \right]^2$$

Donde $y_i^{\text{obs}}$ es la tasa cupón cero observada (o bootstrapeada) al plazo $\tau_i$.

#### Método 2: Estimación conjunta no lineal

Se estiman los cuatro parámetros simultáneamente mediante optimización no lineal (e.g., Levenberg-Marquardt, Nelder-Mead, o BFGS):

$$\min_{\beta_0, \beta_1, \beta_2, \lambda} \sum_{i=1}^{N} \left[ y_i^{\text{obs}} - y(\tau_i; \beta_0, \beta_1, \beta_2, \lambda) \right]^2$$

#### Método 3: Grid search en $\lambda$ + OLS

Se evalúa una malla de valores de $\lambda$ (e.g., de 0.01 a 3.0 en incrementos de 0.01), estimando $(\beta_0, \beta_1, \beta_2)$ por OLS para cada valor, y seleccionando el $\lambda$ que minimiza la suma de errores cuadrados. Es computacionalmente robusto y evita mínimos locales.

### 4.5 Pseudocódigo de Implementación

```
Entradas:
  - Vector de plazos: tau = [tau_1, tau_2, ..., tau_N] (en años)
  - Vector de tasas observadas: y_obs = [y_1, y_2, ..., y_N]

Para cada lambda en grid [0.01, 0.02, ..., 3.00]:
  Construir matriz X de dimensión N x 3:
    X[i, 0] = 1
    X[i, 1] = (1 - exp(-lambda * tau[i])) / (lambda * tau[i])
    X[i, 2] = X[i, 1] - exp(-lambda * tau[i])
  
  Estimar betas por OLS: beta = (X'X)^(-1) X' y_obs
  Calcular residuos: e = y_obs - X * beta
  Calcular SSE = sum(e^2)

Seleccionar lambda* que minimiza SSE
Reportar beta_0*, beta_1*, beta_2*, lambda*
```

---

## 5. Fuentes de Datos

### 5.1 Banco de México — Sistema de Información Económica (SIE)

- **URL:** https://www.banxico.org.mx/SieInternet/
- **Contenido:** Tasas de rendimiento en colocación primaria, tasas de interés de referencia, vector de precios de títulos gubernamentales
- **Series relevantes:**
  - Tasas de rendimiento de CETES (28, 91, 182, 364 días)
  - Tasas de interés de Bonos M a distintos plazos
  - Tasa de fondeo gubernamental
  - Tasa objetivo de Banco de México

### 5.2 Vector de Precios de Títulos Gubernamentales

- **URL:** https://www.banxico.org.mx/mercados/valores-gubernamentales-vecto.html
- **Contenido:** Publicación diaria con precios limpios, precios sucios, tasas de rendimiento y características de cada emisión vigente de CETES, Bondes, Bonos M y UDIBONOS.
- **Formato:** Archivo descargable con datos al cierre de cada día hábil.

### 5.3 Valmer (Valuación Operativa y Referencias de Mercado)

- **URL:** https://www.valmer.com.mx
- **Contenido:** Proveedor de precios autorizado por la CNBV. Publica curvas de rendimiento, vectores de precios, superficies de volatilidad y metodologías de valuación.
- **Nota:** El acceso a datos detallados y metodologías completas requiere suscripción.

### 5.4 Bolsa Mexicana de Valores (BMV)

- **URL:** https://www.bmv.com.mx
- **Contenido:** Información de mercado, aunque la mayoría de la operación de valores gubernamentales se realiza en el mercado OTC.

---

## 6. Escenarios de Estrés sobre la Curva

### 6.1 Enfoque por Choque a Factores Nelson-Siegel

La parametrización Nelson-Siegel permite diseñar escenarios de estrés con interpretación económica directa al modificar los factores estimados:

| Escenario Macro | Factor Afectado | Dirección del Choque |
|----------------|-----------------|----------------------|
| Aumento en expectativas de inflación LP | $\beta_0$ (Nivel) | $\uparrow$ |
| Endurecimiento de política monetaria | $\beta_1$ (Pendiente) | Se hace más negativo (la curva se aplana o invierte) |
| Aumento de incertidumbre en mediano plazo | $\beta_2$ (Curvatura) | $\uparrow$ |
| Desplazamiento paralelo | $\beta_0$ | $\uparrow$ o $\downarrow$ uniformemente |

**Ejemplo concreto:** Si el escenario de estrés asume un incremento de 300 bps en inflación y 500 bps en tasas de interés de política monetaria en un horizonte de 3 años:

1. Incrementar $\beta_0$ en aproximadamente 200-300 bps (efecto Fisher de largo plazo)
2. Ajustar $\beta_1$ para reflejar que la tasa corta sube proporcionalmente más que la larga (aplanamiento de la curva)
3. Incrementar $\beta_2$ si se espera que la incertidumbre se concentre en plazos medios

### 6.2 Enfoque por Componentes Principales (PCA)

Los primeros tres componentes principales de los cambios históricos en la curva típicamente explican >95% de la variación y corresponden a nivel, pendiente y curvatura. Se pueden diseñar escenarios como múltiplos de las desviaciones estándar históricas de cada componente.

### 6.3 Choques Históricos

Utilizar fechas de estrés pasadas (e.g., taper tantrum de 2013, elección 2018, COVID-19 en 2020) como escenarios. Se calculan los cambios observados en la curva y se aplican a la curva actual.

---

## 7. Convenciones Importantes

### 7.1 Base de Días

| Instrumento | Convención de devengamiento | Convención de anualización |
|-------------|---------------------------|---------------------------|
| CETES | N/A (cupón cero) | Actual/360 |
| Bonos M | Actual/360 (cupón) | Actual/360 |
| UDIBONOS | Actual/360 (cupón en UDIs) | Actual/360 |

### 7.2 Tasa de Descuento vs. Tasa de Rendimiento

Es crítico distinguir ambas para CETES:

- **Tasa de descuento ($d$):** Es la tasa que Banco de México publica en los resultados de subasta. Se aplica sobre el valor nominal para determinar el precio.
- **Tasa de rendimiento ($r$):** Es el retorno efectivo sobre la inversión (sobre el precio pagado). **Esta es la tasa relevante para la curva de rendimientos.**

La relación entre ambas es:

$$r = \frac{d}{1 - d \times (t/360)}$$

### 7.3 Precio Limpio vs. Precio Sucio

Para bonos con cupón (Bonos M, UDIBONOS):

$$\text{Precio Sucio} = \text{Precio Limpio} + \text{Interés Devengado}$$

El interés devengado se calcula como:

$$\text{Interés Devengado} = VN \times \frac{\text{Tasa Cupón}}{2} \times \frac{\text{Días transcurridos desde último cupón}}{182}$$

Para la construcción de la curva, se utiliza el **precio sucio** (que representa el flujo real de efectivo) para descontar flujos en el bootstrapping.

---

## 8. Referencias

### Metodología de Curvas de Rendimiento

1. **Nelson, C. R. y Siegel, A. F. (1987).** "Parsimonious Modeling of Yield Curves." *The Journal of Business*, 60(4), 473–489. https://doi.org/10.1086/296409
   — Artículo original que propone el modelo de tres factores para la curva de rendimientos.

2. **Svensson, L. E. O. (1994).** "Estimating and Interpreting Forward Interest Rates: Sweden 1992–1994." *IMF Working Paper*, WP/94/114. https://www.imf.org/external/pubs/ft/wp/wp94114.pdf
   — Extensión del modelo Nelson-Siegel con un segundo término de curvatura.

3. **Diebold, F. X. y Li, C. (2006).** "Forecasting the Term Structure of Government Bond Yields." *Journal of Econometrics*, 130(2), 337–364. https://doi.org/10.1016/j.jeconom.2005.03.005
   — Reinterpretación dinámica de Nelson-Siegel como modelo de factores latentes. Propone la fijación de $\lambda$ y estimación por OLS.

4. **Diebold, F. X. y Rudebusch, G. D. (2013).** *Yield Curve Modeling and Forecasting: The Dynamic Nelson-Siegel Approach.* Princeton University Press.
   — Tratamiento comprehensivo del modelo DNS y sus extensiones para pronóstico y análisis macroeconómico.

5. **Bank for International Settlements (2005).** "Zero-Coupon Yield Curves: Technical Documentation." *BIS Papers*, No. 25. https://www.bis.org/publ/bppdf/bispap25.htm
   — Compendio de metodologías utilizadas por bancos centrales de múltiples países para estimar curvas de rendimiento, incluyendo detalles de implementación.

### Instrumentos de Deuda del Gobierno Federal Mexicano

6. **Banco de México.** "Descripción Técnica de los Certificados de la Tesorería de la Federación (CETES)." Disponible en: https://www.banxico.org.mx/mercados/d/%7B8D012ACA-E430-6F0D-BF23-E49D8C0B7E5C%7D.pdf
   — Documento oficial con la descripción, fórmulas de valuación y convenciones de los CETES.

7. **Banco de México.** "Descripción Técnica de los Bonos de Desarrollo del Gobierno Federal (Bonos M)." Disponible en: https://www.banxico.org.mx/mercados/d/%7BDA5A66FB-B391-D837-A5B1-E5D82B7FB9EF%7D.pdf
   — Documento oficial con la descripción y fórmulas de valuación de Bonos M.

8. **Banco de México.** "Vector de Precios de Títulos Gubernamentales." https://www.banxico.org.mx/mercados/valores-gubernamentales-vecto.html
   — Publicación diaria con precios y rendimientos de todos los títulos gubernamentales vigentes.

9. **Banco de México.** "Sistema de Información Económica (SIE)." https://www.banxico.org.mx/SieInternet/
   — Portal de acceso a series históricas de tasas de interés, tipos de cambio y otras variables económicas.

### Estrés y Riesgo de Tasa de Interés

10. **Litterman, R. y Scheinkman, J. (1991).** "Common Factors Affecting Bond Returns." *The Journal of Fixed Income*, 1(1), 54–61. https://doi.org/10.3905/jfi.1991.692347
    — Identificación de los tres factores principales (nivel, pendiente, curvatura) mediante PCA en la curva de rendimientos de EE.UU.

11. **Basel Committee on Banking Supervision (2016).** "Interest Rate Risk in the Banking Book." *Standards*, BCBS 368. https://www.bis.org/bcbs/publ/d368.htm
    — Estándar regulatorio que incluye escenarios de estrés para curvas de rendimiento y metodologías para su cuantificación.

### Complementarias

12. **Hagan, P. S. y West, G. (2006).** "Interpolation Methods for Curve Construction." *Applied Mathematical Finance*, 13(2), 89–129. https://doi.org/10.1080/13504860500396032
    — Comparación detallada de métodos de interpolación para curvas de rendimiento, incluyendo splines y monotone convex.

13. **Gürkaynak, R. S., Sack, B. y Wright, J. H. (2007).** "The U.S. Treasury Yield Curve: 1961 to the Present." *Journal of Monetary Economics*, 54(8), 2291–2304. https://doi.org/10.1016/j.jmoneco.2007.06.029
    — Metodología de estimación utilizada por la Reserva Federal con el modelo Svensson. Referencia útil para comparación y validación.

---

## 9. Notas de Implementación

### 9.1 Orden Sugerido de Implementación

1. Descargar datos del SIE de Banco de México (tasas de rendimiento de CETES y precios de Bonos M)
2. Calcular las tasas cupón cero directas de los CETES
3. Implementar el bootstrapping secuencial para Bonos M
4. Interpolar los puntos faltantes (spline cúbica recomendada como paso intermedio)
5. Estimar los parámetros de Nelson-Siegel usando grid search + OLS
6. Validar el ajuste calculando el error cuadrático medio y comparando visualmente con la curva publicada por Valmer o Banxico

### 9.2 Advertencias

- Los Bondes (tasa flotante) no se incluyen directamente en la curva cupón cero estándar. Si se desea utilizarlos, se requiere estimar un spread sobre la tasa de referencia.
- La liquidez varía entre emisiones. Los Bonos M on-the-run (emisión más reciente) suelen tener mayor liquidez y sus precios reflejan mejor el valor de mercado.
- Las tasas publicadas por Banxico en resultados de subasta son tasas de descuento para CETES; deben convertirse a rendimiento antes de usarlas en la curva.
- Considerar el efecto fiscal: los rendimientos de títulos gubernamentales mexicanos están sujetos a retención de ISR, lo que puede afectar las tasas observadas vs. las tasas antes de impuestos.

---

*Documento generado como referencia técnica para la construcción de la curva de rendimientos de valores gubernamentales mexicanos.*

## Related
[[MKT_MOC]] · Home: [[_INDEX]]

#arm/mkt #type/theory
