"""
procesar_captura_extensos.py
============================
Procesa las CAPTURAS MANUALES ESTRUCTURADAS de los documentos extensos de CENAPRED
(2016+) y las integra a las mismas estructuras A/B que produce `procesar_cenapred.py`
para el CSV abierto 2000-2015.

Por qué captura manual estructurada (decisión documentada en fuentes/cenapred.md §6bis):
los extensos cambian de diseño año con año; un parser automático requeriría una
plantilla por año + QA visual de cada salida, con riesgo de errores SILENCIOSOS en
montos — lo peor para un dataset de calibración. La captura manual con (1) esquema
fijo, (2) procedencia por PÁGINA del PDF y (3) validación contra cifras de control
nacionales es auditable y reproducible: cualquier cifra se re-verifica en la página
citada del PDF con checksum en _procedencia.json.

Entrada:  datos/datos_CENAPRED/captura/captura_extenso_{anio}.csv
          (esquema: ver plantillas/captura_extenso_PLANTILLA.csv)
Salidas:  consolidados/impacto_estado_anio_peril_extensos.csv   (estructura A)
          consolidados/eventos_cenapred_climada_extensos.csv    (estructura B)

Reglas:
- `fenomeno_nivel1` usa la taxonomía LGPC que estructura los capítulos de los extensos:
  Geológico / Hidrometeorológico / Químico-tecnológico / Sanitario-ecológico /
  Socio-organizativo.
- El alcance climático se decide por SUBTIPO, no por capítulo: deslizamiento es
  capítulo Geológico pero detonado por lluvia (clima=sí, igual que GEO/DESLIZ en el
  CSV 2000-2015); incendio forestal es capítulo Químico-tecnológico pero clima=sí.
  COVID (Sanitario-ecológico, domina 2020) queda fuera automáticamente.
- Validación de control: la suma anual capturada se compara con CIFRAS_CONTROL
  (totales nacionales de los resúmenes); desviación > TOLERANCIA -> FALLA ruidosa.
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.extend([".", "..", str(Path(__file__).resolve().parent)])
from procesar_cenapred import (PERILS_CENAPRED, _norm, a_numero,  # noqa: E402
                               separar_estados, mapear_peril)

DIR_BASE = Path("datos/datos_CENAPRED")
DIR_CAPTURA = DIR_BASE / "captura"
DIR_CONS = DIR_BASE / "consolidados"
ARCHIVO_LOG = DIR_BASE / "_log_cenapred.log"

log = logging.getLogger("procesar_captura_extensos")

COLUMNAS_REQUERIDAS = ["anio", "fenomeno_nivel1", "subtipo_texto", "entidad",
                       "danio_mdp", "pagina_pdf"]

# Totales nacionales (MDP corrientes) de los resúmenes ejecutivos, para validar la
# captura. None = pendiente de registrar al capturar ese año (se exige completarlo).
CIFRAS_CONTROL = {
    2016: None, 2017: None, 2018: None, 2019: None,
    2020: None, 2021: None,
    2022: 16600.0,   # resumen ejecutivo 2022
    2023: 88910.0,   # resumen ejecutivo 2023 (año Otis)
    2024: 14434.0,   # resumen ejecutivo 2024
}
TOLERANCIA = 0.05  # 5%: los extensos refinan cifras preliminares del resumen

NIVEL1_VALIDOS = {"geologico", "hidrometeorologico", "quimico-tecnologico",
                  "quimico tecnologico", "sanitario-ecologico", "sanitario ecologico",
                  "socio-organizativo", "socio organizativo"}


def configurar_log():
    DIR_BASE.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(ARCHIVO_LOG, encoding="utf-8"),
                  logging.StreamHandler(sys.stdout)])


def validar_captura(df: pd.DataFrame, anio: int):
    """Validaciones ruidosas: columnas, nivel1, procedencia por página, total de control."""
    faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltan:
        raise RuntimeError(f"captura {anio}: faltan columnas {faltan}")
    malos = df[~df["fenomeno_nivel1"].map(_norm).isin(NIVEL1_VALIDOS)]
    if len(malos):
        raise RuntimeError(f"captura {anio}: fenomeno_nivel1 inválido en filas "
                           f"{malos.index.tolist()} (valores {malos['fenomeno_nivel1'].unique()})")
    sin_pagina = df[df["pagina_pdf"].isna() | (df["pagina_pdf"].astype(str).str.strip() == "")]
    if len(sin_pagina):
        raise RuntimeError(f"captura {anio}: {len(sin_pagina)} filas SIN pagina_pdf — "
                           "la procedencia por página es obligatoria")
    control = CIFRAS_CONTROL.get(anio)
    total = df["danio_mdp"].map(a_numero).sum()
    if control is None:
        log.warning("captura %d: SIN cifra de control registrada en CIFRAS_CONTROL; "
                    "total capturado = %.1f MDP. Registrar el total del resumen y re-correr.",
                    anio, total)
    else:
        desv = abs(total - control) / control
        if desv > TOLERANCIA:
            raise RuntimeError(
                f"captura {anio}: total capturado {total:,.1f} MDP difiere "
                f"{desv:.1%} de la cifra de control {control:,.1f} MDP (tolerancia "
                f"{TOLERANCIA:.0%}). Revisar captura u origen de la diferencia "
                f"(documentarla en 'notas' si es legítima, p. ej. refinación del extenso).")
        log.info("captura %d: total %.1f MDP vs control %.1f MDP (desv %.2f%%) OK",
                 anio, total, control, 100 * desv)


def procesar_capturas(dir_captura: Path = DIR_CAPTURA, dir_cons: Path = DIR_CONS):
    dir_cons.mkdir(parents=True, exist_ok=True)
    archivos = sorted(dir_captura.glob("captura_extenso_*.csv"))
    if not archivos:
        log.warning("no hay capturas en %s (esquema en plantillas/captura_extenso_PLANTILLA.csv)",
                    dir_captura)
        return None, None
    eventos = []
    for path in archivos:
        anio = int(path.stem.split("_")[-1])
        df = pd.read_csv(path, encoding="utf-8")
        validar_captura(df, anio)
        ev = pd.DataFrame()
        ev["anio"] = pd.to_numeric(df["anio"], errors="coerce").fillna(anio).astype(int)
        ev["tipo"] = df["fenomeno_nivel1"].astype(str).str.strip()
        ev["subtipo"] = df["subtipo_texto"].astype(str).str.strip()
        perils = [mapear_peril(s, t) for s, t in zip(ev["subtipo"], ev["tipo"])]
        ev["peril_canonico"] = [p for p, _ in perils]
        ev["en_alcance_climatico"] = [a for _, a in perils]
        ev["estados_lista"] = df["entidad"].map(separar_estados)
        ev["n_estados"] = ev["estados_lista"].map(len)
        ev["estados"] = ev["estados_lista"].map(lambda xs: "|".join(xs))
        ev["danio_mdp"] = df["danio_mdp"].map(a_numero)
        ev["danio_mdd"] = np.nan
        for c_src, c_dst in [("defunciones", "defunciones"), ("pob_afectada", "pob_afectada"),
                             ("nombre_evento", "nombre_evento"),
                             ("mes", "mes"), ("municipios", "municipio"),
                             ("fecha_inicio", "fecha_inicio"), ("fecha_fin", "fecha_fin"),
                             ("fecha_texto", "fecha"),  # compatibilidad con plantilla previa
                             ("pagina_pdf", "pagina_pdf"), ("notas", "descripcion")]:
            ev[c_dst] = df[c_src] if c_src in df.columns else np.nan
        ev["fuente"] = f"CENAPRED extenso {anio} (captura manual validada)"
        ev["evento_id"] = [f"CENX-{anio}-{i:04d}" for i in range(1, len(ev) + 1)]
        eventos.append(ev)
        log.info("captura %d: %d eventos integrados", anio, len(ev))
    todo = pd.concat(eventos, ignore_index=True)

    # Estructura B (eventos; multi-estado conservado como un registro)
    cols_b = ["evento_id", "nombre_evento", "anio", "mes",
              "fecha_inicio", "fecha_fin", "tipo", "subtipo",
              "peril_canonico", "en_alcance_climatico", "estados", "n_estados",
              "municipio", "danio_mdp", "danio_mdd", "defunciones", "pob_afectada",
              "fuente", "pagina_pdf", "descripcion"]
    salida_b = dir_cons / "eventos_cenapred_climada_extensos.csv"
    todo[cols_b].to_csv(salida_b, index=False)

    # Estructura A (panel; solo un-estado, multi-estado no se reparte)
    un_estado = todo[todo["n_estados"] == 1].copy()
    un_estado["entidad"] = un_estado["estados_lista"].map(lambda xs: xs[0])
    panel = (un_estado.groupby(["entidad", "anio", "peril_canonico",
                                "en_alcance_climatico"], dropna=False)
             .agg(n_eventos=("evento_id", "size"), danio_mdp=("danio_mdp", "sum"),
                  defunciones=("defunciones", "sum"), pob_afectada=("pob_afectada", "sum"))
             .reset_index().sort_values(["entidad", "anio", "peril_canonico"]))
    salida_a = dir_cons / "impacto_estado_anio_peril_extensos.csv"
    panel.to_csv(salida_a, index=False)

    multi = todo[todo["n_estados"] >= 2]
    log.info("[A] panel extensos: %d filas -> %s | [B] eventos: %d -> %s | "
             "multi-estado (no repartidos, solo en B): %d",
             len(panel), salida_a, len(todo), salida_b, len(multi))
    return panel, todo


if __name__ == "__main__":
    configurar_log()
    procesar_capturas()
