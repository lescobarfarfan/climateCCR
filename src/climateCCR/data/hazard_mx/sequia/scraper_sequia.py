#!/usr/bin/env python3
"""
scraper_sequia.py
=================
Orquestador del pipeline de sequía para la tesis de atribución climática.

Encadena (modo "todo"):
    descargar  -> crudos ERA5 (P, PET, ensemble) recortados a México + benchmark oficial
    calcular   -> SPI y SPEI propios, por escala y por periodo de referencia
    agregar    -> media ponderada por área a nivel estatal
    validar    -> compara el SPI/SPEI propio (1991-2020) contra ERA5-Drought oficial

Diseño y referencias completas: README_sequia.md.

NOTA de entorno: la descarga usa la API del CDS (cdsapi) y requiere ~/.cdsapirc.
El CDS no es alcanzable desde el sandbox; las descargas se validan en la máquina
del usuario (igual que cnsf.gob.mx). El resto de modos corre sin red.

Patrón de robustez (logging, reintentos, sesión) siguiendo el scraper SIAP.
"""

from __future__ import annotations
import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import config_sequia as cfg
import indices_sequia as ix
import agregacion_sequia as ag

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("sequia.scraper")


# --------------------------------------------------------------------------- #
# Procedencia / reproducibilidad (mismo patrón que CNSF/CENAPRED, ampliado para CDS).
# --------------------------------------------------------------------------- #
def _sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def registrar_procedencia(dir_destino: Path, archivo: Path, *, dataset: str,
                          request: dict, version: str | None = None,
                          doi: str | None = None) -> None:
    """Anexa una entrada de procedencia a _procedencia.json en el directorio.

    Guarda, además del sha256/bytes/fecha, el REQUEST exacto del CDS, su versión y
    DOI: con eso la descarga es 100% reconstruible.
    """
    ruta_proc = dir_destino / cfg.ARCHIVO_PROCEDENCIA
    registro = {
        "archivo": archivo.name,
        "dataset_cds": dataset,
        "version": version,
        "doi": doi,
        "request": request,
        "sha256": _sha256(archivo),
        "bytes": archivo.stat().st_size,
        "fecha_descarga_utc": datetime.now(timezone.utc).isoformat(),
    }
    existentes = []
    if ruta_proc.exists():
        existentes = json.loads(ruta_proc.read_text(encoding="utf-8"))
    # Reemplaza si ya había un registro del mismo archivo (re-descarga).
    existentes = [r for r in existentes if r.get("archivo") != archivo.name]
    existentes.append(registro)
    ruta_proc.write_text(json.dumps(existentes, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    log.info("Procedencia registrada: %s (sha256=%s...)", archivo.name,
             registro["sha256"][:12])


# --------------------------------------------------------------------------- #
# Verificación de integridad contra _procedencia.json (sin red), igual que el
# modo 'verificar' de CENAPRED: compara sha256/bytes de disco vs lo almacenado.
# Estados: ok | cambiado | sin_procedencia | falta.
# --------------------------------------------------------------------------- #
def _cargar_indice_procedencia(dir_crudos: Path) -> dict:
    ruta = dir_crudos / cfg.ARCHIVO_PROCEDENCIA
    if not ruta.exists():
        return {}
    try:
        registros = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {r.get("archivo"): r for r in registros}


def _estado_integridad(destino: Path, indice_proc: dict) -> tuple[str, str]:
    if not destino.exists():
        return "falta", "no está en disco"
    rec = indice_proc.get(destino.name)
    if not rec:
        # La procedencia se escribe SOLO tras una descarga exitosa; un archivo sin
        # registro suele ser una descarga interrumpida (parcial).
        return "sin_procedencia", "existe pero sin registro (posible descarga parcial)"
    if rec.get("bytes") != destino.stat().st_size:
        return "cambiado", f"bytes {destino.stat().st_size} != procedencia {rec.get('bytes')}"
    if rec.get("sha256") != _sha256(destino):
        return "cambiado", "sha256 no coincide con procedencia"
    return "ok", "íntegro (sha256 + bytes coinciden con procedencia)"


# --------------------------------------------------------------------------- #
# Planificación de descargas (compartida por 'verificar' y 'descargar' para que
# nunca se desincronicen). Devuelve lista de descargas como dicts.
# --------------------------------------------------------------------------- #
def _planificar_descargas(args, dir_crudos: Path) -> list[dict]:
    anios = [str(a) for a in range(args.anio_inicial, args.anio_final + 1)]
    meses = [f"{m:02d}" for m in range(1, 13)]
    # El producto oficial 'consolidated' va 2-3 meses detrás: no pedir el año en curso.
    anio_tope_oficial = min(args.anio_final, datetime.now().year - 1)
    anios_oficial = [str(a) for a in range(args.anio_inicial, anio_tope_oficial + 1)]
    plan = []

    # 1) Crudos ERA5 (CRÍTICO: de esto depende todo el cálculo).
    plan.append({
        "etiqueta": "crudo_era5", "critico": True,
        "dataset": cfg.CDS_DATASET_CRUDO,
        "request": {
            "product_type": cfg.CDS_PRODUCT_TYPE_CRUDO,
            "variable": cfg.VARIABLES_ERA5,
            "year": anios, "month": meses, "time": "00:00",
            "area": cfg.BBOX_CDS_AREA, "data_format": "netcdf",
        },
        "destino": dir_crudos / f"era5_p_pet_mexico_{args.anio_inicial}_{args.anio_final}.nc",
        "version": None, "doi": None,
    })

    # 2) Benchmark oficial ERA5-Drought (NO crítico: solo sirve para 'validar').
    for codigo, indice_oficial in [
            ("spi", "standardised_precipitation_index"),
            ("spei", "standardised_precipitation_evapotranspiration_index")]:
        plan.append({
            "etiqueta": f"benchmark_{codigo}", "critico": False,
            "dataset": cfg.CDS_DATASET_OFICIAL,
            "request": {
                "variable": [indice_oficial],
                "accumulation_period": [str(n) for n in args.escalas],
                "version": cfg.CDS_VERSION_OFICIAL,
                "product_type": [cfg.CDS_PRODUCT_TYPE_OFICIAL],
                "dataset_type": cfg.CDS_DATASET_TYPE_OFICIAL,
                "year": anios_oficial, "month": meses, "area": cfg.BBOX_CDS_AREA,
            },
            "destino": dir_crudos / f"era5drought_{codigo}_oficial.nc",
            "version": cfg.CDS_VERSION_OFICIAL, "doi": cfg.CDS_DOI_OFICIAL,
        })
    return plan


# --------------------------------------------------------------------------- #
# MODO: verificar (pre-vuelo). Revisa config CDS y LISTA lo que se descargaría,
# sin bajar nada. Análogo al modo 'verificar' del scraper CNSF.
# OJO: distinto de 'validar' (que compara el índice propio vs el oficial tras
# el cálculo). 'verificar' es el primer paso recomendado antes de 'descargar'.
# --------------------------------------------------------------------------- #
def modo_verificar(args, raiz: Path):
    dir_crudos = raiz / cfg.DIR_CRUDOS
    dir_crudos.mkdir(parents=True, exist_ok=True)

    log.info("== 1) Configuración del CDS ==")
    rc = Path.home() / ".cdsapirc"
    if rc.exists():
        url = next((ln.split(":", 1)[1].strip() for ln in rc.read_text().splitlines()
                    if ln.strip().startswith("url")), "(sin url)")
        log.info(".cdsapirc encontrado: %s | url=%s | key=(oculta)", rc, url)
    else:
        log.warning(".cdsapirc NO encontrado en %s. Crear con url+key del CDS "
                    "(https://cds.climate.copernicus.eu/how-to-api).", rc)
    try:
        import cdsapi
        try:
            cdsapi.Client()
            log.info("cdsapi instalado e inicializado correctamente.")
        except Exception as e:
            log.warning("cdsapi instalado pero la config no es válida: %s", e)
    except ImportError:
        log.warning("cdsapi NO instalado. Ejecuta: pip install cdsapi")

    log.info("== 2) Estado de los archivos vs procedencia (sin red) ==")
    plan = _planificar_descargas(args, dir_crudos)
    indice_proc = _cargar_indice_procedencia(dir_crudos)
    pendientes = []
    for d in plan:
        estado, detalle = _estado_integridad(d["destino"], indice_proc)
        anios_req = d["request"].get("year", [])
        rango = f"{anios_req[0]}-{anios_req[-1]}" if anios_req else "?"
        log.info("[%s] %s | años=%s -> %s (%s)", d["etiqueta"], d["destino"].name,
                 rango, estado.upper(), detalle)
        log.info("      request=%s", json.dumps(d["request"], ensure_ascii=False))
        if estado != "ok":
            pendientes.append(f"{d['etiqueta']}({estado})")
    if pendientes:
        log.info("Para 'descargar' (faltan/cambiaron/sin verificar): %s", ", ".join(pendientes))
    else:
        log.info("Todo íntegro y verificado: 'descargar' no bajaría nada (salvo --forzar).")

    log.info("== 3) Procedencia / logs previos ==")
    proc = dir_crudos / cfg.ARCHIVO_PROCEDENCIA
    if proc.exists():
        n = len(json.loads(proc.read_text(encoding="utf-8")))
        log.info("%s existe (%d registro[s]). Ya hubo descargas previas.", proc.name, n)
    else:
        log.info("%s no existe: es la primera descarga (correr --modo descargar).",
                 cfg.ARCHIVO_PROCEDENCIA)


# --------------------------------------------------------------------------- #
# MODO: descargar (CDS). No testeable en sandbox; correr en la máquina del usuario.
# --------------------------------------------------------------------------- #
def _es_error_cliente(e: Exception) -> bool:
    """True si el error es 4xx / 'invalid request' (no tiene caso reintentar)."""
    s = str(e).lower()
    return ("invalid request" in s or "400 client error" in s
            or "403 client error" in s or "404 client error" in s
            or "not produced a valid combination" in s)


def _cdsapi_con_reintentos(dataset, request, destino: Path, intentos=4):
    import cdsapi  # import diferido: el resto del pipeline no depende de cdsapi
    cliente = cdsapi.Client()
    for k in range(1, intentos + 1):
        try:
            cliente.retrieve(dataset, request).download(str(destino))
            return
        except Exception as e:
            if _es_error_cliente(e):  # 4xx: el request es inválido, reintentar no ayuda
                raise RuntimeError(
                    f"Request inválido para {dataset} (error de cliente, sin reintentos): {e}")
            espera = 2 ** k  # solo reintenta errores transitorios (red, 5xx, timeouts)
            log.warning("Descarga falló (intento %d/%d): %s. Reintento en %ds.",
                        k, intentos, e, espera)
            time.sleep(espera)
    raise RuntimeError(f"Descarga agotó reintentos: {dataset}")


def modo_descargar(args, raiz: Path):
    dir_crudos = raiz / cfg.DIR_CRUDOS
    dir_crudos.mkdir(parents=True, exist_ok=True)
    indice_proc = _cargar_indice_procedencia(dir_crudos)
    fallos = []
    for d in _planificar_descargas(args, dir_crudos):
        # Salta SOLO si el archivo está verificado e íntegro contra procedencia
        # (estilo 'sync' de CENAPRED). Re-baja lo faltante, cambiado o parcial.
        estado, detalle = _estado_integridad(d["destino"], indice_proc)
        if estado == "ok" and not args.forzar:
            log.info("[%s] %s íntegro vs procedencia; se omite.",
                     d["etiqueta"], d["destino"].name)
            continue
        if estado in ("cambiado", "sin_procedencia"):
            log.warning("[%s] %s: %s -> se re-descarga.",
                        d["etiqueta"], d["destino"].name, detalle)
        log.info("Descargando [%s] -> %s", d["etiqueta"], d["destino"].name)
        try:
            _cdsapi_con_reintentos(d["dataset"], d["request"], d["destino"])
            registrar_procedencia(dir_crudos, d["destino"], dataset=d["dataset"],
                                  request=d["request"], version=d["version"], doi=d["doi"])
        except Exception as e:
            if d["critico"]:
                log.error("Fallo en descarga CRÍTICA [%s]; se aborta. %s", d["etiqueta"], e)
                raise
            # No crítico (benchmark): se registra y se continúa; 'validar' lo saltará.
            log.warning("Fallo en descarga NO crítica [%s]; se continúa sin ella. %s",
                        d["etiqueta"], e)
            fallos.append(d["etiqueta"])
    if fallos:
        log.warning("Descarga completa con %d benchmark(s) faltante(s): %s. "
                    "Los crudos están listos; 'calcular' y 'agregar' pueden proceder; "
                    "'validar' omitirá lo faltante.", len(fallos), ", ".join(fallos))
    else:
        log.info("Descarga completa.")


# --------------------------------------------------------------------------- #
# Localiza una entrada del plan por su etiqueta canónica (crudo_era5,
# benchmark_spi, benchmark_spei). Evita rutas/nombres libres que el pipeline
# luego no reconoce.
# --------------------------------------------------------------------------- #
def _entrada_plan(args, dir_crudos: Path, objetivo: str):
    plan = _planificar_descargas(args, dir_crudos)
    for d in plan:
        if d["etiqueta"] == objetivo:
            return d
    log.error("--objetivo '%s' no válido. Opciones: %s",
              objetivo, ", ".join(d["etiqueta"] for d in plan))
    return None


# --------------------------------------------------------------------------- #
# MODO: recuperar. Descarga UN resultado del CDS por su request_id (un job ya
# enviado, p. ej. uno que quedó "accepted" y se cortó), y NADA MÁS. No re-envía
# el request: se reengancha al job existente en el servidor.
# Usa --objetivo {crudo_era5|benchmark_spi|benchmark_spei} para que el archivo
# caiga con el NOMBRE CANÓNICO y la PROCEDENCIA COMPLETA que el resto del
# pipeline reconoce (evita el problema de nombres libres + renombrado a mano).
# --------------------------------------------------------------------------- #
def modo_recuperar(args, raiz: Path):
    if not args.request_id:
        log.error("Falta --request-id (el 'Request ID is ...' de la consola/bitácora).")
        sys.exit(1)
    dir_crudos = raiz / cfg.DIR_CRUDOS
    dir_crudos.mkdir(parents=True, exist_ok=True)

    # Resolver destino + metadatos de procedencia. Preferir --objetivo (canónico).
    if args.objetivo:
        entrada = _entrada_plan(args, dir_crudos, args.objetivo)
        if entrada is None:
            sys.exit(1)
        destino = entrada["destino"]
        meta = {"dataset": entrada["dataset"],
                "request": {**entrada["request"], "_request_id_recuperado": args.request_id},
                "version": entrada["version"], "doi": entrada["doi"]}
        if args.destino:
            log.warning("Se ignora --destino: --objetivo fija el nombre canónico %s.",
                        destino.name)
    elif args.destino:
        destino = Path(args.destino)
        if not destino.is_absolute():
            destino = raiz / destino
        meta = {"dataset": "(recuperado por request_id)",
                "request": {"request_id": args.request_id}, "version": None, "doi": None}
        log.warning("Sin --objetivo: si el nombre no es canónico, 'verificar'/'descargar' "
                    "NO lo reconocerán. Recomendado: --objetivo "
                    "{crudo_era5|benchmark_spi|benchmark_spei}.")
    else:
        log.error("Falta --objetivo (recomendado) o --destino.")
        sys.exit(1)
    destino.parent.mkdir(parents=True, exist_ok=True)

    try:
        import cdsapi
    except ImportError:
        log.error("cdsapi no está instalado. Ejecuta: pip install cdsapi")
        sys.exit(1)
    log.info("Recuperando job %s -> %s", args.request_id, destino.name)
    cliente = cdsapi.Client()
    try:
        remoto = cliente.client.get_remote(args.request_id)
    except Exception as e:
        if _es_error_cliente(e):
            log.error("Job %s no encontrado (¿ID incorrecto o expiró de la caché?). %s",
                      args.request_id, e)
        else:
            log.error("Error al consultar el job %s: %s", args.request_id, e)
        sys.exit(1)

    estado = getattr(remoto, "status", None)
    if estado:
        log.info("Estado del job: %s", estado)
        if str(estado).lower() in ("failed", "deleted"):
            log.error("El job está en estado '%s'; no se puede descargar.", estado)
            sys.exit(1)
    try:
        remoto.download(str(destino))  # si aún no está listo, espera a que lo esté
    except Exception as e:
        log.error("Falló la descarga del job %s: %s", args.request_id, e)
        sys.exit(1)

    registrar_procedencia(destino.parent, destino, dataset=meta["dataset"],
                          request=meta["request"], version=meta["version"], doi=meta["doi"])
    log.info("Recuperación completa: %s (procedencia registrada).", destino.name)


# --------------------------------------------------------------------------- #
# MODO: registrar. Adopta en la procedencia un archivo que YA está en disco y
# completo, bajo su nombre canónico (--objetivo), SIN red. Útil cuando un archivo
# se recuperó/renombró a mano y quedó como SIN_PROCEDENCIA. El usuario afirma que
# el archivo está completo; se calcula su sha256/bytes y se escribe el registro.
# --------------------------------------------------------------------------- #
def modo_registrar(args, raiz: Path):
    if not args.objetivo:
        log.error("Falta --objetivo {crudo_era5|benchmark_spi|benchmark_spei} para registrar.")
        sys.exit(1)
    dir_crudos = raiz / cfg.DIR_CRUDOS
    entrada = _entrada_plan(args, dir_crudos, args.objetivo)
    if entrada is None:
        sys.exit(1)
    destino = entrada["destino"]
    if not destino.exists():
        log.error("No existe %s; nada que registrar. Descárgalo (descargar) o "
                  "recupéralo (recuperar --objetivo %s) primero.",
                  destino.name, args.objetivo)
        sys.exit(1)

    log.info("Adoptando %s como '%s' (sin red; se confía en que está completo).",
             destino.name, args.objetivo)
    req = {**entrada["request"], "_origen": "adoptado_local"}
    if args.request_id:
        req["_request_id_recuperado"] = args.request_id
    registrar_procedencia(dir_crudos, destino, dataset=entrada["dataset"],
                          request=req, version=entrada["version"], doi=entrada["doi"])
    estado, detalle = _estado_integridad(destino, _cargar_indice_procedencia(dir_crudos))
    log.info("Estado tras registrar: %s (%s)", estado.upper(), detalle)


# --------------------------------------------------------------------------- #
# Lectura y normalización de unidades de los crudos ERA5.
# --------------------------------------------------------------------------- #
def _abrir_crudos(ruta_nc: Path):
    """Devuelve (P_mm, PET_mm, lats, lons, anios, meses, miembros).

    Normaliza unidades a mm/mes y signo de PET (positivo = demanda).
    VERIFICACIÓN: ERA5 entrega tp/pev en m; pev es negativa (convención descendente).
    Las conversiones se registran en log para revisión manual (verification-first).
    """
    import xarray as xr
    ds = xr.open_dataset(ruta_nc)
    nombres = {v.lower(): v for v in ds.data_vars}
    var_tp = nombres.get("tp", "tp")
    var_pev = nombres.get("pev", "pev")

    tp = ds[var_tp]
    pev = ds[var_pev]
    # m -> mm. Sanity-check de magnitud (log para revisión).
    P = tp * 1000.0
    PET = np.abs(pev) * 1000.0   # |pev|: ERA5 reporta pev <= 0
    log.info("Rango P (mm/mes): [%.1f, %.1f]; PET (mm/mes): [%.1f, %.1f] -> revisar",
             float(P.min()), float(P.max()), float(PET.min()), float(PET.max()))

    tiempo = ds["valid_time"] if "valid_time" in ds else ds["time"]
    anios = tiempo.dt.year.values
    meses = tiempo.dt.month.values
    lats = ds["latitude"].values
    lons = ds["longitude"].values
    dim_miembro = "number" if "number" in P.dims else None
    return P, PET, lats, lons, anios, meses, dim_miembro, ds


# --------------------------------------------------------------------------- #
# MODO: calcular (SPI/SPEI propios en malla, por escala y periodo).
# --------------------------------------------------------------------------- #
def modo_calcular(args, raiz: Path):
    import xarray as xr
    dir_crudos = raiz / cfg.DIR_CRUDOS
    dir_cons = raiz / cfg.DIR_CONSOLIDADOS
    dir_cons.mkdir(parents=True, exist_ok=True)
    ruta_nc = next(dir_crudos.glob("era5_p_pet_mexico_*.nc"), None)
    if ruta_nc is None:
        log.error("No hay crudo ERA5 en %s. Corre primero --modo descargar.", dir_crudos)
        sys.exit(1)

    P, PET, lats, lons, anios, meses, dim_miembro, ds = _abrir_crudos(ruta_nc)
    miembros = ds[dim_miembro].values if dim_miembro else [0]
    tiempo = (ds["valid_time"] if "valid_time" in ds else ds["time"]).values

    for nombre_periodo in args.periodos_referencia:
        ini, fin = cfg.PERIODOS_REFERENCIA[nombre_periodo]
        for n in args.escalas:
            for tipo in args.indices:
                log.info("Calculando %s-%d | ref %s | %d miembro(s)...",
                         tipo.upper(), n, nombre_periodo, len(miembros))
                campo = _calcular_grid(P, PET, lats, lons, anios, meses,
                                       n, ini, fin, tipo, dim_miembro, miembros)
                da = xr.DataArray(
                    campo, dims=("number", "time", "latitude", "longitude"),
                    coords={"number": list(miembros), "time": tiempo,
                            "latitude": lats, "longitude": lons},
                    name=f"{tipo}_{n}",
                    attrs={"periodo_referencia": nombre_periodo,
                           "escala_meses": n, "distribucion":
                           cfg.DIST_SPI if tipo == "spi" else cfg.DIST_SPEI})
                salida = dir_cons / f"{tipo}{n}_ref{nombre_periodo}.nc"
                da.to_netcdf(salida)
                log.info("  -> %s", salida.name)


def _calcular_grid(P, PET, lats, lons, anios, meses, n, ini, fin, tipo,
                   dim_miembro, miembros):
    """Aplica SPI/SPEI celda por celda y miembro por miembro. Devuelve
    arreglo (miembro, tiempo, lat, lon). Salta celdas totalmente NaN (océano)."""
    nt = len(anios); nla = len(lats); nlo = len(lons); nm = len(miembros)
    salida = np.full((nm, nt, nla, nlo), np.nan, dtype="float32")
    for im, miembro in enumerate(miembros):
        if dim_miembro:
            p_m = P.isel({dim_miembro: im}).values
            pet_m = PET.isel({dim_miembro: im}).values
        else:
            p_m = P.values; pet_m = PET.values
        for i in range(nla):
            for j in range(nlo):
                serie_p = p_m[:, i, j]
                if not np.isfinite(serie_p).any():
                    continue
                if tipo == "spi":
                    z = ix.spi_serie(serie_p, anios, meses, n, ini, fin)
                else:
                    z = ix.spei_serie(serie_p, pet_m[:, i, j], anios, meses,
                                      n, ini, fin)
                salida[im, :, i, j] = z
    return salida


# --------------------------------------------------------------------------- #
# MODO: agregar (malla -> estatal, ponderado por área).
# --------------------------------------------------------------------------- #
def modo_agregar(args, raiz: Path):
    import xarray as xr
    import pandas as pd
    import geopandas as gpd
    dir_cons = raiz / cfg.DIR_CONSOLIDADOS
    if not args.shp_estados:
        log.error("Falta --shp-estados (Marco Geoestadístico INEGI, 32 entidades).")
        sys.exit(1)
    estados = gpd.read_file(args.shp_estados)

    filas = []
    W = claves = None
    import warnings
    for ruta in sorted(dir_cons.glob("*.nc")):
      with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        da = xr.open_dataarray(ruta)
        lats = da["latitude"].values; lons = da["longitude"].values
        # Media (central) y sd (incertidumbre) sobre miembros del ensemble.
        with np.errstate(invalid="ignore"):
            media = da.mean("number"); sd = da.std("number")
        if W is None:  # matriz de pesos: se construye UNA sola vez (malla fija)
            mascara = np.isfinite(media.values).any(axis=0)  # celdas con dato
            W, claves, _ = ag.construir_matriz_pesos(lats, lons, estados, mascara)
        # Agregación de TODO el stack temporal con un producto matriz.
        agr_m = ag.agregar_stack(media.values, W)   # (T, n_estados)
        agr_s = ag.agregar_stack(sd.values, W)
        fechas = [str(t)[:10] for t in da["time"].values]
        for it, fecha in enumerate(fechas):
            for r, clave in enumerate(claves):
                filas.append({"fecha": fecha, "cve_ent": clave, "indice": da.name,
                              "periodo_referencia": da.attrs.get("periodo_referencia"),
                              "valor_medio": agr_m[it, r],
                              "incertidumbre_sd": agr_s[it, r]})
    df = pd.DataFrame(filas)
    salida_csv = dir_cons / "panel_sequia_estatal.csv"
    df.to_csv(salida_csv, index=False)
    try:
        df.to_parquet(dir_cons / "panel_sequia_estatal.parquet", index=False)
    except Exception as e:
        log.warning("No se pudo escribir parquet (%s); quedó el CSV.", e)
    log.info("Panel estatal consolidado -> %s (%d filas)", salida_csv.name, len(df))


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def construir_parser():
    p = argparse.ArgumentParser(description="Pipeline de sequía ERA5 -> SPI/SPEI -> estatal.")
    p.add_argument("--modo", required=True,
                   choices=["verificar", "descargar", "recuperar", "registrar",
                            "calcular", "agregar", "validar", "todo"])
    p.add_argument("--raiz", default=".", help="Raíz del proyecto (contiene datos/).")
    p.add_argument("--anio-inicial", type=int, default=cfg.ANIO_INICIAL_DEFECTO)
    p.add_argument("--anio-final", type=int, default=datetime.now().year - 1)
    p.add_argument("--indices", nargs="+", default=["spi", "spei"],
                   choices=["spi", "spei"])
    p.add_argument("--escalas", nargs="+", type=int, default=cfg.ESCALAS_BASE)
    p.add_argument("--escalas-extra", action="store_true",
                   help="Añade las escalas opcionales (1, 48) al set base.")
    p.add_argument("--periodos-referencia", nargs="+",
                   default=list(cfg.PERIODOS_REFERENCIA.keys()),
                   choices=list(cfg.PERIODOS_REFERENCIA.keys()))
    p.add_argument("--forzar", action="store_true",
                   help="Re-descarga aunque el archivo ya exista (por defecto se omite).")
    p.add_argument("--shp-estados", help="Ruta al shapefile estatal (INEGI).")
    p.add_argument("--request-id",
                   help="ID de un job del CDS ya enviado (modos recuperar/registrar).")
    p.add_argument("--objetivo", choices=["crudo_era5", "benchmark_spi", "benchmark_spei"],
                   help="Objetivo canónico a recuperar/registrar; fija nombre y procedencia "
                        "correctos (recomendado sobre --destino).")
    p.add_argument("--destino",
                   help="Ruta de salida libre para 'recuperar' (relativa a --raiz si no es "
                        "absoluta). Solo si NO usas --objetivo; ojo: un nombre no canónico "
                        "no será reconocido por verificar/descargar.")
    return p


def _configurar_log_archivo(raiz: Path) -> Path:
    """Anexa un FileHandler a la bitácora persistente en datos/datos_sequia/.

    Se engancha al logger raíz para capturar también los mensajes de cdsapi/ecmwf
    durante las descargas. Mismo patrón que el scraper de CENAPRED.
    """
    dir_sequia = raiz / cfg.DIR_SEQUIA
    dir_sequia.mkdir(parents=True, exist_ok=True)
    ruta = dir_sequia / cfg.ARCHIVO_LOG
    raiz_log = logging.getLogger()
    ya = any(isinstance(h, logging.FileHandler)
             and getattr(h, "baseFilename", "") == str(ruta) for h in raiz_log.handlers)
    if not ya:
        fh = logging.FileHandler(ruta, mode="a", encoding="utf-8")
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        raiz_log.addHandler(fh)
    return ruta


def main(argv=None):
    args = construir_parser().parse_args(argv)
    if args.escalas_extra:
        args.escalas = sorted(set(args.escalas) | set(cfg.ESCALAS_EXTRA))
    raiz = Path(args.raiz).resolve()
    ruta_log = _configurar_log_archivo(raiz)
    log.info("==================== Nueva ejecución %s ====================",
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("Modo=%s | escalas=%s | periodos=%s | indices=%s | años=%s-%s",
             args.modo, args.escalas, args.periodos_referencia, args.indices,
             args.anio_inicial, args.anio_final)
    log.info("Bitácora persistente: %s", ruta_log)

    try:
        if args.modo == "verificar":
            modo_verificar(args, raiz)
        if args.modo == "recuperar":
            modo_recuperar(args, raiz)
        if args.modo == "registrar":
            modo_registrar(args, raiz)
        if args.modo in ("descargar", "todo"):
            modo_descargar(args, raiz)
        if args.modo in ("calcular", "todo"):
            modo_calcular(args, raiz)
        if args.modo in ("agregar", "todo"):
            modo_agregar(args, raiz)
        if args.modo in ("validar", "todo"):
            import validacion_sequia
            validacion_sequia.validar(args, raiz)
        log.info("Ejecución finalizada correctamente (modo=%s).", args.modo)
    except Exception:
        log.exception("La ejecución terminó con error (modo=%s).", args.modo)
        raise


if __name__ == "__main__":
    main()
