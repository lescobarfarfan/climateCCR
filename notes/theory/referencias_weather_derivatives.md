# Referencias académicas consolidadas

## 1. Manuales generales sobre derivados financieros

### En español

| Título | Autor(es) | Editorial / Año | ISBN | Observaciones |
|--------|-----------|-----------------|------|---------------|
| **Derivados Financieros. Productos, riesgos, estrategias, contabilización y regulación** | Francisco Javier Fernández Fernández, Roberto Knop Muszynski y otros 11 autores | Delta Publicaciones, 2021 | 9788417526689 | Obra colectiva con enfoque completo: productos (plain vanilla, exóticos, swaps, tipos de interés, crédito, equity, materias primas), gestión de riesgos (mercado, contrapartida), contabilidad y regulación. |

### En inglés

| Título | Autor(es) | Editorial / Año | ISBN / Notas |
|--------|-----------|-----------------|--------------|
| **Derivatives Pricing** | Frédéric D. Vrins | Cambridge University Press, 2025 | – | Equilibrio entre rigor matemático e intuición financiera. Cubre probabilidad, cálculo estocástico, teoremas fundamentales de valoración, ejemplos numéricos y simulaciones Monte Carlo. |
| **Swaps & Financial Derivatives Library** (varios volúmenes) | Satyajit Das | Wiley (múltiples ediciones) | – | Enciclopedia sobre productos derivados, pricing, gestión de riesgos (VaR, stress testing), riesgo de crédito, aspectos legales (ISDA), contabilidad (FASB 133, IAS 39) y regulación (Basilea). |
| **Options, Futures, and Other Derivatives** | John C. Hull | Pearson (múltiples ediciones) | – | Texto clásico estándar. Cubre forwards, futuros, swaps, opciones plain vanilla y exóticas, modelos estocásticos y gestión de riesgos. Ampliamente utilizado en programas de posgrado. |
| **Stochastic Calculus for Finance** (Vols. I y II) | Steven E. Shreve | Springer (2004) | Vol I: 9780387249681; Vol II: 9780387401010 | Referencia rigurosa para el modelado matemático. Vol I: modelos en tiempo discreto (árboles binomiales). Vol II: cálculo estocástico en tiempo continuo, modelo de Black‑Scholes‑Merton, valoración por cambio de numeraire. |

---

## 2. Referencias sobre riesgos ambientales, climáticos y financieros

### Libros

| Título | Autor(es) / Editor(es) | Editorial / Año | ISBN / Notas |
|--------|------------------------|-----------------|--------------|
| **Weather Derivatives: Modeling and Pricing Weather‑Related Risk** | Alexandridis, A. K., & Zapranis, A. D. | Springer, 2013 | 9781461460718 | Texto fundamental para modelado y valoración de derivados meteorológicos. |
| **Handbook of Quantitative Sustainable Finance** | Peter Tankov, Ruixun Zhang (editores) | CRC Press, 2025 | – | Obra de referencia integral. Dividida en: riesgos y regulación; pricing de activos y gestión de carteras; datos, medición e IA; diseño de productos. Cada capítulo escrito por expertos líderes. |

### Artículos de investigación (riesgos ambientales)

| Título | Autor(es) | Revista / Evento | Año | Enfoque |
|--------|-----------|------------------|------|---------|
| **Weather and Climate Services for Finance—The Development of Financial Meteorology in China** | Zhao, Y. X., et al. | *Advances in Atmospheric Sciences* | 2026 | Revisión del estado del arte en meteorología financiera: índices financieros meteorológicos, derivados climáticos, pruebas de estrés por riesgo climático, servicios para bancos y seguros. |
| **Climate Derivatives and Risk Transfer Mechanisms in Investment Decision‑Making in Developing Economies** | – | 65th ISI World Statistics Congress | 2025 | Análisis de cómo los derivados climáticos y mecanismos de transferencia de riesgo afectan la toma de decisiones de inversión en economías en desarrollo. |
| **Quantifying Downstream Value Chain Carbon Risk: A Six‑Factor Asset Pricing Model for China’s Low‑Carbon Transition** | – | *Mathematics* (MDPI) | 2026 | Extiende el marco de Fama‑French incorporando riesgo de carbono de la cadena de valor *downstream*. Propone un factor DMC basado en modelos input‑output de Ghosh. |
| **Factor Structure of Green, Grey, and Red EU Securities** | – | *Risks* (MDPI) | 2025 | Examina la estructura factorial de activos verdes, grises y rojos en la UE utilizando modelos Fama‑French y Carhart extendidos. Muestra sensibilidades dinámicas a factores tradicionales. |

### Tesis académicas

| Tipo | Título | Autor | Institución | Año | Enfoque |
|------|--------|-------|-------------|------|---------|
| **Tesis doctoral** | *MODELING AND RISK MANAGEMENT WITH APPLICATIONS IN FINANCIAL AND WEATHER DERIVATIVES* | Gleda Kutrolli | Università degli Studi di Milano‑Bicocca | 2021 | Modelado cuantitativo, valoración (pricing) y gestión de riesgos (VaR, Expected Shortfall) de derivados financieros y climáticos. Incluye modelización de series de temperatura y opciones sobre derivados climáticos. |
| **Tesis de maestría** | *An examination of the role of derivatives in corporate risk management: strategies, instruments, and impacts: Case study: Italian weather derivatives market* | Abderrahim El Adnani | Luiss Guido Carli | 2024 | Estudio de caso del mercado italiano de derivados meteorológicos. Incluye metodologías de valoración (Monte Carlo), modelado de temperatura (Ornstein‑Uhlenbeck con estacionalidad) y análisis del riesgo de base (*basis risk*). |

---

## 3. Artículos fundacionales y extensiones sobre derivados climáticos (*Weather Derivatives*)

### Artículos fundacionales (modelos pioneros)

| Referencia | Aporte Principal |
|------------|------------------|
| **Alaton, P., Djehiche, B., & Stillberger, D. (2002).** *On modelling and pricing weather derivatives.* Applied Mathematical Finance, 9(1), 1‑20. | **Modelo de referencia fundamental.** Propone un proceso de Ornstein‑Uhlenbeck (OU) con media estacional y volatilidad constante por meses. Ampliamente citado por su equilibrio entre precisión y simplicidad computacional. |
| **Brody, D. C., Syroka, J., & Zervos, M. (2002).** *Dynamical pricing of weather derivatives.* Quantitative Finance, 2(3), 189‑198. | **Modelo fraccional.** Introduce movimiento browniano fraccional para capturar la memoria larga (persistencia) en series de temperatura. |
| **Benth, F. E., & Šaltytė-Benth, J. (2005).** *Stochastic modelling of temperature variations with a view to weather derivatives.* (Desarrollado en su libro de 2007 y en *Modeling and Pricing in Financial Markets for Weather Derivatives*, World Scientific, 2013). | **Marco integral de modelado estocástico.** Incorpora estacionalidad en media, volatilidad y velocidad de reversión a la media. Aborda características como autocorrelación y efectos de salto. |

### Principales extensiones y mejoras

#### 4.1 Refinamientos del proceso de temperatura subyacente

| Referencia | Aporte / Mejora |
|------------|-----------------|
| **Benth, F. E., & Šaltytė-Benth, J. (2007).** *Modelling and pricing in financial markets for weather derivatives.* World Scientific. | Formaliza y extiende el trabajo de 2005 con una estructura de estacionalidad más flexible para volatilidad y velocidad de reversión. |
| **Zapranis, A., & Alexandridis, A. (2008).** *Modelling temperature time series to price weather derivatives.* (Referenciado en la literatura). | Propone una velocidad de reversión a la media dependiente del tiempo, mejorando el ajuste empírico. |
| **Alfonsi, A., & Vadillo, N. (2024).** *A stochastic volatility model for the valuation of temperature derivatives.* IMA Journal of Management Mathematics, 35(4), 737‑785. | Introduce volatilidad estocástica en el modelo Gaussiano estándar. Permite evaluar mejor eventos extremos (olas de calor/frío) con trazabilidad analítica. |
| **Tong, Y., & Liu, Z. (2020).** *A time-changed Ornstein-Uhlenbeck process for temperature modeling.* | Utiliza un proceso OU con cambio de tiempo para capturar dinámicas temporales complejas, manteniendo flexibilidad. |

#### 4.2 Enfoques de pricing y gestión de riesgo

| Referencia | Aporte / Mejora |
|------------|-----------------|
| **Li, P., Lu, X., & Zhu, S.-P. (2020).** *Pricing weather derivatives with the market price of risk extracted from the utility indifference valuation.* Computers & Mathematics with Applications, 79(12). | Aborda mercados incompletos mediante valoración por utilidad indiferente; resuelve EDP con diferencias finitas. |
| **Li, B., Diao, X., & Wu, C. (2025).** *Model selection for temperature Asian option pricing from long-and short-term forecasting perspectives: Applicability of deep learning algorithms vs. Ornstein-Uhlenbeck processes.* Journal of Systems Management (en línea). | Compara deep learning con procesos OU para opciones asiáticas sobre temperatura en horizontes de corto y largo plazo. |

#### 4.3 Riesgo de base geográfico y modelos espaciales

| Referencia | Aporte / Mejora |
|------------|-----------------|
| **D’Aversa, F., et al. (2023).** *A non-parametric optimization strategy for basis risk mitigation in weather derivatives.* | Propone optimización no paramétrica para mitigar riesgo de base geográfico, aplicado a Italia. |
| **Capriotti, L., et al. (2025).** *A spatially-continuous neural network temperature model for weather derivatives evaluation.* Annals of Operations Research (6 de mayo de 2025). | Modelo continuo espacial con redes neuronales profundas entrenadas con datos satelitales (NASA‑MERRA‑2). Permite valorar derivados en cualquier punto geográfico, reduciendo riesgo de base. |

#### 4.4 Nuevas metodologías (Machine Learning)

| Referencia | Aporte / Mejora |
|------------|-----------------|
| **Huo, H., et al. (2024).** *Pricing Weather Derivatives: A Time Series Neural Network Approach.* arXiv preprint arXiv:2411.12013. | Combina redes neuronales con pronósticos de series temporales para valorar derivados sobre temperatura y precipitación (aplicado a índices en Toronto y Chicago). |
| **Feng, Y., Li, Y., & Zhao, Y. (2025).** *A computationally efficient temperature risk stress testing model with improved extreme temperature description.* Acta Meteorologica Sinica, 83(6), 1502‑1513. | Modelo híbrido (OU + LSTM) para pruebas de estrés de riesgo climático en banca y energía; mejora la descripción de temperaturas extremas con bajo costo computacional. |

### Libros de referencia especializados en derivados climáticos

| Título | Autor(es) | Editorial / Año | Notas |
|--------|-----------|-----------------|-------|
| **Weather Derivative Valuation: The Meteorological, Statistical, Financial and Mathematical Foundations** | Jewson, S., & Brix, A. | Cambridge University Press, 2005 | Tratado integral que cubre los fundamentos meteorológicos, estadísticos, financieros y matemáticos de la valoración de derivados climáticos. |
| **Modeling and Pricing in Financial Markets for Weather Derivatives** | Benth, F. E., & Šaltytė-Benth, J. | World Scientific (Advanced Series on Statistical Science & Applied Probability, Vol. 17), 2013 | Marco unificado para el modelado estocástico de variables climáticas (temperatura, viento, precipitación) y la valoración de derivados. |

---

## Resumen de la evolución en derivados climáticos

1. **Fundaciones (2002‑2005):** Modelos de Alaton et al. (OU con estacionalidad), Brody et al. (fraccional) y Benth & Šaltytė-Benth (marco estocástico completo).
2. **Refinamientos (2007‑2020):** Volatilidad estocástica (Alfonsi & Vadillo, 2024), cambios de tiempo (Tong & Liu, 2020) y métodos de pricing para mercados incompletos (Li et al., 2020).
3. **Nuevas fronteras (2024‑presente):** Machine learning y redes neuronales (Capriotti et al., 2025; Huo et al., 2024), mitigación del riesgo de base geográfico y modelos híbridos para pruebas de estrés (Feng et al., 2025).

---

*Nota: Este documento consolida todas las referencias proporcionadas en las respuestas anteriores. Si se requiere profundizar en algún modelo o autor específico, se puede solicitar información adicional.*