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

UTM_2025 = {
    "ENE": 67429,
    "FEB": 67294,
    "MAR": 68034,
    "ABR": 68306,
    "MAY": 68648,
    "JUN": 68785,
    "JUL": 68923,
    "AGO": 68647,
    "SEP": 69265,
    "OCT": 69265,
    "NOV": 69542,
    "DIC": 69542,
}

TRAMOS_IUSC_UTM = [
    {"desde": Decimal("0"), "hasta": Decimal("13.5"), "factor": Decimal("0"), "rebaja": Decimal("0")},
    {"desde": Decimal("13.5"), "hasta": Decimal("30"), "factor": Decimal("0.04"), "rebaja": Decimal("0.54")},
    {"desde": Decimal("30"), "hasta": Decimal("50"), "factor": Decimal("0.08"), "rebaja": Decimal("1.74")},
    {"desde": Decimal("50"), "hasta": Decimal("70"), "factor": Decimal("0.135"), "rebaja": Decimal("4.49")},
    {"desde": Decimal("70"), "hasta": Decimal("90"), "factor": Decimal("0.23"), "rebaja": Decimal("11.14")},
    {"desde": Decimal("90"), "hasta": Decimal("120"), "factor": Decimal("0.304"), "rebaja": Decimal("17.80")},
    {"desde": Decimal("120"), "hasta": Decimal("150"), "factor": Decimal("0.35"), "rebaja": Decimal("23.32")},
    {"desde": Decimal("150"), "hasta": None, "factor": Decimal("0.40"), "rebaja": Decimal("30.82")},
]


# =====================================================
# 2. COLUMNAS LRE
# =====================================================

COL_RUT = "Rut trabajador(1101)"
COL_FECHA_TERMINO = "Fecha término de contrato(1103)"
COL_JORNADA = "Código tipo de jornada(1107)"

COL_TOTAL_HABERES_IMP_TRIB = "Total haberes imponibles y tributables(5210)"
COL_TOTAL_HABERES_IMP_NO_TRIB = "Total haberes imponibles no tributables(5220)"
COL_TOTAL_HABERES_NO_IMP_NO_TRIB = "Total haberes no imponibles y no tributables(5230)"

COL_AFP = "Cotización obligatoria previsional (AFP o IPS)(3141)"
COL_SALUD = "Cotización obligatoria salud 7%(3143)"
COL_SALUD_VOLUNTARIA = "Cotización voluntaria para salud(3144)"
COL_AFC_TRAB = "Cotización AFC - trabajador(3151)"
COL_TRABAJO_PESADO_TRAB = "Cotización adicional trabajo pesado - trabajador(3154)"
COL_APVI_MOD_B = "Cotización APVi Mod B hasta UF50(3156)"

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
# 3. SESSION STATE
# =====================================================

def inicializar_estado_1887():
    defaults = {
        "paso_actual_1887": 0,
        "datos_declarante_1887": {},
        "df_lre_mensual_1887": None,
        "df_dj_1887": None,
        "df_resumen_1887": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def ir_a_paso(paso):
    st.session_state.paso_actual_1887 = paso
    st.rerun()


# =====================================================
# 4. FUNCIONES AUXILIARES
# =====================================================

def sii_round(valor):
    try:
        return int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except Exception:
        return 0


def formato_monto(valor):
    try:
        return f"{int(round(float(valor))):,}".replace(",", ".")
    except Exception:
        return "0"


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
    try:
        return int(rut.split("-")[0])
    except Exception:
        return 0


def limpiar_monto(valor):
    if pd.isna(valor) or valor == "":
        return 0

    if isinstance(valor, (int, float)):
        try:
            return int(round(float(valor)))
        except Exception:
            return 0

    texto = str(valor).strip()

    if texto in ["", "-", "nan", "NaN", "None"]:
        return 0

    texto = texto.replace("$", "").replace(" ", "")

    if re.match(r"^-?\d+\.0+$", texto):
        return int(float(texto))

    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
        try:
            return int(round(float(texto)))
        except Exception:
            return 0

    if "." in texto and "," not in texto:
        partes = texto.split(".")
        if len(partes[-1]) == 3:
            texto = texto.replace(".", "")
        else:
            try:
                return int(round(float(texto)))
            except Exception:
                return 0

    if "," in texto and "." not in texto:
        partes = texto.split(",")
        if len(partes[-1]) == 3:
            texto = texto.replace(",", "")
        else:
            texto = texto.replace(",", ".")
            try:
                return int(round(float(texto)))
            except Exception:
                return 0

    try:
        return int(round(float(texto)))
    except Exception:
        return 0


def obtener_serie_monto(df, columna):
    if columna in df.columns:
        return df[columna].apply(limpiar_monto)

    return pd.Series([0] * len(df), index=df.index)


def detectar_mes_desde_nombre(nombre_archivo):
    nombre = nombre_archivo.lower()

    for nombre_mes, codigo_mes in NOMBRE_A_MES.items():
        if nombre_mes in nombre:
            return codigo_mes

    return None


def leer_archivo_lre(file):
    for enc in ["utf-8-sig", "latin1", "cp1252"]:
        try:
            file.seek(0)
            df = pd.read_csv(file, sep=";", encoding=enc)

            if len(df.columns) > 20:
                return df

        except Exception:
            pass

    raise ValueError(f"No se pudo leer el archivo {file.name}.")


# =====================================================
# 5. VALIDACIÓN DE MESES LRE
# =====================================================

def validar_meses_lre(meses_detectados):
    meses_unicos = sorted(set(meses_detectados), key=lambda x: MESES.index(x))

    meses_duplicados = sorted(
        [m for m in set(meses_detectados) if meses_detectados.count(m) > 1],
        key=lambda x: MESES.index(x),
    )

    if meses_duplicados:
        raise ValueError("No se puede avanzar. Existen meses duplicados: " + ", ".join(meses_duplicados))

    if not meses_unicos:
        raise ValueError("No se detectaron meses válidos en los archivos cargados.")

    primer_mes = meses_unicos[0]
    idx_inicio = MESES.index(primer_mes)

    meses_requeridos = MESES[idx_inicio:]
    meses_faltantes = [m for m in meses_requeridos if m not in meses_unicos]

    if meses_faltantes:
        raise ValueError(
            f"No se puede avanzar. Detecté que el primer LRE cargado corresponde a {primer_mes}. "
            f"Desde ese mes deben cargarse todos los LRE hasta diciembre. "
            f"Faltan: {', '.join(meses_faltantes)}"
        )

    return meses_unicos


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

    validar_meses_lre(meses_detectados)

    df_total = pd.concat(registros, ignore_index=True)

    columnas_minimas = [
        COL_RUT,
        COL_TOTAL_HABERES_IMP_TRIB,
        COL_IUSC,
    ]

    faltantes = [c for c in columnas_minimas if c not in df_total.columns]

    if faltantes:
        raise ValueError("El LRE no contiene columnas mínimas requeridas: " + ", ".join(faltantes))

    return df_total


# =====================================================
# 6. INGENIERÍA INVERSA IUSC
# =====================================================

def calcular_iusc_desde_base(base_pesos, mes):
    utm = Decimal(str(UTM_2025[mes]))
    base = Decimal(str(base_pesos))

    for tramo in TRAMOS_IUSC_UTM:
        desde = tramo["desde"] * utm
        hasta = tramo["hasta"] * utm if tramo["hasta"] is not None else None

        if base > desde and (hasta is None or base <= hasta):
            if tramo["factor"] == 0:
                return 0

            impuesto = base * tramo["factor"] - tramo["rebaja"] * utm
            return max(sii_round(impuesto), 0)

    return 0


def inferir_renta_desde_iusc(iusc_mensual, mes):
    impuesto = Decimal(str(int(iusc_mensual)))

    if impuesto <= 0:
        return None

    utm = Decimal(str(UTM_2025[mes]))

    for tramo in TRAMOS_IUSC_UTM:
        if tramo["factor"] == 0:
            continue

        factor = tramo["factor"]
        rebaja_pesos = tramo["rebaja"] * utm

        base = (impuesto + rebaja_pesos) / factor

        desde = tramo["desde"] * utm
        hasta = tramo["hasta"] * utm if tramo["hasta"] is not None else None

        if base > desde and (hasta is None or base <= hasta):
            return sii_round(base)

    return None


# =====================================================
# 7. MOTOR DE CÁLCULO DJ 1887
# =====================================================

def transformar_lre_mensual(df_lre):
    df = df_lre.copy()

    df["Rut_Trabajador"] = df[COL_RUT].apply(normalizar_rut)

    df["Total_Haberes_Imp_Trib"] = obtener_serie_monto(df, COL_TOTAL_HABERES_IMP_TRIB)
    df["Haberes_Imp_No_Trib"] = obtener_serie_monto(df, COL_TOTAL_HABERES_IMP_NO_TRIB)
    df["Haberes_No_Imp_No_Trib"] = obtener_serie_monto(df, COL_TOTAL_HABERES_NO_IMP_NO_TRIB)

    df["Cot_AFP"] = obtener_serie_monto(df, COL_AFP)
    df["Cot_Salud"] = obtener_serie_monto(df, COL_SALUD)
    df["Cot_Salud_Voluntaria"] = obtener_serie_monto(df, COL_SALUD_VOLUNTARIA)
    df["Cot_AFC_Trab"] = obtener_serie_monto(df, COL_AFC_TRAB)
    df["Cot_Trabajo_Pesado_Trab"] = obtener_serie_monto(df, COL_TRABAJO_PESADO_TRAB)
    df["APVI_Mod_B"] = obtener_serie_monto(df, COL_APVI_MOD_B)

    df["IUSC"] = obtener_serie_monto(df, COL_IUSC)
    df["IUSC_Indemnizaciones"] = obtener_serie_monto(df, COL_IUSC_INDEMNIZACIONES)
    df["IUSC_Reliquidacion"] = obtener_serie_monto(df, COL_IUSC_RELIQ)
    df["Diferencia_Reliquidacion"] = obtener_serie_monto(df, COL_DIF_RELIQ)
    df["Mayor_Retencion"] = obtener_serie_monto(df, COL_MAYOR_RETENCION)
    df["Prestamo_3"] = obtener_serie_monto(df, COL_PRESTAMO_3)
    df["Rebaja_Zona_Extrema"] = obtener_serie_monto(df, COL_REBAJA_ZONA)

    df["Total_Cotizaciones_Trabajador"] = obtener_serie_monto(df, COL_TOTAL_COTIZACIONES_TRAB)
    df["Total_Aportes_Empleador"] = obtener_serie_monto(df, COL_TOTAL_APORTES_EMPLEADOR)

    df["Cotizaciones_Deducibles_Renta_Neta"] = (
        df["Cot_AFP"]
        + df["Cot_Salud"]
        + df["Cot_Salud_Voluntaria"]
        + df["Cot_AFC_Trab"]
        + df["Cot_Trabajo_Pesado_Trab"]
        + df["APVI_Mod_B"]
    )

    df["Renta_LRE_Fallback"] = (
        df["Total_Haberes_Imp_Trib"] - df["Cotizaciones_Deducibles_Renta_Neta"]
    ).apply(lambda x: max(int(x), 0))

    df["IUSC_Total_Mensual"] = (
        df["IUSC"]
        + df["IUSC_Indemnizaciones"]
        + df["IUSC_Reliquidacion"]
        + df["Diferencia_Reliquidacion"]
    )

    df["Renta_Inferida_IUSC"] = df.apply(
        lambda row: inferir_renta_desde_iusc(row["IUSC_Total_Mensual"], row["MES_DJ"]),
        axis=1,
    )

    df["Renta_Total_Neta_Mensual"] = df.apply(
        lambda row: int(row["Renta_Inferida_IUSC"])
        if pd.notna(row["Renta_Inferida_IUSC"]) and row["Renta_Inferida_IUSC"] is not None
        else int(row["Renta_LRE_Fallback"]),
        axis=1,
    )

    # Redondeo SII a nivel trabajador-mes antes de cualquier agrupación.
    df["Renta_Total_Neta_Mensual"] = df["Renta_Total_Neta_Mensual"].apply(sii_round)

    df["Metodo_Renta"] = df.apply(
        lambda row: "Inferida desde IUSC"
        if pd.notna(row["Renta_Inferida_IUSC"]) and row["Renta_Inferida_IUSC"] is not None
        else "Fallback LRE",
        axis=1,
    )

    df["Renta_No_Gravada_Mensual"] = (
        df["Haberes_Imp_No_Trib"] + df["Haberes_No_Imp_No_Trib"]
    ).apply(sii_round)

    df["Renta_Exenta_Mensual"] = 0

    df["Monto_Ingreso_Mensual_Sin_Actualizar"] = (
        df["Renta_Total_Neta_Mensual"] + df["Rebaja_Zona_Extrema"]
    ).apply(sii_round)

    df["Factor"] = df["MES_DJ"].map(FACTORES_ACTUALIZACION)

    df["Renta_Total_Neta_Actualizada"] = df.apply(
        lambda row: sii_round(Decimal(str(int(row["Renta_Total_Neta_Mensual"]))) * row["Factor"]),
        axis=1,
    )

    df["IUSC_Actualizado"] = df.apply(
        lambda row: sii_round(Decimal(str(int(row["IUSC_Total_Mensual"]))) * row["Factor"]),
        axis=1,
    )

    df["Mayor_Retencion_Actualizada"] = df.apply(
        lambda row: sii_round(Decimal(str(int(row["Mayor_Retencion"]))) * row["Factor"]),
        axis=1,
    )

    df["Renta_No_Gravada_Actualizada"] = df.apply(
        lambda row: sii_round(Decimal(str(int(row["Renta_No_Gravada_Mensual"]))) * row["Factor"]),
        axis=1,
    )

    df["Renta_Exenta_Actualizada"] = 0

    df["Rebaja_Zona_Extrema_Actualizada"] = df.apply(
        lambda row: sii_round(Decimal(str(int(row["Rebaja_Zona_Extrema"]))) * row["Factor"]),
        axis=1,
    )

    df["Prestamo_3_Actualizado"] = df.apply(
        lambda row: sii_round(Decimal(str(int(row["Prestamo_3"]))) * row["Factor"]),
        axis=1,
    )

    df["Remuneracion_Imponible_Prev_Actualizada"] = df.apply(
        lambda row: sii_round(Decimal(str(int(row["Total_Haberes_Imp_Trib"]))) * row["Factor"]),
        axis=1,
    )

    df["Leyes_Sociales"] = (
        df["Total_Cotizaciones_Trabajador"] + df["Total_Aportes_Empleador"]
    ).apply(sii_round)

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

    columnas_base = [
        "Rut_Trabajador",
        "MES_DJ",
        "Renta_Total_Neta_Mensual",
        "Renta_Inferida_IUSC",
        "Renta_LRE_Fallback",
        "Metodo_Renta",
        "Monto_Ingreso_Mensual_Sin_Actualizar",
        "IUSC",
        "IUSC_Indemnizaciones",
        "IUSC_Total_Mensual",
        "Mayor_Retencion",
        "Renta_No_Gravada_Mensual",
        "Renta_Exenta_Mensual",
        "Rebaja_Zona_Extrema",
        "Prestamo_3",
        "Leyes_Sociales",
        "Total_Haberes_Imp_Trib",
        "Cotizaciones_Deducibles_Renta_Neta",
        "Cot_Salud_Voluntaria",
        "APVI_Mod_B",
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

    df = df[columnas_base].copy()

    # Si existen varias líneas por trabajador-mes, se consolidan primero a nivel trabajador-mes.
    df_tm = df.groupby(["Rut_Trabajador", "MES_DJ"], as_index=False).agg({
        "Renta_Total_Neta_Mensual": "sum",
        "Renta_Inferida_IUSC": "sum",
        "Renta_LRE_Fallback": "sum",
        "Monto_Ingreso_Mensual_Sin_Actualizar": "sum",
        "IUSC": "sum",
        "IUSC_Indemnizaciones": "sum",
        "IUSC_Total_Mensual": "sum",
        "Mayor_Retencion": "sum",
        "Renta_No_Gravada_Mensual": "sum",
        "Renta_Exenta_Mensual": "sum",
        "Rebaja_Zona_Extrema": "sum",
        "Prestamo_3": "sum",
        "Leyes_Sociales": "sum",
        "Total_Haberes_Imp_Trib": "sum",
        "Cotizaciones_Deducibles_Renta_Neta": "sum",
        "Cot_Salud_Voluntaria": "sum",
        "APVI_Mod_B": "sum",
        "Renta_Total_Neta_Actualizada": "sum",
        "IUSC_Actualizado": "sum",
        "Mayor_Retencion_Actualizada": "sum",
        "Renta_No_Gravada_Actualizada": "sum",
        "Renta_Exenta_Actualizada": "sum",
        "Rebaja_Zona_Extrema_Actualizada": "sum",
        "Prestamo_3_Actualizado": "sum",
        "Remuneracion_Imponible_Prev_Actualizada": "sum",
        "Periodo_DJ": lambda x: next((v for v in x if v != ""), ""),
        "Horas_Semanales": "max",
        "ARCHIVO_ORIGEN": lambda x: " | ".join(sorted(set(map(str, x)))),
        "Metodo_Renta": lambda x: " / ".join(sorted(set(map(str, x)))),
    })

    campos_redondeo = [
        "Renta_Total_Neta_Mensual",
        "Monto_Ingreso_Mensual_Sin_Actualizar",
        "IUSC",
        "IUSC_Indemnizaciones",
        "IUSC_Total_Mensual",
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
    ]

    for col in campos_redondeo:
        df_tm[col] = df_tm[col].apply(sii_round)

    return df_tm.copy()


def consolidar_dj_1887(df_mensual):
    df = df_mensual.copy()

    agrupado = df.groupby("Rut_Trabajador").agg({
        "Renta_Total_Neta_Actualizada": "sum",
        "IUSC_Actualizado": "sum",
        "Mayor_Retencion_Actualizada": "sum",
        "Renta_No_Gravada_Actualizada": "sum",
        "Renta_Exenta_Actualizada": "sum",
        "Rebaja_Zona_Extrema_Actualizada": "sum",
        "Prestamo_3_Actualizado": "sum",
        "Renta_Total_Neta_Mensual": "sum",
        "IUSC_Total_Mensual": "sum",
        "Renta_No_Gravada_Mensual": "sum",
        "Renta_Exenta_Mensual": "sum",
        "Rebaja_Zona_Extrema": "sum",
        "Prestamo_3": "sum",
        "Leyes_Sociales": "sum",
        "Remuneracion_Imponible_Prev_Actualizada": "sum",
        "Horas_Semanales": "max",
    }).reset_index()

    pivot_periodos = df.pivot_table(
        index="Rut_Trabajador",
        columns="MES_DJ",
        values="Periodo_DJ",
        aggfunc=lambda x: next((v for v in x if v != ""), ""),
    ).reset_index()

    pivot_ingresos = df.pivot_table(
        index="Rut_Trabajador",
        columns="MES_DJ",
        values="Monto_Ingreso_Mensual_Sin_Actualizar",
        aggfunc="sum",
    ).reset_index()

    for mes in MESES:
        if mes not in pivot_periodos.columns:
            pivot_periodos[mes] = ""

        if mes not in pivot_ingresos.columns:
            pivot_ingresos[mes] = 0

    pivot_ingresos = pivot_ingresos.rename(columns={m: f"Ingreso_{m}" for m in MESES})

    df_final = agrupado.merge(
        pivot_periodos[["Rut_Trabajador"] + MESES],
        on="Rut_Trabajador",
        how="left",
    )

    df_final = df_final.merge(
        pivot_ingresos[["Rut_Trabajador"] + [f"Ingreso_{m}" for m in MESES]],
        on="Rut_Trabajador",
        how="left",
    )

    for mes in MESES:
        df_final[mes] = (
            df_final[mes]
            .fillna("")
            .astype(str)
            .replace(["nan", "NaN", "None"], "")
        )

        df_final[f"Ingreso_{mes}"] = (
            df_final[f"Ingreso_{mes}"]
            .fillna(0)
            .apply(limpiar_monto)
            .apply(sii_round)
        )

    df_final["Rut_Orden"] = df_final["Rut_Trabajador"].apply(rut_a_numero)
    df_final = df_final.sort_values("Rut_Orden").drop(columns=["Rut_Orden"]).reset_index(drop=True)

    df_final.insert(0, "N°", range(1, len(df_final) + 1))
    df_final["Número Certificado"] = range(1, len(df_final) + 1)
    df_final["ESTADO"] = "Calculada por D&D Tax Suite"

    return df_final[
        [
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
        ] + [f"Ingreso_{m}" for m in MESES] + [
            "Horas_Semanales",
            "ESTADO",
            "Renta_Total_Neta_Mensual",
            "IUSC_Total_Mensual",
            "Renta_No_Gravada_Mensual",
            "Renta_Exenta_Mensual",
            "Rebaja_Zona_Extrema",
            "Prestamo_3",
            "Leyes_Sociales",
            "Remuneracion_Imponible_Prev_Actualizada",
        ]
    ].copy()


def generar_resumen_1887(df_dj):
    resumen = {
        "Total Casos Informados": len(df_dj),
        "Renta Total Neta Pagada Actualizada": df_dj["Renta_Total_Neta_Actualizada"].sum(),
        "Impuesto Único Retenido Actualizado": df_dj["IUSC_Actualizado"].sum(),
        "Mayor Retención Solicitada Actualizada": df_dj["Mayor_Retencion_Actualizada"].sum(),
        "Renta Total No Gravada Actualizada": df_dj["Renta_No_Gravada_Actualizada"].sum(),
        "Renta Total Exenta Actualizada": df_dj["Renta_Exenta_Actualizada"].sum(),
        "Rebaja Zonas Extremas Actualizada": df_dj["Rebaja_Zona_Extrema_Actualizada"].sum(),
        "3% Préstamo Tasa 0% Actualizado": df_dj["Prestamo_3_Actualizado"].sum(),
        "Renta Total Neta Pagada Sin Actualizar": df_dj["Renta_Total_Neta_Mensual"].sum(),
        "IUSC Retenido Sin Actualizar": df_dj["IUSC_Total_Mensual"].sum(),
        "Renta No Gravada Sin Actualizar": df_dj["Renta_No_Gravada_Mensual"].sum(),
        "Renta Exenta Sin Actualizar": df_dj["Renta_Exenta_Mensual"].sum(),
        "Rebaja Zona Extrema Sin Actualizar": df_dj["Rebaja_Zona_Extrema"].sum(),
        "Leyes Sociales": df_dj["Leyes_Sociales"].sum(),
        "3% Préstamo Sin Actualizar": df_dj["Prestamo_3"].sum(),
        "Remuneración Imponible Previsional Actualizada": df_dj["Remuneracion_Imponible_Prev_Actualizada"].sum(),
    }

    for mes in MESES:
        resumen[f"Ingreso Mensual {mes} Sin Actualizar"] = df_dj[f"Ingreso_{mes}"].sum()

    return pd.DataFrame({
        "Campo": list(resumen.keys()),
        "Monto": list(resumen.values()),
    })


# =====================================================
# 8. EXPORTACIÓN
# =====================================================

def convertir_a_excel_1887(df_dj, df_resumen, df_mensual):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_dj.to_excel(writer, index=False, sheet_name="DJ_1887")
        df_resumen.to_excel(writer, index=False, sheet_name="Resumen_1887")
        df_mensual.to_excel(writer, index=False, sheet_name="Base_LRE_Mensual")

    output.seek(0)
    return output.getvalue()


# =====================================================
# 9. HTML - TABLAS TIPO SII
# =====================================================

def tabla_html_resumen_1887(df_resumen):
    data = {row["Campo"]: row["Monto"] for _, row in df_resumen.iterrows()}
    anio_40 = st.session_state.datos_declarante_1887.get("anio_40_horas", 2028)
    ingresos = {m: data.get(f"Ingreso Mensual {m} Sin Actualizar", 0) for m in MESES}

    return f"""
<style>
.tabla-sii {{
    width: 100%;
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 12px;
    margin-bottom: 24px;
}}
.tabla-sii th {{
    background-color: #073B53;
    color: white;
    border: 1px solid #D9E2E7;
    padding: 7px;
    text-align: center;
    vertical-align: middle;
}}
.tabla-sii td {{
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #D9E2E7;
    padding: 7px;
    text-align: center;
}}
.tabla-sii .seccion {{
    text-align: left;
    font-weight: bold;
}}
.tabla-sii .monto {{
    font-weight: 600;
}}
</style>

<table class="tabla-sii">
<tr><th colspan="9">TOTAL MONTOS ANUALES SIN ACTUALIZAR</th></tr>
<tr>
<th>Renta Total Neta Pagada<br>(Art.42 N°1, Ley de la Renta)</th>
<th>Impuesto Único de Segunda Categoría Retenido</th>
<th>Impuesto Único Rentas Accesorias</th>
<th>Renta Total No Gravada</th>
<th>Renta Total Exenta</th>
<th>Rebaja Zonas Extremas</th>
<th>Leyes Sociales</th>
<th>3% PRÉSTAMO TASA 0%</th>
<th>Total Remuneración Imponible Previsional Actualizada</th>
</tr>
<tr>
<td class="monto">{formato_monto(data.get("Renta Total Neta Pagada Sin Actualizar", 0))}</td>
<td class="monto">{formato_monto(data.get("IUSC Retenido Sin Actualizar", 0))}</td>
<td class="monto">0</td>
<td class="monto">{formato_monto(data.get("Renta No Gravada Sin Actualizar", 0))}</td>
<td class="monto">{formato_monto(data.get("Renta Exenta Sin Actualizar", 0))}</td>
<td class="monto">{formato_monto(data.get("Rebaja Zona Extrema Sin Actualizar", 0))}</td>
<td class="monto">{formato_monto(data.get("Leyes Sociales", 0))}</td>
<td class="monto">{formato_monto(data.get("3% Préstamo Sin Actualizar", 0))}</td>
<td class="monto">{formato_monto(data.get("Remuneración Imponible Previsional Actualizada", 0))}</td>
</tr>

<tr><th colspan="12">TOTAL MONTO INGRESO MENSUAL (SIN ACTUALIZAR)</th></tr>
<tr>
<th>Enero</th><th>Febrero</th><th>Marzo</th><th>Abril</th><th>Mayo</th><th>Junio</th>
<th>Julio</th><th>Agosto</th><th>Septiembre</th><th>Octubre</th><th>Noviembre</th><th>Diciembre</th>
</tr>
<tr>
<td>{formato_monto(ingresos["ENE"])}</td>
<td>{formato_monto(ingresos["FEB"])}</td>
<td>{formato_monto(ingresos["MAR"])}</td>
<td>{formato_monto(ingresos["ABR"])}</td>
<td>{formato_monto(ingresos["MAY"])}</td>
<td>{formato_monto(ingresos["JUN"])}</td>
<td>{formato_monto(ingresos["JUL"])}</td>
<td>{formato_monto(ingresos["AGO"])}</td>
<td>{formato_monto(ingresos["SEP"])}</td>
<td>{formato_monto(ingresos["OCT"])}</td>
<td>{formato_monto(ingresos["NOV"])}</td>
<td>{formato_monto(ingresos["DIC"])}</td>
</tr>
</table>

<table class="tabla-sii">
<tr><th colspan="9">CUADRO RESUMEN FINAL DE LA DECLARACIÓN</th></tr>
<tr><th colspan="9" class="seccion">Montos Informados</th></tr>
<tr>
<th>Total Casos Informados</th>
<th>Renta Total Neta Pagada</th>
<th>Impuesto Único Retenido</th>
<th>Mayor Retención Solicitada</th>
<th>Renta Total No Gravada</th>
<th>Renta Total Exenta</th>
<th>Rebaja Zonas Extremas</th>
<th>3% PRÉSTAMO TASA 0%</th>
<th>¿En qué año se acogerá plenamente a las 40 horas?</th>
</tr>
<tr>
<td>{formato_monto(data.get("Total Casos Informados", 0))}</td>
<td>{formato_monto(data.get("Renta Total Neta Pagada Actualizada", 0))}</td>
<td>{formato_monto(data.get("Impuesto Único Retenido Actualizado", 0))}</td>
<td>{formato_monto(data.get("Mayor Retención Solicitada Actualizada", 0))}</td>
<td>{formato_monto(data.get("Renta Total No Gravada Actualizada", 0))}</td>
<td>{formato_monto(data.get("Renta Total Exenta Actualizada", 0))}</td>
<td>{formato_monto(data.get("Rebaja Zonas Extremas Actualizada", 0))}</td>
<td>{formato_monto(data.get("3% Préstamo Tasa 0% Actualizado", 0))}</td>
<td>{anio_40}</td>
</tr>

<tr><th colspan="9" class="seccion">Montos Calculados</th></tr>
<tr>
<th>Total Casos Informados</th>
<th>Renta Total Neta Pagada</th>
<th>Impuesto Único Retenido</th>
<th>Mayor Retención Solicitada</th>
<th>Renta Total No Gravada</th>
<th>Renta Total Exenta</th>
<th>Rebaja Zonas Extremas</th>
<th>3% PRÉSTAMO TASA 0%</th>
<th>Estado</th>
</tr>
<tr>
<td>{formato_monto(data.get("Total Casos Informados", 0))}</td>
<td>{formato_monto(data.get("Renta Total Neta Pagada Actualizada", 0))}</td>
<td>{formato_monto(data.get("Impuesto Único Retenido Actualizado", 0))}</td>
<td>{formato_monto(data.get("Mayor Retención Solicitada Actualizada", 0))}</td>
<td>{formato_monto(data.get("Renta Total No Gravada Actualizada", 0))}</td>
<td>{formato_monto(data.get("Renta Total Exenta Actualizada", 0))}</td>
<td>{formato_monto(data.get("Rebaja Zonas Extremas Actualizada", 0))}</td>
<td>{formato_monto(data.get("3% Préstamo Tasa 0% Actualizado", 0))}</td>
<td>Calculado</td>
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
}
.tabla-dj th {
    background-color: #073B53;
    color: white;
    border: 1px solid #D9E2E7;
    padding: 6px;
    text-align: center;
}
.tabla-dj td {
    border: 1px solid #D9E2E7;
    padding: 5px;
    text-align: center;
    color: #1A1A1A;
}
.tabla-dj tr:nth-child(even) { background-color: #F4F7F8; }
.tabla-dj tr:nth-child(odd) { background-color: #FFFFFF; }
.tabla-dj .monto { text-align: right; font-weight: 600; }
</style>

<table class="tabla-dj">
<tr>
<th>N°</th><th>RUT Trabajador</th><th>Renta Total Neta</th><th>IUSC</th><th>Mayor Retención</th>
<th>No Gravada</th><th>Exenta</th><th>Zona Extrema</th><th>3% Préstamo</th>
<th>ENE</th><th>FEB</th><th>MAR</th><th>ABR</th><th>MAY</th><th>JUN</th>
<th>JUL</th><th>AGO</th><th>SEP</th><th>OCT</th><th>NOV</th><th>DIC</th>
<th>N° Cert.</th><th>Horas</th><th>Estado</th>
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
<td>{row["ENE"]}</td><td>{row["FEB"]}</td><td>{row["MAR"]}</td><td>{row["ABR"]}</td>
<td>{row["MAY"]}</td><td>{row["JUN"]}</td><td>{row["JUL"]}</td><td>{row["AGO"]}</td>
<td>{row["SEP"]}</td><td>{row["OCT"]}</td><td>{row["NOV"]}</td><td>{row["DIC"]}</td>
<td>{row["Número Certificado"]}</td>
<td>{row["Horas_Semanales"]}</td>
<td>{row["ESTADO"]}</td>
</tr>
"""

    html += "</table>"
    return html


# =====================================================
# 10. PANTALLAS
# =====================================================

def pantalla_bienvenida():
    st.title("👥 Asistente DJ 1887 - Remuneraciones")

    st.markdown("""
### Automatiza la preparación de la DJ 1887 desde el Libro de Remuneraciones Electrónico

Este módulo consolida los archivos mensuales del LRE, valida continuidad desde el primer mes cargado hasta diciembre, calcula los montos anuales actualizados por trabajador y genera una salida tipo SII.
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
            anio_comercial = st.number_input("Año Comercial", value=ANIO_COMERCIAL_DEFAULT, step=1)

        anio_40_horas = st.selectbox(
            "¿En qué año se acogerá plenamente a las 40 horas?",
            options=[2024, 2025, 2026, 2027, 2028],
            index=4,
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
                "anio_comercial": int(anio_comercial),
                "anio_tributario": int(anio_comercial) + 1,
                "anio_40_horas": int(anio_40_horas),
            }

            ir_a_paso(2)


def pantalla_paso_2():
    st.title("Paso 2: Carga de Libros de Remuneraciones Electrónicos")

    datos = st.session_state.datos_declarante_1887
    anio_comercial = datos.get("anio_comercial", ANIO_COMERCIAL_DEFAULT)

    st.markdown(f"""
Carga los archivos CSV del Libro de Remuneraciones Electrónico correspondientes al año comercial **{anio_comercial}**.

No es obligatorio cargar enero si la empresa aún no tenía trabajadores.  
El sistema detectará el primer mes cargado y exigirá continuidad desde ese mes hasta diciembre.
""")

    files = st.file_uploader(
        f"Sube los archivos LRE CSV del año comercial {anio_comercial}",
        type=["csv"],
        accept_multiple_files=True,
    )

    if files:
        st.write(f"Archivos cargados: {len(files)}")

        with st.expander("Ver archivos cargados"):
            for file in files:
                mes = detectar_mes_desde_nombre(file.name)
                st.write(f"• {file.name} → Mes detectado: {mes if mes else 'No detectado'}")

    if st.button("Validar LRE"):
        try:
            if not files:
                st.error("Debes cargar al menos un archivo LRE en formato CSV.")
                return

            df_lre = cargar_lre_desde_archivos(files)
            df_mensual = transformar_lre_mensual(df_lre)
            df_dj = consolidar_dj_1887(df_mensual)
            df_resumen = generar_resumen_1887(df_dj)

            st.session_state.df_lre_mensual_1887 = df_mensual
            st.session_state.df_dj_1887 = df_dj
            st.session_state.df_resumen_1887 = df_resumen

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
    st.markdown(tabla_html_resumen_1887(df_resumen), unsafe_allow_html=True)

    st.markdown("## Datos de los informados - DJ 1887")
    st.markdown(tabla_html_dj_1887(df_dj), unsafe_allow_html=True)

    with st.expander("Ver base mensual LRE procesada"):
        st.dataframe(df_mensual.reset_index(drop=True), use_container_width=True, hide_index=True)

    with st.expander("Ver tabla DJ 1887 calculada"):
        st.dataframe(df_dj.reset_index(drop=True), use_container_width=True, hide_index=True)

    excel_data = convertir_a_excel_1887(df_dj, df_resumen, df_mensual)

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
            st.rerun()


# =====================================================
# 11. FUNCIÓN PRINCIPAL
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
    st.set_page_config(page_title="D&D Tax Suite - DJ 1887", layout="wide")
    run_1887()
