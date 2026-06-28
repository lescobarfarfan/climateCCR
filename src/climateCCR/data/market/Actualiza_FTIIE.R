# Codigo para actualizar datos de F-TIIE usando la API del SIE - Banxico ----

## Librerías -----
suppressPackageStartupMessages(library(tidyverse))
library(siebanxicor)
library(dotenv)

## Definimos token de la API -----
dotenv::load_dot_env()
setToken(Sys.getenv("SIEBANXICO_TOKEN"))

## Definimos parámetros de la búsqueda -----

### Fechas de inicio y fin de la búsqueda ----
inicio <- "2006-01-02"
final <- today()

## Extracciones curva corto plazo (TIIE) -----

### Series seleccionadas ------
ids_series <- c("TObjetivo" = "SF61745",
                "FTIIE" = "SF331451",
                "TIIE28" = "SF43783",
                "TIIE91" = "SF43878",
                "TIIE182" = "SF111916")

### Realizamos query ----
tiies_query <- getSeriesData(series = ids_series,
                             startDate = inicio,
                             endDate = final)

### Acomodamos datos -----
tiies <- tibble()

for (i in 1:length(tiies_query)) { # nolint: seq_linter.
  id_serie <- names(tiies_query)[i]
  nom_serie <- names(ids_series[which(ids_series == id_serie)])
  
  if (i == 1) {
    aux_df <- tibble(Fecha = tiies_query[[id_serie]]$date,
                     val = tiies_query[[id_serie]]$value/100)
    names(aux_df)[2] <- nom_serie
    
    tiies <- list(tiies, aux_df) %>% 
      bind_rows()
  } else {
    aux_df <- tibble(Fecha = tiies_query[[id_serie]]$date,
                     val = tiies_query[[id_serie]]$value/100)
    names(aux_df)[2] <- nom_serie
    
    tiies <- tiies %>% 
      left_join(aux_df, by = "Fecha")
  }
}

### Guardamos -----
tiies %>%
  select(Fecha, TObjetivo, FTIIE, TIIE28, TIIE91, TIIE182) %>% 
  write_csv(paste0("data/TIIEs_Extraccion_", final, ".csv"))

## Extraccion para tenor de 1 año (cetes 364 días) ----

### Identificadores de las series -----
ids_series_cetes <- c("Plazo" = "SF45425",
                      "PrecioSucio" = "SF45445",
                      "TasaRendimiento" = "SF45473")

# Hacemos query 
series_cetes <- getSeriesData(series = ids_series_cetes,
                              startDate = inicio,
                              endDate = final)

# Acomodamos en un data farme.
cetes_364 <- tibble(Fecha = series_cetes[[ids_series_cetes["Plazo"]]]$date,
                    Plazo = series_cetes[[ids_series_cetes["Plazo"]]]$value,
                    Precio = series_cetes[[ids_series_cetes["PrecioSucio"]]]$value,
                    Tasa = series_cetes[[ids_series_cetes["TasaRendimiento"]]]$value/100)

### Guardamos -----
cetes_364 %>% 
  write_csv(paste0("data/Cetes364_Extracion_", final, ".csv"))

## Extracciones curva largo plazo (bonos m) -----

### Series de plazo ------
ids_series_plazo <- c("BonosM_0_3" = "SF45427",
                      "BonosM_3_5" = "SF45428",
                      "BonosM_5_7" = "SF45429",
                      "BonosM_7_10" = "SF45430",
                      "BonosM_10_20" = "SF45431",
                      "BonosM_20_30" = "SF60720")

series_plazo <- getSeriesData(series = ids_series_plazo,
                              startDate = inicio,
                              endDate = final)

### Series de precio sucio -----
ids_series_valor <- c("BonosM_0_3" = "SF45449",
                      "BonosM_3_5" = "SF45451",
                      "BonosM_5_7" = "SF45453",
                      "BonosM_7_10" = "SF45455",
                      "BonosM_10_20" = "SF45457",
                      "BonosM_20_30" = "SF60722")

series_valor <- getSeriesData(series = ids_series_valor,
                              startDate = inicio,
                              endDate = final)

### Series de cupon vigente -----
ids_series_cupon <- c("BonosM_0_3" = "SF45475",
                      "BonosM_3_5" = "SF45476",
                      "BonosM_5_7" = "SF45477",
                      "BonosM_7_10" = "SF45478",
                      "BonosM_10_20" = "SF45479",
                      "BonosM_20_30" = "SF60723")

series_cupon <- getSeriesData(series = ids_series_cupon,
                              startDate = inicio,
                              endDate = final)

nombres_bonos <- names(ids_series_plazo)

### Procesamiento de datos -----
bonos_m <- tibble()

for (i in 1:length(nombres_bonos)) {
  aux_nom_bono <- nombres_bonos[i]
  aux_id_plazo <- ids_series_plazo[aux_nom_bono]
  aux_id_valor <- ids_series_valor[aux_nom_bono]
  aux_id_cupon <- ids_series_cupon[aux_nom_bono]
  
  fecha_plazo <- series_plazo[[aux_id_plazo]]$date
  valor_plazo <- series_plazo[[aux_id_plazo]]$value
  
  aux_df_plazo <- tibble(Fecha = fecha_plazo,
                         Serie = aux_nom_bono,
                         Plazo = valor_plazo)
  
  fecha_valor <- series_valor[[aux_id_valor]]$date
  valor_valor <- series_valor[[aux_id_valor]]$value
  
  aux_df_valor <- tibble(Fecha = fecha_valor,
                         Serie = aux_nom_bono,
                         Valor = valor_valor)
  
  fecha_cupon <- series_cupon[[aux_id_cupon]]$date
  valor_cupon <- series_cupon[[aux_id_cupon]]$value/100
  
  aux_df_cupon <- tibble(Fecha = fecha_cupon,
                         Serie = aux_nom_bono,
                         Cupon = valor_cupon)
  
  aux_df <- aux_df_plazo %>% 
    left_join(aux_df_cupon, by = c("Fecha", "Serie")) %>% 
    left_join(aux_df_valor, by = c("Fecha", "Serie"))
  
  bonos_m <- list(bonos_m, aux_df) %>% 
    bind_rows()
}

### Escribimos -----
bonos_m %>%
  write_csv(paste0("data/BonosM_Extraccion_", final, ".csv"))
  

## Extracciones bonos MS (ligados a sustentabilidad) ------
inicio_ms <- "2023-07-24"

ids_series_ms <- c("Plazo" = "SF355417",
                   "PrecioLimpio" = "SF355418",
                   "PrecioSucio" = "SF355419",
                   "CuponVigente" = "SF355420")

series_ms <- getSeriesData(series = ids_series_ms,
                           startDate = inicio_ms,
                           endDate = final)

### Procesamiento de datos -----
bonos_ms <- tibble()

for (i in 1:length(series_ms)) {
  aux_serie <- series_ms[[i]]
  aux_id <- names(series_ms)[i]
  aux_nombre <- names(ids_series_ms[which(ids_series_ms == aux_id)])
  aux_fecha <- series_ms[[i]]$date
  aux_valor <- series_ms[[i]]$value
  
  if (i == 1)  {
    aux_df <- tibble(Fecha = aux_fecha,
                     Serie = "BonosMS",
                     valor = aux_valor)
    bonos_ms <- list(bonos_ms, aux_df) %>% 
      bind_rows()
    names(bonos_ms)[ncol(bonos_ms)] <- aux_nombre
  } else {
    aux_df <- tibble(Fecha = aux_fecha,
                     Serie = "BonosMS",
                     valor = aux_valor)
    bonos_ms <- bonos_ms %>%
      left_join(aux_df, by = c("Fecha", "Serie"))
    names(bonos_ms)[ncol(bonos_ms)] <- aux_nombre
  }
  
}

### Escribimos -----
bonos_ms %>%
  write_csv(paste0("data/BonosMS_Extraccion_", final, ".csv"))
