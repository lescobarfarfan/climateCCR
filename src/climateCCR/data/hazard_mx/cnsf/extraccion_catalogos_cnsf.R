# Codigo de extracción de catálogos de datos de CNSF ----
library(tidyverse)

setwd("~/Documents/projects/thesis/natural_risks_calibration/datos/datos_CNSF/")

## Agrícola y ganadero ----
agro_emision <- read_csv("consolidados/agricola_y_animales/emision.csv.gz")
agro_siniestros <- read_csv("consolidados/agricola_y_animales/siniestros.csv.gz")

cat(names(agro_emision), sep="\n")
cat(names(agro_siniestros), sep="\n")

### Siniestros -----
agro_siniestros_cat <- agro_siniestros %>% 
  select(anio, `CAUSA DEL SINIESTRO`) %>% 
  group_by(anio, `CAUSA DEL SINIESTRO`) %>% 
  distinct_all()

write_csv(agro_siniestros_cat,
          "../../catalogos/CNSF/agro_cat_siniestro.csv")

### de cultivos ----

agro_siniestros_cultivos <- agro_siniestros %>% 
  select(anio, CULTIVO, `TIPO DE CULTIVO`, `CICLO DE CULTIVO`) %>% 
  distinct_all()


write_csv(agro_siniestros_cultivos,
          "../../catalogos/CNSF/agro_cat_cultivos.csv")

### de cosas animales ----
agro_siniestros_ganaderos <- agro_siniestros %>% 
  select(anio, `ESPECIE ANIMAL`, `FUNCIÓN ZOOTÉCNICA`) %>% 
  distinct_all()


write_csv(agro_siniestros_ganaderos,
          "../../catalogos/CNSF/agro_cat_ganaderia.csv")

### Esquema aseguramiento ----
agro_esquema_asegu_cat <- agro_siniestros %>% 
  select(anio, `ESQUEMA DE ASEGURAMIENTO`) %>% 
  distinct_all()

write_csv(agro_esquema_asegu_cat,
          "../../catalogos/CNSF/agro_cat_esquema_asegura.csv")


## Automoviles (flotilla) ----

auto_emision <- read_csv("consolidados/automoviles_flotilla/emision.csv.gz")
auto_siniestros <- read_csv("consolidados/automoviles_flotilla/siniestros.csv.gz")

### Causa del siniestro -----
auto_siniestro_cat <- auto_siniestros %>% 
  select(anio, `Causa del Siniestro_desc`) %>% 
  filter(!is.na(`Causa del Siniestro_desc`)) %>% 
  distinct_all()

write_csv(auto_siniestro_cat,
          "../../catalogos/CNSF/auto_flotilla_cat_siniestros.csv")

### Tipo de pérdida ----
auto_tipo_perdida_cat <- auto_siniestros %>% 
  select(anio, `Tipo de perdida_desc`) %>% 
  filter(!is.na(`Tipo de perdida_desc`)) %>% 
  distinct_all()

write_csv(auto_tipo_perdida_cat,
          "../../catalogos/CNSF/auto_flotilla_cat_tipo_perdida.csv")


### tipo cobertura ----
auto_tipo_cobertura_cat <- auto_siniestros %>% 
  select(anio, `Cobertura_desc`) %>% 
  filter(!is.na(Cobertura_desc)) %>% 
  distinct_all()

write_csv(auto_tipo_cobertura_cat,
          "../../catalogos/CNSF/auto_flotilla_cat_tipo_cobertura.csv")

### entidad ----
auto_flotilla_edo_cat <- auto_siniestros %>% 
  select(anio, Entidad_desc) %>% 
  filter(!is.na(Entidad_desc)) %>% 
  distinct_all()

write_csv(auto_flotilla_edo_cat,
          "../../catalogos/CNSF/auto_flotilla_cat_edo.csv")

## Automoviles individual ----
auto_emision <- read_csv("consolidados/automoviles_individual/emision.csv.gz")
auto_siniestros <- read_csv("consolidados/automoviles_individual/siniestros.csv.gz")

### Causa del siniestro -----
auto_siniestro_cat <- auto_siniestros %>% 
  select(anio, `Causa del siniestro_desc`) %>% 
  filter(!is.na(`Causa del siniestro_desc`)) %>% 
  distinct_all()

write_csv(auto_siniestro_cat,
          "../../catalogos/CNSF/auto_individual_cat_siniestros.csv")

### Tipo de pérdida ----
auto_tipo_perdida_cat <- auto_siniestros %>% 
  select(anio, `Tipo de Perdida_desc`) %>% 
  filter(!is.na(`Tipo de Perdida_desc`)) %>% 
  distinct_all()

write_csv(auto_tipo_perdida_cat,
          "../../catalogos/CNSF/auto_individual_cat_tipo_perdida.csv")


### tipo cobertura ----
auto_tipo_cobertura_cat <- auto_siniestros %>% 
  select(anio, Cobertura_desc) %>% 
  filter(!is.na(Cobertura_desc)) %>% 
  distinct_all()

write_csv(auto_tipo_cobertura_cat,
          "../../catalogos/CNSF/auto_individual_cat_tipo_cobertura.csv")

### entidad ----
auto_flotilla_edo_cat <- auto_siniestros %>% 
  select(anio, Entidad_desc) %>% 
  filter(!is.na(Entidad_desc)) %>% 
  distinct_all()

write_csv(auto_flotilla_edo_cat,
          "../../catalogos/CNSF/auto_individual_cat_edo.csv")


## Incendio ----

incendio_emision <- read_csv("consolidados/incendio/emision.csv.gz")
incendio_siniestros <- read_csv("consolidados/incendio/siniestros.csv.gz")


### causa del siniestro ----
incen_siniestros_cat <- incendio_siniestros %>% 
  select(anio, `CAUSA DEL SINIESTRO`) %>% 
  distinct_all()

write_csv(incen_siniestros_cat,
          "../../catalogos/CNSF/incen_cat_siniestros.csv")


### giro de la ubicacion ----
incen_giro_cat <- incendio_siniestros %>% 
  select(anio, `GIRO LA UBICACIÓN`) %>% 
  distinct_all()

write_csv(incen_giro_cat,
          "../../catalogos/CNSF/incen_cat_giro.csv")


## Hidrometeorológico ----

hidro_emision <- read_csv("consolidados/riesgos_hidrometereologicos/emision.csv.gz")
hidro_siniestros <- read_csv("consolidados/riesgos_hidrometereologicos/siniestros.csv.gz")


### causa del siniestro ----
hidro_siniestros_cat <- hidro_siniestros %>% 
  select(anio, `TIPO DE EVENTO`) %>% 
  distinct_all()

write_csv(hidro_siniestros_cat,
          "../../catalogos/CNSF/hidro_cat_siniestros.csv")


### Primera linea del mar ----
hidro_primlin_cat <- hidro_siniestros %>% 
  select(anio, `PRIMERA LÍNEA 
DE MAR`) %>% 
  distinct_all()

write_csv(hidro_primlin_cat,
          "../../catalogos/CNSF/hidro_cat_primlin.csv")

### cobertura y tipo de bien -----
hidro_cobtipbien_cat <- hidro_siniestros %>% 
  select(anio, COBERTURA, `TIPO BIEN`) %>% 
  distinct_all()

write_csv(hidro_cobtipbien_cat,
          "../../catalogos/CNSF/hidro_cat_cobert_tipobien.csv")

