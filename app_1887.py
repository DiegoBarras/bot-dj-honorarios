import re
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import streamlit as st


# =====================================================
# 1. PARÁMETROS GENERALES
# =====================================================

ANIO_COMERCIAL_DEFAULT = 2025

MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

MESES_NOMBRE = {
    "ENE": "Enero",
    "FEB": "Febrero",
    "MAR": "Marzo",
    "ABR": "Abril",
    "MAY": "Mayo",
    "JUN": "Junio",
    "JUL": "Julio",
    "AGO": "Agosto",
    "SEP": "Septiembre",
    "OCT": "Octubre",
    "NOV": "Noviembre",
    "DIC": "Diciembre",
}

NOMBRE_A_MES = {
    "enero": "ENE",
    "febrero": "FEB",
    "marzo": "MAR",
    "abril": "ABR",
    "mayo": "MAY",
    "junio": "JUN",
    "julio": "JUL",
    "agosto": "AGO",
    "septiembre": "SEP",
    "setiembre": "SEP",
    "octubre": "OCT",
    "noviembre": "NOV",
    "diciembre": "DIC",
}

FACTORES_ACTUALIZACION = {
    "ENE": Decimal("1.036"),
    "FEB": Decimal("1.026"),
    "MAR": Decimal("1.022"),
    "ABR": Decimal("1.016"),
    "MAY": Decimal("1.014"),
    "JUN": Decimal("1.012"),
    "JUL": Decimal("1.017"),
    "AGO": Decimal("1.008"),
    "SEP": Decimal("1.007"),
    "OCT": Decimal("1.003"),
    "NOV": Decimal("1.003"),
    "DIC": Decimal("1.000"),
}


# =====================================================
# 2. COLUMNAS LRE
# =====================================================

COL_RUT = "Rut trabajador(1101)"
COL_FECHA_TERMINO = "Fecha término de contrato(1103)"
COL_JORNADA = "Código tipo de jornada(1107)"
COL_DIAS_TRABAJADOS = "Nro días trabajados en el mes(1115)"

COL_TOTAL_HABERES_IMP_TRIB = "Total haberes imponibles y tributables(5210)"
COL_TOTAL_HABERES_IMP_NO_TRIB = "Total haberes imponibles no tributables(5220)"
COL_TOTAL_HABERES_NO_IMP_NO_TRIB = "Total haberes no imponibles y no tributables(5230)"
COL_TOTAL_HABERES_NO_IMP_TRIB = "Total haberes no imponibles y tributables(5240)"

COL_AFP = "Cotización obligatoria previsional (AFP o IPS)(3141)"
COL_SALUD = "Cotización obligatoria salud 7%(3143)"
COL_AFC_TRAB = "Cotización AFC - trabajador(3151)"
COL_TRABAJO_PESADO_TRAB = "Cotización adicional trabajo pesado - trabajador(3154)"

COL_IUSC = "Impuesto retenido por remuneraciones(3161)"
COL_IUSC_INDEMNIZACIONES = "Impuesto retenido por indemnizaciones(3162)"
COL_MAYOR_RETENCION = "Mayor retención de impuestos solicitada por el trabajador(3163)"
COL_IUSC_RELIQ = "Impuesto retenido por reliquidación remun. devengadas otros períodos(3164)"
COL_DIF_RELIQ = "Diferencia impuesto reliquidación remun. devengadas en este período(3165)"
COL_PRESTAMO_3 = "Retención préstamo clase media 2020 (Ley 21.252) (3166)"
COL_REBAJA_ZONA = "Rebaja zona extrema DL 889 (3167)"

COL_TOTAL_COTIZACIONES_TRAB = "Total descuentos por cotizaciones del trabajador(5341)"
COL_TOTAL_APORTES_EMPLEADOR = "Total aportes empleador(5410)"


# =====================================================
# 3. ESTADO DE SESIÓN
# =====================================================

def inicializar_estado_1887():
    if "paso_actual_1887" not in st.session_state:
        st.session_state.paso_actual_1887 = 0

    if "datos_declarante_1887" not in st.session_state:
        st.session_state.datos_declarante_1887 = {}

    if "df_lre_mensual_1887" not in st.session_state:
        st.session_state.df_lre_mensual_1887 = None

    if "df_dj_1887" not in st.session_state:
        st.session_state.df_dj_1887 = None

    if "df_resumen_1887" not in st.session_state:
        st.session_state.df_resumen_1887 = None

    if "df_comparacion_sii_1887" not in st.session_state:
        st.session_state.df_comparacion_sii_1887 = None


def ir_a_paso(paso):
    st.session_state.paso_actual_1887 = paso
    st.rerun()


# =====================================================
# 4. FUNCIONES AUXILIARES
# =====================================================

def formato_monto(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except Exception:
        return "0"


def redondear_peso(valor):
    return int(Decimal(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def normalizar_rut(rut):
    if pd.isna(rut):
        return ""

    rut = str(rut).strip().upper()
    rut = rut.replace(".", "").replace(" ", "")
    return rut


def validar_rut_basico(rut):
    rut = normalizar_rut(rut)
    return bool(re.match(r"^[0-9]{7,8}-[0-9K]$", rut))


def rut_a_numero(rut):
    rut = normalizar_rut(rut)
    rut_sin_dv = rut.split("-")[0]

    try:
        return int(rut_sin_dv)
    except Exception:
        return 0


def limpiar_monto(valor):
    if pd.isna(valor) or valor == "":
        return 0

    texto = str(valor).strip()
    texto = texto.replace("$", "")
    texto = texto.replace(".", "")
    texto = texto.replace(",", "")
    texto = texto.replace(" ", "")

    if texto in ["", "-", "nan", "None"]:
        return 0

    try:
        return int(float(texto))
    except Exception:
        return 0


def obtener_columna(df, nombre_columna):
    if nombre_columna in df.columns:
        return nombre_columna
    return None


def obtener_serie_monto(df, nombre_columna):
    if nombre_columna in df.columns:
        return df[nombre_columna].apply(limpiar_monto)
    return pd.Series([0] * len(df), index=df.index)


def detectar_mes_desde_nombre(nombre_archivo):
    nombre = nombre_archivo.lower()

    for nombre_mes, codigo_mes in NOMBRE_A_MES.items():
        if nombre_mes in nombre:
            return codigo_mes

    return None


def leer_archivo_lre(file):
    nombre = file.name

    if nombre.lower().endswith(".xlsx"):
        df = pd.read_excel(file)
        return df

    encodings = ["utf-8-sig", "latin1", "cp1252"]
    separadores = [";", ",", "\t"]

    ultimo_error = None

    for enc in encodings:
        for sep in separadores:
            try:
                file.seek(0)
                df = pd.read_csv(file, sep=sep, encoding=enc)
                if len(df.columns) > 20:
                    return df
            except Exception as e:
                ultimo_error = e

    raise ValueError(f"No se pudo leer el archivo {nombre}. Error: {ultimo_error}")


def crear_template_manual_1887():
    columnas = [
        "Rut_Trabajador",
        "Monto_ENE",
        "Monto_FEB",
        "Monto_MAR",
        "Monto_ABR",
        "Monto_MAY",
        "Monto_JUN",
        "Monto_JUL",
        "Monto_AGO",
        "Monto_SEP",
        "Monto_OCT",
        "Monto_NOV",
        "Monto_DIC",
        "IUSC_ENE",
        "IUSC_FEB",
        "IUSC_MAR",
        "IUSC_ABR",
        "IUSC_MAY",
        "IUSC_JUN",
        "IUSC_JUL",
        "IUSC_AGO",
        "IUSC_SEP",
        "IUSC_OCT",
        "IUSC_NOV",
        "IUSC_DIC",
        "Mayor_Retencion_Anual",
        "Renta_No_Gravada_Anual",
        "Renta_Exenta_Anual",
        "Rebaja_Zona_Extrema_Anual",
        "Prestamo_3_Anual",
        "Horas_Semanales",
    ]

    df = pd.DataFrame(columns=columnas)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Carga_Manual_1887")

    output.seek(0)
    return output.getvalue()


# =====================================================
# 5. PROCESAMIENTO LRE
# =====================================================

def cargar_lre_desde_archivos(files):
    registros = []
    meses_detectados = []

    for file in files:
        mes = detectar_mes_desde_nombre(file.name)

        if mes is None:
            raise ValueError(f"No pude detectar el mes desde el nombre del archivo: {file.name}")

        df = leer_archivo_lre(file)
        df["MES_DJ"] = mes
        df["ARCHIVO_ORIGEN"] = file.name

        registros.append(df)
        meses_detectados.append(mes)

    meses_unicos = sorted(set(meses_detectados), key=lambda x: MESES.index(x))

    meses_faltantes = [mes for mes in MESES if mes not in meses_unicos]
    meses_duplicados = sorted(
        [mes for mes in set(meses_detectados) if meses_detectados.count(mes) > 1],
        key=lambda x: MESES.index(x)
    )

    if meses_faltantes:
        raise ValueError(
            "No se puede avanzar. Faltan LRE de los siguientes meses: "
            + ", ".join(meses_faltantes)
        )

    if meses_duplicados:
        raise ValueError(
            "No se puede avanzar. Existen meses duplicados en la carga: "
            + ", ".join(meses_duplicados)
        )

    if len(meses_unicos) != 12:
        raise ValueError("No se puede avanzar. Debes cargar exactamente los 12 meses del LRE.")

    df_total = pd.concat(registros, ignore_index=True)

    columnas_minimas = [
        COL_RUT,
        COL_TOTAL_HABERES_IMP_TRIB,
        COL_IUSC,
    ]

    faltantes = [col for col in columnas_minimas if col not in df_total.columns]

    if faltantes:
        raise ValueError(
            "El LRE no contiene columnas mínimas requeridas: "
            + ", ".join(faltantes)
        )

    return df_total


def transformar_lre_mensual(df_lre):
    df = df_lre.copy()

    df["Rut_Trabajador"] = df[COL_RUT].apply(normalizar_rut)

    df["Total_Haberes_Imp_Trib"] = obtener_serie_monto(df, COL_TOTAL_HABERES_IMP_TRIB)
    df["Haberes_Imp_No_Trib"] = obtener_serie_monto(df, COL_TOTAL_HABERES_IMP_NO_TRIB)
    df["Haberes_No_Imp_No_Trib"] = obtener_serie_monto(df, COL_TOTAL_HABERES_NO_IMP_NO_TRIB)
    df["Haberes_No_Imp_Trib"] = obtener_serie_monto(df, COL_TOTAL_HABERES_NO_IMP_TRIB)

    df["Cot_AFP"] = obtener_serie_monto(df, COL_AFP)
    df["Cot_Salud"] = obtener_serie_monto(df, COL_SALUD)
    df["Cot_AFC_Trab"] = obtener_serie_monto(df, COL_AFC_TRAB)
    df["Cot_Trabajo_Pesado_Trab"] = obtener_serie_monto(df, COL_TRABAJO_PESADO_TRAB)

    df["IUSC"] = obtener_serie_monto(df, COL_IUSC)
    df["IUSC_Reliquidacion"] = obtener_serie_monto(df, COL_IUSC_RELIQ)
    df["Diferencia_Reliquidacion"] = obtener_serie_monto(df, COL_DIF_RELIQ)
    df["Mayor_Retencion"] = obtener_serie_monto(df, COL_MAYOR_RETENCION)
    df["Prestamo_3"] = obtener_serie_monto(df, COL_PRESTAMO_3)
    df["Rebaja_Zona_Extrema"] = obtener_serie_monto(df, COL_REBAJA_ZONA)

    df["Total_Cotizaciones_Trabajador"] = obtener_serie_monto(df, COL_TOTAL_COTIZACIONES_TRAB)
    df["Total_Aportes_Empleador"] = obtener_serie_monto(df, COL_TOTAL_APORTES_EMPLEADOR)

    df["Cotizaciones_Obligatorias_Para_DJ"] = (
        df["Cot_AFP"]
        + df["Cot_Salud"]
        + df["Cot_AFC_Trab"]
        + df["Cot_Trabajo_Pesado_Trab"]
    )

    df["Renta_Total_Neta_Mensual"] = (
        df["Total_Haberes_Imp_Trib"] - df["Cotizaciones_Obligatorias_Para_DJ"]
    )

    df["Renta_Total_Neta_Mensual"] = df["Renta_Total_Neta_Mensual"].apply(lambda x: max(int(x), 0))

    df["Renta_No_Gravada_Mensual"] = df["Haberes_Imp_No_Trib"] + df["Haberes_No_Imp_No_Trib"]

    df["Renta_Exenta_Mensual"] = 0

    df["Monto_Ingreso_Mensual_Sin_Actualizar"] = (
        df["Renta_Total_Neta_Mensual"] + df["Rebaja_Zona_Extrema"]
    )

    df["Factor"] = df["MES_DJ"].map(FACTORES_ACTUALIZACION)

    df["Renta_Total_Neta_Actualizada"] = df.apply(
        lambda row: redondear_peso(Decimal(str(int(row["Renta_Total_Neta_Mensual"]))) * row["Factor"]),
        axis=1,
    )

    df["IUSC_Actualizado"] = df.apply(
        lambda row: redondear_peso(Decimal(str(int(row["IUSC"] + row["IUSC_Reliquidacion"] + row["Diferencia_Reliquidacion"]))) * row["Factor"]),
        axis=1,
    )

    df["Mayor_Retencion_Actualizada"] = df.apply(
        lambda row: redondear_peso(Decimal(str(int(row["Mayor_Retencion"]))) * row["Factor"]),
        axis=1,
    )

    df["Renta_No_Gravada_Actualizada"] = df.apply(
        lambda row: redondear_peso(Decimal(str(int(row["Renta_No_Gravada_Mensual"]))) * row["Factor"]),
        axis=1,
    )

    df["Renta_Exenta_Actualizada"] = df.apply(
        lambda row: redondear_peso(Decimal(str(int(row["Renta_Exenta_Mensual"]))) * row["Factor"]),
        axis=1,
    )

    df["Rebaja_Zona_Extrema_Actualizada"] = df.apply(
        lambda row: redondear_peso(Decimal(str(int(row["Rebaja_Zona_Extrema"]))) * row["Factor"]),
        axis=1,
    )

    df["Prestamo_3_Actualizado"] = df.apply(
        lambda row: redondear_peso(Decimal(str(int(row["Prestamo_3"]))) * row["Factor"]),
        axis=1,
    )

    df["Remuneracion_Imponible_Prev_Actualizada"] = df.apply(
        lambda row: redondear_peso(Decimal(str(int(row["Total_Haberes_Imp_Trib"]))) * row["Factor"]),
        axis=1,
    )

    df["Leyes_Sociales"] = (
        df["Total_Cotizaciones_Trabajador"] + df["Total_Aportes_Empleador"]
    )

    if COL_FECHA_TERMINO in df.columns:
        df["Tiene_Termino"] = df[COL_FECHA_TERMINO].fillna("").astype(str).str.strip().apply(
            lambda x: x not in ["", "nan", "NaT", "None"]
        )
    else:
        df["Tiene_Termino"] = False

    if COL_JORNADA in df.columns:
        df["Codigo_Jornada"] = pd.to_numeric(df[COL_JORNADA], errors="coerce").fillna(0).astype(int)
    else:
        df["Codigo_Jornada"] = 101

    df["Horas_Semanales"] = df["Codigo_Jornada"].apply(lambda x: 99 if x >= 700 else 40)

    df["Periodo_DJ"] = df.apply(
        lambda row: "F" if row["Tiene_Termino"] else ("C" if row["Monto_Ingreso_Mensual_Sin_Actualizar"] > 0 else ""),
        axis=1,
    )

    columnas = [
        "Rut_Trabajador",
        "MES_DJ",
        "Renta_Total_Neta_Mensual",
        "Monto_Ingreso_Mensual_Sin_Actualizar",
        "IUSC",
        "Mayor_Retencion",
        "Renta_No_Gravada_Mensual",
        "Renta_Exenta_Mensual",
        "Rebaja_Zona_Extrema",
        "Prestamo_3",
        "Leyes_Sociales",
        "Total_Haberes_Imp_Trib",
        "Renta_Total_Neta_Actualizada",
        "IUSC_Actualizado",
        "Mayor_Retencion_Actualizada",
        "Renta_No_Gravada_Actualizada",
        "Renta_Exenta_Actualizada",
        "Rebaja_Zona_Extrema_Actualizada",
        "Prestamo_3_Actualizado",
        "Remuneracion_Imponible_Prev_Actualizada",
        "Periodo_DJ",
        "Horas_Semanales",
        "ARCHIVO_ORIGEN",
    ]

    return df[columnas].copy()


def consolidar_dj_1887(df_mensual):
    df = df_mensual.copy()

    agrupado = (
        df.groupby("Rut_Trabajador")
        .agg({
            "Renta_Total_Neta_Actualizada": "sum",
            "IUSC_Actualizado": "sum",
            "Mayor_Retencion_Actualizada": "sum",
            "Renta_No_Gravada_Actualizada": "sum",
            "Renta_Exenta_Actualizada": "sum",
            "Rebaja_Zona_Extrema_Actualizada": "sum",
            "Prestamo_3_Actualizado": "sum",
            "Renta_Total_Neta_Mensual": "sum",
            "IUSC": "sum",
            "Renta_No_Gravada_Mensual": "sum",
            "Renta_Exenta_Mensual": "sum",
            "Rebaja_Zona_Extrema": "sum",
            "Prestamo_3": "sum",
            "Leyes_Sociales": "sum",
            "Remuneracion_Imponible_Prev_Actualizada": "sum",
            "Horas_Semanales": "max",
        })
        .reset_index()
    )

    pivot_periodos = (
        df.pivot_table(
            index="Rut_Trabajador",
            columns="MES_DJ",
            values="Periodo_DJ",
            aggfunc=lambda x: next((v for v in x if v != ""), "")
        )
        .reset_index()
    )

    pivot_ingresos = (
        df.pivot_table(
            index="Rut_Trabajador",
            columns="MES_DJ",
            values="Monto_Ingreso_Mensual_Sin_Actualizar",
            aggfunc="sum"
        )
        .reset_index()
    )

    for mes in MESES:
        if mes not in pivot_periodos.columns:
            pivot_periodos[mes] = ""

        if mes not in pivot_ingresos.columns:
            pivot_ingresos[mes] = 0

    pivot_ingresos = pivot_ingresos.rename(columns={mes: f"Ingreso_{mes}" for mes in MESES})

    df_final = agrupado.merge(pivot_periodos[["Rut_Trabajador"] + MESES], on="Rut_Trabajador", how="left")
    df_final = df_final.merge(pivot_ingresos[["Rut_Trabajador"] + [f"Ingreso_{mes}" for mes in MESES]], on="Rut_Trabajador", how="left")

    df_final["Rut_Orden"] = df_final["Rut_Trabajador"].apply(rut_a_numero)
    df_final = df_final.sort_values("Rut_Orden").drop(columns=["Rut_Orden"]).reset_index(drop=True)

    df_final.insert(0, "N°", range(1, len(df_final) + 1))
    df_final["Número Certificado"] = range(1, len(df_final) + 1)
    df_final["ESTADO"] = "Calculada por D&D Tax Suite"

    columnas_dj = [
        "N°",
        "Rut_Trabajador",
        "Renta_Total_Neta_Actualizada",
        "IUSC_Actualizado",
        "Mayor_Retencion_Actualizada",
        "Renta_No_Gravada_Actualizada",
        "Renta_Exenta_Actualizada",
        "Rebaja_Zona_Extrema_Actualizada",
        "Prestamo_3_Actualizado",
    ] + MESES + [
        "Número Certificado",
    ] + [f"Ingreso_{mes}" for mes in MESES] + [
        "Horas_Semanales",
        "ESTADO",
        "Renta_Total_Neta_Mensual",
        "IUSC",
        "Renta_No_Gravada_Mensual",
        "Renta_Exenta_Mensual",
        "Rebaja_Zona_Extrema",
        "Prestamo_3",
        "Leyes_Sociales",
        "Remuneracion_Imponible_Prev_Actualizada",
    ]

    return df_final[columnas_dj].copy()


def generar_resumen_1887(df_dj):
    total_casos = len(df_dj)

    resumen = {
        "Total Casos Informados": total_casos,
        "Renta Total Neta Pagada Actualizada": df_dj["Renta_Total_Neta_Actualizada"].sum(),
        "Impuesto Único Retenido Actualizado": df_dj["IUSC_Actualizado"].sum(),
        "Mayor Retención Solicitada Actualizada": df_dj["Mayor_Retencion_Actualizada"].sum(),
        "Renta Total No Gravada Actualizada": df_dj["Renta_No_Gravada_Actualizada"].sum(),
        "Renta Total Exenta Actualizada": df_dj["Renta_Exenta_Actualizada"].sum(),
        "Rebaja Zonas Extremas Actualizada": df_dj["Rebaja_Zona_Extrema_Actualizada"].sum(),
        "3% Préstamo Tasa 0% Actualizado": df_dj["Prestamo_3_Actualizado"].sum(),
        "Renta Total Neta Pagada Sin Actualizar": df_dj["Renta_Total_Neta_Mensual"].sum(),
        "IUSC Retenido Sin Actualizar": df_dj["IUSC"].sum(),
        "Renta No Gravada Sin Actualizar": df_dj["Renta_No_Gravada_Mensual"].sum(),
        "Renta Exenta Sin Actualizar": df_dj["Renta_Exenta_Mensual"].sum(),
        "Rebaja Zona Extrema Sin Actualizar": df_dj["Rebaja_Zona_Extrema"].sum(),
        "Leyes Sociales": df_dj["Leyes_Sociales"].sum(),
        "3% Préstamo Sin Actualizar": df_dj["Prestamo_3"].sum(),
        "Remuneración Imponible Previsional Actualizada": df_dj["Remuneracion_Imponible_Prev_Actualizada"].sum(),
    }

    return pd.DataFrame({
        "Campo": list(resumen.keys()),
        "Monto": list(resumen.values()),
    })


# =====================================================
# 6. COMPARADOR SII
# =====================================================

def leer_resultado_sii(file):
    xls = pd.ExcelFile(file)

    if "DETALLE" not in xls.sheet_names:
        raise ValueError("El archivo SII debe contener una hoja llamada DETALLE.")

    df = pd.read_excel(file, sheet_name="DETALLE", header=1)
    df = df.dropna(how="all").copy()

    col_num = "Unnamed: 1"
    col_dv = "Unnamed: 3"

    if col_num not in df.columns or col_dv not in df.columns:
        raise ValueError("No pude identificar las columnas de RUT en el archivo SII.")

    df = df[pd.to_numeric(df[col_num], errors="coerce").notna()].copy()

    df["Rut_Trabajador"] = df.apply(
        lambda row: f"{int(row[col_num])}-{str(row[col_dv]).strip().upper()}",
        axis=1,
    )

    columnas = {
        "Renta_Total_Neta_Actualizada_SII": "Renta Total Neta Pagada (Art.42 N°1, LIR)",
        "IUSC_Actualizado_SII": "Impuesto Único de Segunda Categoría Retenido",
        "Mayor_Retencion_Actualizada_SII": "Mayor Retención Solicitada (Art.88 L.I.R)",
        "Renta_No_Gravada_Actualizada_SII": "Renta Total No Gravada",
        "Renta_Exenta_Actualizada_SII": "Renta Total Exenta",
        "Rebaja_Zona_Extrema_Actualizada_SII": "Rebajas Por Zonas Extremas (FRANQUICIA D.L. 889)",
        "Prestamo_3_Actualizado_SII": "3% PRÉSTAMO TASA 0% AÑO 2021",
    }

    salida = df[["Rut_Trabajador"]].copy()

    for nuevo, original in columnas.items():
        if original in df.columns:
            salida[nuevo] = df[original].apply(limpiar_monto)
        else:
            salida[nuevo] = 0

    for mes, nombre_mes in MESES_NOMBRE.items():
        if nombre_mes in df.columns:
            salida[f"Ingreso_{mes}_SII"] = df[nombre_mes].apply(limpiar_monto)
        else:
            salida[f"Ingreso_{mes}_SII"] = 0

        if mes in df.columns:
            salida[f"Periodo_{mes}_SII"] = df[mes].fillna("").astype(str).str.strip()
        else:
            salida[f"Periodo_{mes}_SII"] = ""

    return salida


def comparar_con_sii(df_dj, df_sii):
    df = df_dj.merge(df_sii, on="Rut_Trabajador", how="outer", indicator=True)

    pares = [
        ("Renta_Total_Neta_Actualizada", "Renta_Total_Neta_Actualizada_SII"),
        ("IUSC_Actualizado", "IUSC_Actualizado_SII"),
        ("Mayor_Retencion_Actualizada", "Mayor_Retencion_Actualizada_SII"),
        ("Renta_No_Gravada_Actualizada", "Renta_No_Gravada_Actualizada_SII"),
        ("Renta_Exenta_Actualizada", "Renta_Exenta_Actualizada_SII"),
        ("Rebaja_Zona_Extrema_Actualizada", "Rebaja_Zona_Extrema_Actualizada_SII"),
        ("Prestamo_3_Actualizado", "Prestamo_3_Actualizado_SII"),
    ]

    for col_bot, col_sii in pares:
        if col_bot not in df.columns:
            df[col_bot] = 0
        if col_sii not in df.columns:
            df[col_sii] = 0

        df[f"DIF_{col_bot}"] = df[col_bot].fillna(0).astype(int) - df[col_sii].fillna(0).astype(int)

    for mes in MESES:
        col_bot = f"Ingreso_{mes}"
        col_sii = f"Ingreso_{mes}_SII"

        if col_bot not in df.columns:
            df[col_bot] = 0
        if col_sii not in df.columns:
            df[col_sii] = 0

        df[f"DIF_Ingreso_{mes}"] = df[col_bot].fillna(0).astype(int) - df[col_sii].fillna(0).astype(int)

    columnas_salida = [
        "Rut_Trabajador",
        "_merge",
    ] + [f"DIF_{col_bot}" for col_bot, _ in pares] + [f"DIF_Ingreso_{mes}" for mes in MESES]

    return df[columnas_salida].copy()


# =====================================================
# 7. EXPORTACIÓN
# =====================================================

def convertir_a_excel_1887(df_dj, df_resumen, df_mensual, df_comparacion=None):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_dj.to_excel(writer, index=False, sheet_name="DJ_1887")
        df_resumen.to_excel(writer, index=False, sheet_name="Resumen_1887")
        df_mensual.to_excel(writer, index=False, sheet_name="Base_LRE_Mensual")

        if df_comparacion is not None:
            df_comparacion.to_excel(writer, index=False, sheet_name="Comparacion_SII")

    output.seek(0)
    return output.getvalue()


# =====================================================
# 8. HTML
# =====================================================

def tabla_html_resumen_1887(df_resumen):
    data = {row["Campo"]: row["Monto"] for _, row in df_resumen.iterrows()}

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
    font-weight: 600;
}}
</style>

<table class="tabla-resumen">
<tr>
    <th colspan="8" class="seccion">Cuadro resumen final de la declaración</th>
</tr>
<tr>
    <th>Total Casos</th>
    <th>Renta Total Neta</th>
    <th>IUSC Retenido</th>
    <th>Mayor Retención</th>
    <th>Renta No Gravada</th>
    <th>Renta Exenta</th>
    <th>Rebaja Zona Extrema</th>
    <th>3% Préstamo</th>
</tr>
<tr>
    <td>{formato_monto(data.get("Total Casos Informados", 0))}</td>
    <td class="monto">{formato_monto(data.get("Renta Total Neta Pagada Actualizada", 0))}</td>
    <td class="monto">{formato_monto(data.get("Impuesto Único Retenido Actualizado", 0))}</td>
    <td class="monto">{formato_monto(data.get("Mayor Retención Solicitada Actualizada", 0))}</td>
    <td class="monto">{formato_monto(data.get("Renta Total No Gravada Actualizada", 0))}</td>
    <td class="monto">{formato_monto(data.get("Renta Total Exenta Actualizada", 0))}</td>
    <td class="monto">{formato_monto(data.get("Rebaja Zonas Extremas Actualizada", 0))}</td>
    <td class="monto">{formato_monto(data.get("3% Préstamo Tasa 0% Actualizado", 0))}</td>
</tr>
</table>
"""


def tabla_html_dj_1887(df_dj):
    html = """
<style>
.tabla-dj {
    width: 100%;
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 11px;
    margin-top: 10px;
    margin-bottom: 25px;
}
.tabla-dj th {
    background-color: #073B53;
    color: white;
    border: 1px solid #D9E2E7;
    padding: 6px;
    text-align: center;
    vertical-align: middle;
}
.tabla-dj td {
    border: 1px solid #D9E2E7;
    padding: 5px;
    text-align: center;
    color: #1A1A1A;
}
.tabla-dj tr:nth-child(even) {
    background-color: #F4F7F8;
}
.tabla-dj tr:nth-child(odd) {
    background-color: #FFFFFF;
}
.tabla-dj .monto {
    text-align: right;
    font-weight: 600;
}
</style>

<table class="tabla-dj">
<tr>
<th>N°</th>
<th>RUT Trabajador</th>
<th>Renta Total Neta</th>
<th>IUSC</th>
<th>Mayor Retención</th>
<th>No Gravada</th>
<th>Exenta</th>
<th>Zona Extrema</th>
<th>3% Préstamo</th>
<th>ENE</th><th>FEB</th><th>MAR</th><th>ABR</th><th>MAY</th><th>JUN</th>
<th>JUL</th><th>AGO</th><th>SEP</th><th>OCT</th><th>NOV</th><th>DIC</th>
<th>N° Cert.</th>
<th>Horas</th>
<th>Estado</th>
</tr>
"""

    for _, row in df_dj.iterrows():
        html += f"""
<tr>
<td>{row["N°"]}</td>
<td>{row["Rut_Trabajador"]}</td>
<td class="monto">{formato_monto(row["Renta_Total_Neta_Actualizada"])}</td>
<td class="monto">{formato_monto(row["IUSC_Actualizado"])}</td>
<td class="monto">{formato_monto(row["Mayor_Retencion_Actualizada"])}</td>
<td class="monto">{formato_monto(row["Renta_No_Gravada_Actualizada"])}</td>
<td class="monto">{formato_monto(row["Renta_Exenta_Actualizada"])}</td>
<td class="monto">{formato_monto(row["Rebaja_Zona_Extrema_Actualizada"])}</td>
<td class="monto">{formato_monto(row["Prestamo_3_Actualizado"])}</td>
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
<td>{row["Número Certificado"]}</td>
<td>{row["Horas_Semanales"]}</td>
<td>{row["ESTADO"]}</td>
</tr>
"""

    html += "</table>"
    return html


# =====================================================
# 9. PANTALLAS
# =====================================================

def pantalla_bienvenida():
    st.title("👥 Asistente DJ 1887 - Remuneraciones")

    st.markdown("""
### Automatiza la preparación de la DJ 1887 desde el Libro de Remuneraciones Electrónico

Este módulo consolida los **12 archivos mensuales del LRE**, valida que no falte ningún mes, calcula los montos anuales actualizados por trabajador y genera una salida tipo SII.

El objetivo es permitir al equipo contable comparar, revisar y respaldar la propuesta de DJ 1887 generada por el SII.
""")

    if st.button("Comenzar"):
        ir_a_paso(1)


def pantalla_paso_1():
    st.title("Paso 1: Datos del declarante")

    with st.form("form_declarante_1887"):
        col1, col2 = st.columns(2)

        with col1:
            nombre_declarante = st.text_input("Nombre o Razón Social")
            rut_declarante = st.text_input("RUT Empresa Declarante")
            correo = st.text_input("Correo electrónico")

        with col2:
            domicilio = st.text_input("Domicilio")
            comuna = st.text_input("Comuna")
            telefono = st.text_input("Teléfono")
            anio_comercial = st.number_input("Año Comercial", value=ANIO_COMERCIAL_DEFAULT, step=1)
            anio_tributario = int(anio_comercial) + 1
            st.caption(f"Año Tributario asociado: {anio_tributario}")

        anio_40_horas = st.number_input(
            "¿En qué año se acogerá plenamente a las 40 horas?",
            value=2023,
            step=1,
        )

        guardar = st.form_submit_button("Guardar y continuar")

    if guardar:
        errores = []

        if nombre_declarante.strip() == "":
            errores.append("Debes ingresar el nombre o razón social.")

        if not validar_rut_basico(rut_declarante):
            errores.append("Debes ingresar un RUT válido con formato 12345678-9.")

        if errores:
            for error in errores:
                st.error(error)
        else:
            st.session_state.datos_declarante_1887 = {
                "nombre_declarante": nombre_declarante.strip(),
                "rut_declarante": normalizar_rut(rut_declarante),
                "correo": correo.strip(),
                "domicilio": domicilio.strip(),
                "comuna": comuna.strip(),
                "telefono": telefono.strip(),
                "anio_comercial": int(anio_comercial),
                "anio_tributario": int(anio_tributario),
                "anio_40_horas": int(anio_40_horas),
            }

            st.success("Paso 1 guardado correctamente.")
            ir_a_paso(2)


def pantalla_paso_2():
    st.title("Paso 2: Carga de información")

    st.markdown("""
### Opción principal: cargar los 12 archivos LRE

Carga los archivos mensuales del **Libro de Remuneraciones Electrónico**.  
El sistema no permitirá avanzar si falta algún mes o si existe un mes duplicado.

### Opción secundaria: carga manual acotada

Quedará disponible en una versión posterior. La prioridad de este módulo es trabajar con archivos oficiales o estructurados generados por software de remuneraciones.
""")

    files = st.file_uploader(
        "Sube los 12 archivos LRE del año comercial",
        type=["csv", "txt", "xlsx"],
        accept_multiple_files=True,
    )

    if files:
        st.write(f"Archivos cargados: {len(files)}")

        with st.expander("Ver archivos cargados"):
            for file in files:
                st.write(f"• {file.name}")

    if st.button("Validar LRE y continuar"):
        if not files:
            st.error("Debes cargar los 12 archivos LRE.")
            return

        try:
            df_lre = cargar_lre_desde_archivos(files)
            df_mensual = transformar_lre_mensual(df_lre)
            df_dj = consolidar_dj_1887(df_mensual)
            df_resumen = generar_resumen_1887(df_dj)

            st.session_state.df_lre_mensual_1887 = df_mensual
            st.session_state.df_dj_1887 = df_dj
            st.session_state.df_resumen_1887 = df_resumen

            st.success("LRE validado correctamente. Se cargaron los 12 meses.")
            ir_a_paso(3)

        except Exception as e:
            st.error(str(e))

    st.divider()

    if st.button("Volver al Paso 1"):
        ir_a_paso(1)


def pantalla_paso_3():
    st.title("Paso 3: Generar DJ 1887")

    df_dj = st.session_state.df_dj_1887
    df_resumen = st.session_state.df_resumen_1887
    df_mensual = st.session_state.df_lre_mensual_1887
    datos = st.session_state.datos_declarante_1887

    if df_dj is None:
        st.error("No hay datos procesados. Vuelve al Paso 2.")
        return

    st.success("DJ 1887 generada correctamente.")

    st.markdown("## Detalle consulta declaración jurada")

    st.markdown(f"""
**Nombre o Razón Social:** {datos.get("nombre_declarante", "")}  
**RUT Empresa Declarante:** {datos.get("rut_declarante", "")}  
**Año Tributario:** {datos.get("anio_tributario", "")}  
**Año Comercial:** {datos.get("anio_comercial", "")}  
**Año 40 horas:** {datos.get("anio_40_horas", "")}
""")

    st.markdown("## Resumen final de la declaración")
    st.markdown(
        tabla_html_resumen_1887(df_resumen),
        unsafe_allow_html=True,
    )

    st.markdown("## Datos de los informados - DJ 1887")
    st.markdown(
        tabla_html_dj_1887(df_dj),
        unsafe_allow_html=True,
    )

    st.markdown("## Comparación opcional contra propuesta SII")

    archivo_sii = st.file_uploader(
        "Sube Excel con resultado/propuesta SII para comparar diferencias",
        type=["xlsx"],
        key="comparador_sii_1887",
    )

    df_comparacion = None

    if archivo_sii:
        try:
            df_sii = leer_resultado_sii(archivo_sii)
            df_comparacion = comparar_con_sii(df_dj, df_sii)
            st.session_state.df_comparacion_sii_1887 = df_comparacion

            st.success("Comparación contra SII generada correctamente.")

            with st.expander("Ver comparación contra SII"):
                st.dataframe(
                    df_comparacion.reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as e:
            st.error(f"No pude procesar el Excel SII: {e}")

    with st.expander("Ver base mensual LRE procesada"):
        st.dataframe(
            df_mensual.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Ver tabla DJ 1887 calculada"):
        st.dataframe(
            df_dj.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

    excel_data = convertir_a_excel_1887(
        df_dj,
        df_resumen,
        df_mensual,
        df_comparacion=st.session_state.df_comparacion_sii_1887,
    )

    st.download_button(
        label="📥 Descargar Excel DJ 1887",
        data=excel_data,
        file_name="DJ_1887_Remuneraciones_DD_Contable.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅️ Volver al Paso 2"):
            ir_a_paso(2)

    with col2:
        if st.button("Reiniciar asistente"):
            st.session_state.paso_actual_1887 = 0
            st.session_state.datos_declarante_1887 = {}
            st.session_state.df_lre_mensual_1887 = None
            st.session_state.df_dj_1887 = None
            st.session_state.df_resumen_1887 = None
            st.session_state.df_comparacion_sii_1887 = None
            st.rerun()


# =====================================================
# 10. FUNCIÓN PRINCIPAL DEL MÓDULO
# =====================================================

def run_1887():
    inicializar_estado_1887()

    paso = st.session_state.paso_actual_1887

    if paso == 0:
        pantalla_bienvenida()

    elif paso == 1:
        pantalla_paso_1()

    elif paso == 2:
        pantalla_paso_2()

    elif paso == 3:
        pantalla_paso_3()


if __name__ == "__main__":
    st.set_page_config(
        page_title="D&D Tax Suite - DJ 1887",
        layout="wide",
    )
    run_1887()