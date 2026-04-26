import re
import streamlit as st
import pandas as pd
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP


# =====================================================
# 1. PARÁMETROS SII 2025
# =====================================================

TASA_HONORARIOS = Decimal("0.145")
TASA_PRESTAMO_3 = Decimal("0.03")

ANIO_COMERCIAL = 2025
ANIO_TRIBUTARIO = 2026

factores_actualizacion = {
    1: Decimal("1.036"),
    2: Decimal("1.026"),
    3: Decimal("1.022"),
    4: Decimal("1.016"),
    5: Decimal("1.014"),
    6: Decimal("1.012"),
    7: Decimal("1.017"),
    8: Decimal("1.008"),
    9: Decimal("1.007"),
    10: Decimal("1.003"),
    11: Decimal("1.003"),
    12: Decimal("1.000"),
}

meses_dict = {
    1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR",
    5: "MAY", 6: "JUN", 7: "JUL", 8: "AGO",
    9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC",
}


# =====================================================
# 2. FUNCIONES AUXILIARES
# =====================================================

def redondear_peso(valor):
    return int(Decimal(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def rut_a_numero(rut):
    rut = str(rut).replace(".", "").replace("-", "").strip()
    return int(rut[:-1])


def formato_monto(valor):
    return f"{int(valor):,}".replace(",", ".")


def calcular_retencion_base_honorarios(bruto):
    return redondear_peso(Decimal(str(int(bruto))) * TASA_HONORARIOS)


def calcular_prestamo_3_truncado(bruto):
    return int(Decimal(str(int(bruto))) * TASA_PRESTAMO_3)


def normalizar_rut(rut):
    return str(rut).replace(" ", "").replace(".", "").upper()


# =====================================================
# 3. DATOS DEL CONTRIBUYENTE
# =====================================================

def extraer_info_contribuyente(df_raw):
    valores = df_raw.values.flatten().tolist()
    texto = " ".join([str(valor) for valor in valores if pd.notna(valor)])

    nombre = "No disponible"
    rut = "No disponible"

    match_nombre = re.search(
        r"Contribuyente:\s*([A-ZÁÉÍÓÚÑ0-9 .,&\-]+?)\s+RUT",
        texto,
        re.IGNORECASE,
    )

    if match_nombre:
        nombre = match_nombre.group(1).strip()

    match_rut = re.search(
        r"RUT\s*[:\-]?\s*([0-9]{1,2}\.?[0-9]{3}\.?[0-9]{3}\s*-\s*[0-9Kk])",
        texto,
        re.IGNORECASE,
    )

    if match_rut:
        rut = normalizar_rut(match_rut.group(1))

    return nombre, rut


def bloque_contribuyente(nombre_empresa, rut_empresa):
    return f"""
<style>
.bloque-sii {{
    font-family: Arial, sans-serif;
    color: #F4F7F8;
    margin-top: 30px;
    margin-bottom: 30px;
    padding: 15px 20px;
    background-color: #0f172a;
    border-radius: 8px;
    max-width: 650px;
}}
.bloque-sii h2 {{
    margin-bottom: 12px;
}}
.bloque-sii p {{
    margin-bottom: 14px;
}}
.bloque-sii table {{
    border-collapse: collapse;
    font-size: 14px;
}}
.bloque-sii td {{
    padding: 4px 14px 4px 0;
}}
.bloque-sii .label {{
    font-weight: bold;
}}
</style>

<div class="bloque-sii">
    <h2>Detalle consulta declaración jurada</h2>
    <p>A continuación se despliega el detalle preparado para la Declaración Jurada <b>1879</b>.</p>
    <table>
        <tr><td class="label">Nombre o Razón Social:</td><td>{nombre_empresa}</td></tr>
        <tr><td class="label">RUT Empresa Declarante:</td><td>{rut_empresa}</td></tr>
        <tr><td class="label">Año Tributario:</td><td>{ANIO_TRIBUTARIO}</td></tr>
        <tr><td class="label">Año Comercial:</td><td>{ANIO_COMERCIAL}</td></tr>
    </table>
</div>
"""


# =====================================================
# 4. PROCESAMIENTO DE ARCHIVOS
# =====================================================

def procesar_archivo(file):
    df_raw = pd.read_html(file)[0]
    nombre_empresa, rut_empresa = extraer_info_contribuyente(df_raw)

    df = df_raw.copy()
    df.columns = df.iloc[2]
    df = df.iloc[3:].copy()

    df.columns = df.columns.astype(str)
    df.columns = df.columns.str.replace("\xa0", " ", regex=False)
    df.columns = df.columns.str.strip()

    df = df[df["Estado"] != "Totales* :"].copy()
    df = df[df["Estado"] != "Totales*:"].copy()
    df = df[df["Estado"] == "VIGENTE"].copy()

    df["Brutos"] = pd.to_numeric(df["Brutos"], errors="coerce").fillna(0).astype(int)
    df["Retenido"] = pd.to_numeric(df["Retenido"], errors="coerce").fillna(0).astype(int)
    df["Pagado"] = pd.to_numeric(df["Pagado"], errors="coerce").fillna(0).astype(int)

    df = df[df["Retenido"] > 0].copy()

    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce")
    df["Mes"] = df["Fecha"].dt.month
    df["Archivo_Origen"] = file.name
    df["Nombre_Empresa_Declarante"] = nombre_empresa
    df["Rut_Empresa_Declarante"] = rut_empresa

    return df, nombre_empresa, rut_empresa


# =====================================================
# 5. LÓGICA TRIBUTARIA SII
# =====================================================

def separar_retenciones(df_total):
    df = df_total.copy()

    df["Retenido_Base_145"] = df["Brutos"].apply(calcular_retencion_base_honorarios)
    df["Exceso_Retencion"] = df["Retenido"] - df["Retenido_Base_145"]

    df["Retenido_Prestamo_3"] = df.apply(
        lambda row: calcular_prestamo_3_truncado(row["Brutos"])
        if row["Exceso_Retencion"] > 0
        else 0,
        axis=1,
    )

    df["Retenido_Honorarios"] = df["Retenido"] - df["Retenido_Prestamo_3"]

    return df


def calcular_actualizaciones_sii(df_total):
    df_calculo = separar_retenciones(df_total)

    df_calculo["Factor"] = df_calculo["Mes"].map(factores_actualizacion)

    if df_calculo["Factor"].isna().any():
        meses_sin_factor = df_calculo[df_calculo["Factor"].isna()]["Mes"].unique()
        raise ValueError(f"Existen meses sin factor de actualización: {meses_sin_factor}")

    df_calculo["Honorarios_Actualizado_Decimal"] = df_calculo.apply(
        lambda row: Decimal(str(int(row["Retenido_Honorarios"]))) * row["Factor"],
        axis=1,
    )

    df_calculo["Prestamo_3_Actualizado_Decimal"] = df_calculo.apply(
        lambda row: Decimal(str(int(row["Retenido_Prestamo_3"]))) * row["Factor"],
        axis=1,
    )

    df_actualizado = (
        df_calculo
        .groupby("Rut")[[
            "Honorarios_Actualizado_Decimal",
            "Prestamo_3_Actualizado_Decimal"
        ]]
        .sum()
        .reset_index()
    )

    df_actualizado["Honorarios_Actualizado"] = df_actualizado[
        "Honorarios_Actualizado_Decimal"
    ].apply(redondear_peso)

    df_actualizado["Prestamo_3_Actualizado"] = df_actualizado[
        "Prestamo_3_Actualizado_Decimal"
    ].apply(redondear_peso)

    df_actualizado = df_actualizado[[
        "Rut",
        "Honorarios_Actualizado",
        "Prestamo_3_Actualizado",
    ]]

    df_calculo["Honorarios_Actualizado_Decimal"] = df_calculo[
        "Honorarios_Actualizado_Decimal"
    ].astype(str)

    df_calculo["Prestamo_3_Actualizado_Decimal"] = df_calculo[
        "Prestamo_3_Actualizado_Decimal"
    ].astype(str)

    return df_calculo, df_actualizado


# =====================================================
# 6. EXPORTACIÓN EXCEL
# =====================================================

def convertir_a_excel(df_dj, df_cuadro_resumen, df_resumen, df_detalle):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_dj.to_excel(writer, index=False, sheet_name="DJ_1879")
        df_cuadro_resumen.to_excel(writer, index=False, sheet_name="Cuadro_Resumen")
        df_resumen.to_excel(writer, index=False, sheet_name="Resumen_Anual")
        df_detalle.to_excel(writer, index=False, sheet_name="Detalle_Boletas")

    output.seek(0)
    return output.getvalue()


# =====================================================
# 7. TABLAS HTML TIPO SII
# =====================================================

def tabla_html_resumen(total_casos, total_honorarios_actualizados, total_prestamo_3, total_honorarios_sin_actualizar):
    return f"""
<style>
.tabla-resumen {{
    width: 100%;
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 13px;
    margin-top: 10px;
    margin-bottom: 25px;
}}
.tabla-resumen th {{
    background-color: #073B53;
    color: white;
    border: 1px solid #D9E2E7;
    padding: 8px;
    text-align: center;
    vertical-align: middle;
}}
.tabla-resumen td {{
    border: 1px solid #D9E2E7;
    padding: 8px;
    text-align: center;
    background-color: #FFFFFF;
    color: #1A1A1A;
}}
.tabla-resumen .seccion {{
    background-color: #073B53;
    color: white;
    font-weight: bold;
    text-align: left;
}}
.tabla-resumen .monto {{
    text-align: right;
    font-weight: 600;
}}
</style>

<table class="tabla-resumen">
<tr>
    <th colspan="6" class="seccion">Montos Informados</th>
    <th colspan="5" class="seccion">Montos Calculados</th>
</tr>
<tr>
    <th>Total de Casos Informados</th>
    <th>Honorarios y Otros Art. 42 N°2<br>Tasa 14,5%</th>
    <th>Remuneración Directores Art. 48<br>Tasa 10%</th>
    <th>Remuneración Directores Art. 48<br>Tasa 35%</th>
    <th>Monto pagado anual actualizado<br>servicios Isla de Pascua</th>
    <th>3% Préstamo tasa 0% año 2021</th>
    <th>Total de Casos Informados</th>
    <th>Honorarios y Otros Art. 42 N°2<br>Tasa 14,5%</th>
    <th>Remuneración Directores Art. 48<br>Tasa 10%</th>
    <th>Monto pagado anual actualizado<br>servicios Isla de Pascua</th>
    <th>3% Préstamo tasa 0% año 2021</th>
</tr>
<tr>
    <td>{total_casos}</td>
    <td class="monto">{formato_monto(total_honorarios_actualizados)}</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td class="monto">{formato_monto(total_prestamo_3)}</td>
    <td>{total_casos}</td>
    <td class="monto">{formato_monto(total_honorarios_actualizados)}</td>
    <td>0</td>
    <td>0</td>
    <td class="monto">{formato_monto(total_prestamo_3)}</td>
</tr>
</table>

<table class="tabla-resumen">
<tr>
    <th>Monto total honorarios sin actualizar</th>
</tr>
<tr>
    <td style="text-align:center; font-weight:600;">{formato_monto(total_honorarios_sin_actualizar)}</td>
</tr>
</table>
"""


def tabla_html_dj(df_dj_lista):
    html = """
<style>
.tabla-dj {
    width: 100%;
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 13px;
    margin-top: 10px;
    margin-bottom: 25px;
}
.tabla-dj th {
    background-color: #073B53;
    color: white;
    border: 1px solid #D9E2E7;
    padding: 8px;
    text-align: center;
    vertical-align: middle;
}
.tabla-dj td {
    border: 1px solid #D9E2E7;
    padding: 7px;
    text-align: center;
    color: #1A1A1A;
}
.tabla-dj tr:nth-child(even) {
    background-color: #F4F7F8;
}
.tabla-dj tr:nth-child(odd) {
    background-color: #FFFFFF;
}
.tabla-dj .nombre {
    text-align: left;
    font-weight: 500;
}
.tabla-dj .monto {
    text-align: right;
    font-weight: 600;
}
</style>

<table class="tabla-dj">
<tr>
<th>N°</th>
<th>RUT Receptor de la Renta</th>
<th>Nombre o Razón Social</th>
<th>Monto Retenido Anual Actualizado<br>Honorarios y Otros<br>Tasa 14,5%</th>
<th>ENE</th><th>FEB</th><th>MAR</th><th>ABR</th><th>MAY</th><th>JUN</th>
<th>JUL</th><th>AGO</th><th>SEP</th><th>OCT</th><th>NOV</th><th>DIC</th>
<th>3% Préstamo<br>Año 2021</th>
</tr>
"""

    for i, row in df_dj_lista.reset_index(drop=True).iterrows():
        html += f"""
<tr>
<td>{i + 1}</td>
<td>{row["Rut"]}</td>
<td class="nombre">{row["Nombre o Razón Social"]}</td>
<td class="monto">{formato_monto(row["Honorarios y Otros Art. 42 N°2 - Tasa 14,5%"])}</td>
<td>{row["ENE"]}</td>
<td>{row["FEB"]}</td>
<td>{row["MAR"]}</td>
<td>{row["ABR"]}</td>
<td>{row["MAY"]}</td>
<td>{row["JUN"]}</td>
<td>{row["JUL"]}</td>
<td>{row["AGO"]}</td>
<td>{row["SEP"]}</td>
<td>{row["OCT"]}</td>
<td>{row["NOV"]}</td>
<td>{row["DIC"]}</td>
<td class="monto">{formato_monto(row["3% Préstamo tasa 0% año 2021"])}</td>
</tr>
"""

    html += "</table>"
    return html


# =====================================================
# 8. INTERFAZ WEB
# =====================================================

def run_1879():

    st.title("📊 Asistente DJ 1879 - Honorarios")
    st.subheader("Automatiza la preparación de la DJ 1879 en minutos")

    st.markdown("""
    Esta herramienta permite preparar automáticamente la **Declaración Jurada 1879 de Honorarios (SII)**, reduciendo errores y tiempos de procesamiento.

    **Paso 1: Descarga los archivos desde el SII**
    Ruta sugerida:
    Servicios Online → Boletas de Honorarios Electrónicas → Receptor de Boletas → Informe mensual de boletas recibidas.

    **Paso 2: Sube los archivos mensuales**
    Debes subir los archivos de **Boletas de Honorarios Recibidas** descargados desde el portal del SII.

    **Paso 3: Revisa y descarga tu DJ**
    El sistema consolida los archivos, excluye documentos no vigentes, actualiza las retenciones y genera una tabla lista para revisión y descarga.
    """)

    st.markdown("### Paso 1: Sube los archivos mensuales")

    files = st.file_uploader(
        "Archivos de Boletas de Honorarios Recibidas (SII)",
        accept_multiple_files=True,
        type=["xls", "html", "htm"]
    )


# =====================================================
# 9. PROCESAMIENTO PRINCIPAL
# =====================================================

if files:

    with st.expander("Ver archivos cargados"):
        st.write([file.name for file in files])

    lista_df = []
    nombre_empresa = "No disponible"
    rut_empresa = "No disponible"

    for file in files:
        try:
            df_mes, nombre_detectado, rut_detectado = procesar_archivo(file)
            lista_df.append(df_mes)

            if nombre_detectado != "No disponible":
                nombre_empresa = nombre_detectado

            if rut_detectado != "No disponible":
                rut_empresa = rut_detectado

        except Exception as e:
            st.error(f"Error procesando el archivo {file.name}: {e}")

    if lista_df:

        df_total = pd.concat(lista_df, ignore_index=True)

        df_calculo_retenciones, df_actualizado = calcular_actualizaciones_sii(df_total)

        df_base = (
            df_calculo_retenciones
            .groupby("Rut")[[
                "Brutos",
                "Retenido",
                "Pagado",
                "Retenido_Honorarios",
                "Retenido_Prestamo_3"
            ]]
            .sum()
            .reset_index()
        )

        df_resumen = df_base.merge(df_actualizado, on="Rut", how="left")

        df_nombres = (
            df_total[["Rut", "Nombre o Razón Social"]]
            .drop_duplicates(subset=["Rut"])
            .copy()
        )

        df_meses = (
            df_total
            .groupby("Rut")["Mes"]
            .apply(lambda x: sorted(x.dropna().unique().tolist()))
            .reset_index()
            .rename(columns={"Mes": "Meses"})
        )

        df_final = df_resumen.merge(df_nombres, on="Rut", how="left")
        df_final = df_final.merge(df_meses, on="Rut", how="left")

        df_final = df_final[
            (df_final["Retenido_Honorarios"] > 0) |
            (df_final["Retenido_Prestamo_3"] > 0)
        ].copy()

        df_final["Rut_Orden"] = df_final["Rut"].apply(rut_a_numero)
        df_final = df_final.sort_values("Rut_Orden").drop(columns=["Rut_Orden"])
        df_final = df_final.reset_index(drop=True)

        for num_mes, nombre_mes in meses_dict.items():
            df_final[nombre_mes] = df_final["Meses"].apply(
                lambda lista: "X" if num_mes in lista else ""
            )

        df_resumen_final = df_final[
            [
                "Rut",
                "Nombre o Razón Social",
                "Brutos",
                "Retenido",
                "Retenido_Honorarios",
                "Retenido_Prestamo_3",
                "Honorarios_Actualizado",
                "Prestamo_3_Actualizado",
                "Pagado",
                "Meses",
                "ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
                "JUL", "AGO", "SEP", "OCT", "NOV", "DIC",
            ]
        ].copy().reset_index(drop=True)

        df_dj_lista = df_final[
            [
                "Rut",
                "Nombre o Razón Social",
                "Honorarios_Actualizado",
                "ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
                "JUL", "AGO", "SEP", "OCT", "NOV", "DIC",
                "Prestamo_3_Actualizado",
            ]
        ].copy().reset_index(drop=True)

        df_dj_lista = df_dj_lista.rename(
            columns={
                "Honorarios_Actualizado": "Honorarios y Otros Art. 42 N°2 - Tasa 14,5%",
                "Prestamo_3_Actualizado": "3% Préstamo tasa 0% año 2021",
            }
        )

        total_honorarios_actualizados = df_dj_lista[
            "Honorarios y Otros Art. 42 N°2 - Tasa 14,5%"
        ].sum()

        total_prestamo_3 = df_dj_lista[
            "3% Préstamo tasa 0% año 2021"
        ].sum()

        total_honorarios_sin_actualizar = df_resumen_final["Brutos"].sum()
        total_casos = df_dj_lista["Rut"].nunique()

        df_cuadro_resumen = pd.DataFrame({
            "Campo": [
                "Honorarios y Otros Art. 42 N°2 - Tasa 14,5%",
                "Remuneración Directores Art. 48 - Tasa 10%",
                "Remuneración Directores Art. 48 - Tasa 35%",
                "Monto pagado anual actualizado por servicios en Isla de Pascua",
                "3% Préstamo tasa 0% año 2021",
                "Monto total honorarios sin actualizar",
                "Total casos informados",
            ],
            "Monto": [
                total_honorarios_actualizados,
                0,
                0,
                0,
                total_prestamo_3,
                total_honorarios_sin_actualizar,
                total_casos,
            ],
        })

        st.markdown("---")
        st.markdown("## Paso 2: Revisa los resultados y descarga tu DJ")
        st.success("Archivos procesados correctamente.")

        st.markdown(
            bloque_contribuyente(nombre_empresa, rut_empresa),
            unsafe_allow_html=True,
        )

        st.markdown("## Resumen final de la declaración")
        st.markdown(
            tabla_html_resumen(
                total_casos,
                total_honorarios_actualizados,
                total_prestamo_3,
                total_honorarios_sin_actualizar,
            ),
            unsafe_allow_html=True,
        )

        st.subheader("Datos de los informados - DJ 1879 lista para declarar")
        st.markdown(
            tabla_html_dj(df_dj_lista),
            unsafe_allow_html=True,
        )

        with st.expander("Ver resumen anual por RUT"):
            st.dataframe(
                df_resumen_final,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Ver detalle consolidado de boletas válidas"):
            st.dataframe(
                df_total.reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

        excel_data = convertir_a_excel(
            df_dj_lista,
            df_cuadro_resumen,
            df_resumen_final,
            df_total.reset_index(drop=True),
        )

        st.download_button(
            label="📥 Descargar Excel completo",
            data=excel_data,
            file_name="DJ_1879_Honorarios_DD_Contable.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
