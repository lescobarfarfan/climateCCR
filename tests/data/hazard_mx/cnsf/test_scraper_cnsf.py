"""Pruebas de parseo del scraper CNSF (sin red, con fixtures realistas)."""

from scraper_cnsf import Categoria, _normalizar_url, descubrir_categorias, listar_archivos

B = "https://www.cnsf.gob.mx"
PRE = "/EntidadesSupervisadas/InstitucionesSociedadesMutualistas"

# --- Fixture índice: imita DetalladaSeguros.aspx (con chrome de SharePoint) ---
HTML_INDICE = f"""
<html><body>
  <a href="{B}{PRE}/_layouts/15/Authenticate.aspx?Source=x">Inicio de sesión</a>
  <a href="{B}{PRE}/Paginas/Vida.aspx">Vida</a>
  <a href="{B}{PRE}/Paginas/AgricolayAnimales.aspx">Agrícola y Animales</a>
  <a href="{B}{PRE}/Paginas/RiesgosHidrometeorologicos.aspx">Riesgos Hidrometereológicos</a>
  <a href="{B}{PRE}/Paginas/Diversos.aspx">Diversos</a>
  <a href="{B}{PRE}/Paginas/DetalladaSeguros.aspx">índice (debe ignorarse)</a>
  <a href="https://www.gob.mx/cnsf">otro sitio (ignorar)</a>
</body></html>
"""


# --- Fixture categoría: imita la tabla agrupada con ruido de postbacks ---
def _fila(anio, tam, carpeta, nombre):
    href = f"{B}{PRE}/{carpeta}/{nombre}"
    icon = "icxlsx.png" if nombre.lower().endswith("xlsx") else "icxls.png"
    return f"""
      <tr>
        <td>{anio}</td>
        <td>{tam} KB</td>
        <td><a href="{href}"><img src="{B}/_layouts/images/{icon}" title="{nombre}"></a></td>
      </tr>"""


HTML_AGRICOLA = f"""
<html><body>
 <table>
  <tr>
    <th><a href="javascript: __doPostBack('ctl00$ctl37$g_abc$ctl02','dvt_sortfield=Title')">
      Título</a></th>
    <th><a href="javascript: __doPostBack('ctl00$ctl37$g_abc$ctl02',
      'dvt_sortfield=FileSizeDisplay')">Tamaño</a></th>
    <th>Tipo</th>
  </tr>
  <tr><td colspan="3"><a href="javascript:">Agrícola y de Animales : Bases (5)</a></td></tr>
  {_fila(2024, 544, "AyA Bases", "2024 Agricola Bases.xlsx")}
  {_fila(2023, 584, "AyA Bases", "2023 Agricola Bases.xlsx")}
  {_fila(2015, 629, "AyA Bases", "2015 Agricola Bases.xlsx")}
  {_fila(2014, 1286, "AyA Bases", "2014 Agricola Bases.xls")}
  {_fila(2008, 944, "AyA Bases", "2008 Agricola Bases.xls")}
 </table>
 <!-- ruido: plantillas de menú contextual de SharePoint -->
 <a href="javascript:(function(){{}})()">Ver en el explorador</a>
 <a href="{B}{PRE}/Paginas/AgricolayAnimales.aspx">Self link aspx (ignorar)</a>
</body></html>
"""


def test_indice():
    cats = descubrir_categorias(None, html=HTML_INDICE)
    nombres = [c.nombre for c in cats]
    slugs = [c.slug for c in cats]
    assert nombres == [
        "Vida",
        "Agrícola y Animales",
        "Riesgos Hidrometereológicos",
        "Diversos",
    ], nombres
    assert "agricola_y_animales" in slugs
    assert all("detalladaseguros" not in c.url.lower() for c in cats)
    assert all("authenticate" not in c.url.lower() for c in cats)
    print("OK indice:", slugs)


def test_listado():
    cat = Categoria(nombre="Agrícola y Animales", url=f"{B}{PRE}/Paginas/AgricolayAnimales.aspx")
    arch = listar_archivos(None, cat, html=HTML_AGRICOLA)
    assert len(arch) == 5, f"esperaba 5, obtuve {len(arch)}: {[a.nombre_archivo for a in arch]}"
    # Orden por año desc
    assert [a.anio for a in arch] == [2024, 2023, 2015, 2014, 2008]
    # Extensiones mixtas
    assert arch[0].ext == ".xlsx" and arch[3].ext == ".xls"
    # Tamaño parseado (con coma de miles)
    assert arch[3].tamano_kb == 1286.0, arch[3].tamano_kb
    # URL codificada (espacios -> %20) y absoluta
    assert arch[0].url == f"{B}{PRE}/AyA%20Bases/2024%20Agricola%20Bases.xlsx", arch[0].url
    # Nombre decodificado conserva espacios
    assert arch[0].nombre_archivo == "2024 Agricola Bases.xlsx"
    # Ruta relativa de guardado
    assert str(arch[0].ruta_relativa()) == "agricola_y_animales/2024 Agricola Bases.xlsx"
    print("OK listado:", [(a.anio, a.ext, a.tamano_kb) for a in arch])


def test_normalizar_url():
    # No debe doble-codificar si ya viene con %20
    u = _normalizar_url(f"{PRE}/AyA%20Bases/2024%20Agricola%20Bases.xlsx")
    assert u == f"{B}{PRE}/AyA%20Bases/2024%20Agricola%20Bases.xlsx", u
    # Debe codificar espacios literales
    u2 = _normalizar_url(f"{PRE}/Riesgos Hidro Bases/2024 Hidro Bases.xlsx")
    assert "%20" in u2 and " " not in u2, u2
    print("OK normalizar_url")


if __name__ == "__main__":
    test_indice()
    test_listado()
    test_normalizar_url()
    print("\nTODAS LAS PRUEBAS PASARON")
