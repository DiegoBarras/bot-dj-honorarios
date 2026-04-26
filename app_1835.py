import re
import streamlit as st
import pandas as pd
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP


# =====================================================
# 1. PARÁMETROS GENERALES
# =====================================================

ANIO_COMERCIAL_DEFAULT = 2025

MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

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

COLUMNAS_BASE = [
    "Rol_Parte_1",
    "Rol_Parte_2",
    "Codigo_Comuna",
    "Comuna",
    "Rut_Arrendador",
    "Rut_Arrendatario",
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
    "Amoblado",
    "Destino_Arriendo",
    "DFL2",
    "Naturaleza_Bien_Raiz",
]


# =====================================================
# 2. ESTADO DE SESIÓN
# =====================================================

if "paso_actual_1835" not in st.session_state:
    st.session_state.paso_actual_1835 = 0

if "datos_declarante_1835" not in st.session_state:
    st.session_state.datos_declarante_1835 = {}

if "df_base_1835" not in st.session_state:
    st.session_state.df_base_1835 = None

if "df_dj_1835" not in st.session_state:
    st.session_state.df_dj_1835 = None

if "df_resumen_1835" not in st.session_state:
    st.session_state.df_resumen_1835 = None


# =====================================================
# 3. FUNCIONES AUXILIARES
# =====================================================

def ir_a_paso(paso):
    st.session_state.paso_actual_1835 = paso
    st.rerun()


def formato_monto(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except Exception:
        return "0"


def redondear_peso(valor):
    return int(Decimal(valor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def limpiar_monto(valor):
    if pd.isna(valor) or valor == "":
        return 0

    texto = str(valor).strip()
    texto = texto.replace(".", "").replace(",", "")

    if texto == "":
        return 0

    try:
        return int(float(texto))
    except Exception:
        return 0


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


def crear_dataframe_vacio():
    return pd.DataFrame(columns=COLUMNAS_BASE)


def crear_template_excel():
    df_template = pd.DataFrame(columns=COLUMNAS_BASE)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_template.to_excel(writer, index=False, sheet_name="Carga_DJ_1835")

    output.seek(0)
    return output.getvalue()


# =====================================================
# 4. PROCESAMIENTO DJ 1835
# =====================================================

def preparar_dataframe_base(df_input):
    df = df_input.copy()

    for col in COLUMNAS_BASE:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUMNAS_BASE].copy()

    df = df.dropna(how="all").copy()

    for col in COLUMNAS_BASE:
        if col.startswith("Monto_"):
            continue
        df[col] = df[col].fillna("").astype(str).str.strip()

    for col in [f"Monto_{mes}" for mes in MESES]:
        df[col] = df[col].apply(limpiar_monto)

    df["Rut_Arrendador"] = df["Rut_Arrendador"].apply(normalizar_rut)
    df["Rut_Arrendatario"] = df["Rut_Arrendatario"].apply(normalizar_rut)

    df["Amoblado"] = df["Amoblado"].replace("", "1")
    df["Destino_Arriendo"] = df["Destino_Arriendo"].replace("", "2")
    df["Naturaleza_Bien_Raiz"] = df["Naturaleza_Bien_Raiz"].replace("", "2")
    df["DFL2"] = df["DFL2"].str.upper().str.strip()

    return df


def calcular_monto_arriendo(df, aplicar_actualizacion=True):
    df = df.copy()

    for mes in MESES:
        col_monto = f"Monto_{mes}"
        col_actualizado = f"Actualizado_{mes}"

        if aplicar_actualizacion:
            df[col_actualizado] = df[col_monto].apply(
                lambda x: redondear_peso(Decimal(str(int(x))) * FACTORES_ACTUALIZACION[mes])
            )
        else:
            df[col_actualizado] = df[col_monto]

    columnas_actualizadas = [f"Actualizado_{mes}" for mes in MESES]
    df["Monto_Arriendo"] = df[columnas_actualizadas].sum(axis=1)

    for mes in MESES:
        df[mes] = df[f"Monto_{mes}"].apply(lambda x: "X" if x > 0 else "")

    return df


def validar_datos(df, tipo_declarante):
    errores = []
    advertencias = []

    if df.empty:
        errores.append("No existen bienes raíces cargados. Debes ingresar al menos un registro.")
        return errores, advertencias

    for idx, row in df.iterrows():
        fila = idx + 1

        if str(row["Rol_Parte_1"]).strip() == "" or str(row["Rol_Parte_2"]).strip() == "":
            errores.append(f"Fila {fila}: falta completar el Rol del Bien Raíz.")

        if str(row["Codigo_Comuna"]).strip() == "":
            errores.append(f"Fila {fila}: falta código de comuna.")

        if str(row["Comuna"]).strip() == "":
            errores.append(f"Fila {fila}: falta nombre de comuna.")

        if not validar_rut_basico(row["Rut_Arrendador"]):
            errores.append(f"Fila {fila}: RUT arrendador inválido o incompleto.")

        if tipo_declarante == "Corredor / intermediario / mandatario":
            if not validar_rut_basico(row["Rut_Arrendatario"]):
                errores.append(f"Fila {fila}: RUT arrendatario inválido o incompleto.")

        if row["Monto_Arriendo"] <= 0:
            errores.append(f"Fila {fila}: el monto anual de arriendo es cero.")

        if str(row["Amoblado"]) not in ["1", "2"]:
            errores.append(f"Fila {fila}: Amoblado debe ser 1 o 2.")

        if str(row["Destino_Arriendo"]) not in ["1", "2", "3", "4", "5", "6"]:
            errores.append(f"Fila {fila}: Destino del arriendo debe ser un código entre 1 y 6.")

        if str(row["Naturaleza_Bien_Raiz"]) not in ["1", "2"]:
            errores.append(f"Fila {fila}: Naturaleza del bien raíz debe ser 1 o 2.")

        meses_con_monto = [mes for mes in MESES if row[f"Monto_{mes}"] > 0]

        if len(meses_con_monto) == 0:
            advertencias.append(f"Fila {fila}: no tiene meses con monto informado.")

    return errores, advertencias


def generar_dj_1835(df_base, tipo_declarante):
    df = df_base.copy()
    df = df[df["Monto_Arriendo"] > 0].copy()

    df["Rut_Orden"] = df["Rut_Arrendador"].apply(rut_a_numero)
    df = df.sort_values(["Rut_Orden", "Rol_Parte_1", "Rol_Parte_2"]).reset_index(drop=True)
    df = df.drop(columns=["Rut_Orden"])

    df.insert(0, "N°", range(1, len(df) + 1))

    if tipo_declarante == "Arrendatario":
        df["Rut_Arrendatario_DJ"] = ""
    else:
        df["Rut_Arrendatario_DJ"] = df["Rut_Arrendatario"]

    columnas_dj = [
        "N°",
        "Rol_Parte_1",
        "Rol_Parte_2",
        "Codigo_Comuna",
        "Comuna",
        "Rut_Arrendador",
        "Rut_Arrendatario_DJ",
        "Monto_Arriendo",
        "ENE",
        "FEB",
        "MAR",
        "ABR",
        "MAY",
        "JUN",
        "JUL",
        "AGO",
        "SEP",
        "OCT",
        "NOV",
        "DIC",
        "Amoblado",
        "Destino_Arriendo",
        "DFL2",
        "Naturaleza_Bien_Raiz",
    ]

    return df[columnas_dj].copy()


def convertir_a_excel(df_dj, df_resumen, df_base):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_dj.to_excel(writer, index=False, sheet_name="DJ_1835")
        df_resumen.to_excel(writer, index=False, sheet_name="Cuadro_Resumen")
        df_base.to_excel(writer, index=False, sheet_name="Base_Calculo")

    output.seek(0)
    return output.getvalue()


# =====================================================
# 5. HTML
# =====================================================

def tabla_html_resumen_1835(total_casos, total_monto_arriendo):
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
    <th colspan="2" class="seccion">Montos Informados</th>
    <th colspan="2" class="seccion">Montos Calculados</th>
</tr>
<tr>
    <th>Total de casos informados</th>
    <th>Total de Monto Arriendo</th>
    <th>Total de casos informados</th>
    <th>Total de Monto Arriendo</th>
</tr>
<tr>
    <td>{total_casos}</td>
    <td class="monto">{formato_monto(total_monto_arriendo)}</td>
    <td>{total_casos}</td>
    <td class="monto">{formato_monto(total_monto_arriendo)}</td>
</tr>
</table>
"""


def tabla_html_dj_1835(df_dj):
    html = """
<style>
.tabla-dj {
    width: 100%;
    border-collapse: collapse;
    font-family: Arial, sans-serif;
    font-size: 12px;
    margin-top: 10px;
    margin-bottom: 25px;
}
.tabla-dj th {
    background-color: #073B53;
    color: white;
    border: 1px solid #D9E2E7;
    padding: 7px;
    text-align: center;
    vertical-align: middle;
}
.tabla-dj td {
    border: 1px solid #D9E2E7;
    padding: 6px;
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
<th>Rol del Bien Raíz</th>
<th>Comuna Código</th>
<th>Comuna</th>
<th>RUT Arrendador</th>
<th>RUT Arrendatario</th>
<th>Monto Arriendo</th>
<th>ENE</th><th>FEB</th><th>MAR</th><th>ABR</th><th>MAY</th><th>JUN</th>
<th>JUL</th><th>AGO</th><th>SEP</th><th>OCT</th><th>NOV</th><th>DIC</th>
<th>Amoblado</th>
<th>Destino</th>
<th>DFL2</th>
<th>Naturaleza</th>
</tr>
"""

    for _, row in df_dj.iterrows():
        rol = f"{row['Rol_Parte_1']}-{row['Rol_Parte_2']}"

        html += f"""
<tr>
<td>{row["N°"]}</td>
<td>{rol}</td>
<td>{row["Codigo_Comuna"]}</td>
<td>{row["Comuna"]}</td>
<td>{row["Rut_Arrendador"]}</td>
<td>{row["Rut_Arrendatario_DJ"]}</td>
<td class="monto">{formato_monto(row["Monto_Arriendo"])}</td>
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
<td>{row["Amoblado"]}</td>
<td>{row["Destino_Arriendo"]}</td>
<td>{row["DFL2"]}</td>
<td>{row["Naturaleza_Bien_Raiz"]}</td>
</tr>
"""

    html += "</table>"
    return html


# =====================================================
# 6. PANTALLAS
# =====================================================

def pantalla_bienvenida():
    st.title("🏢 Asistente DJ 1835 - Bienes Raíces Arrendados")

    st.markdown("""
    ### Automatiza la preparación de la DJ 1835 en minutos

    Esta herramienta permite preparar la **Declaración Jurada 1835 sobre Bienes Raíces Arrendados**, consolidando la información de inmuebles, arrendadores, períodos de arriendo y montos mensuales pagados o devengados.

    El asistente te guiará paso a paso para:

    1. Registrar los datos del declarante.  
    2. Cargar la información de los bienes raíces arrendados.  
    3. Validar los datos y generar el resumen final estilo SII.  
    4. Descargar un Excel listo para revisión y respaldo.

    Para utilizar este módulo, debes tener a mano los contratos de arriendo, información del rol del bien raíz, comuna, RUT del arrendador y los pagos mensuales del año comercial.
    """)

    if st.button("Comenzar"):
        ir_a_paso(1)


def pantalla_paso_1():
    st.title("Paso 1: Datos del declarante")

    st.markdown("""
    Ingresa la información general de quien presentará la declaración.

    El **Año Tributario** se calcula automáticamente como el año siguiente al **Año Comercial**, ya que esta declaración informa rentas del año comercial anterior.
    """)

    with st.form("form_declarante_1835"):
        col1, col2 = st.columns(2)

        with col1:
            nombre_declarante = st.text_input("Nombre o Razón Social")
            rut_declarante = st.text_input("RUT Empresa Declarante")

        with col2:
            anio_comercial = st.number_input(
                "Año Comercial",
                value=ANIO_COMERCIAL_DEFAULT,
                step=1,
            )

            anio_tributario = int(anio_comercial) + 1
            

        tipo_declarante = st.selectbox(
            "Tipo de declarante",
            ["Arrendatario", "Corredor / intermediario / mandatario"],
        )

        aplicar_actualizacion = st.checkbox(
            "Aplicar factores de actualización mensual al 31 de diciembre",
            value=True,
        )

        st.caption(
            "Si ingresas montos históricos mensuales, deja esta opción marcada. "
            "Si ingresas montos ya actualizados, desmárcala."
        )

        guardar = st.form_submit_button("Guardar y continuar")

    if guardar:
        errores = []

        if nombre_declarante.strip() == "":
            errores.append("Debes ingresar el nombre o razón social del declarante.")

        if not validar_rut_basico(rut_declarante):
            errores.append("Debes ingresar un RUT válido con formato 12345678-9.")

        if errores:
            for error in errores:
                st.error(error)
        else:
            st.session_state.datos_declarante_1835 = {
                "nombre_declarante": nombre_declarante.strip(),
                "rut_declarante": normalizar_rut(rut_declarante),
                "anio_comercial": int(anio_comercial),
                "anio_tributario": int(anio_tributario),
                "tipo_declarante": tipo_declarante,
                "aplicar_actualizacion": aplicar_actualizacion,
            }

            st.success("Paso 1 guardado correctamente.")
            ir_a_paso(2)


def pantalla_selector_carga():
    st.title("Paso 2: Método de carga de bienes raíces arrendados")

    st.markdown("""
    En este paso debes cargar la información de los bienes raíces arrendados durante el año comercial.

    Puedes elegir una de dos formas de trabajo:
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### Opción A: Carga masiva Excel

        Recomendada cuando tienes varios inmuebles o trabajas como estudio contable.

        Descarga una plantilla, complétala con la información de cada bien raíz y vuelve a subirla al sistema.
        """)

        if st.button("Usar carga Excel"):
            ir_a_paso("2A")

    with col2:
        st.markdown("""
        ### Opción B: Carga manual

        Recomendada cuando tienes pocos inmuebles o quieres ingresar la información directamente en pantalla.

        El sistema abrirá una tabla editable para completar cada bien raíz arrendado.
        """)

        if st.button("Usar carga manual"):
            ir_a_paso("2B")

    st.markdown("---")

    if st.button("Volver al Paso 1"):
        ir_a_paso(1)


def procesar_y_validar_paso_2(df_editado):
    datos_declarante = st.session_state.datos_declarante_1835

    df_base = preparar_dataframe_base(df_editado)

    df_base = calcular_monto_arriendo(
        df_base,
        aplicar_actualizacion=datos_declarante["aplicar_actualizacion"],
    )

    errores, advertencias = validar_datos(
        df_base,
        datos_declarante["tipo_declarante"],
    )

    if errores:
        st.error("Existen errores que deben corregirse antes de continuar.")
        for error in errores:
            st.write(f"❌ {error}")
        return

    st.session_state.df_base_1835 = df_base

    if advertencias:
        st.warning("Advertencias para revisión:")
        for adv in advertencias:
            st.write(f"⚠️ {adv}")

    st.success("Paso 2 cargado correctamente. La información fue validada.")
    ir_a_paso(3)


def pantalla_carga_excel():
    st.title("Paso 2A: Carga masiva mediante Excel")

    # 🔹 Descripción simple (UX limpia)
    st.markdown("""
Descarga la plantilla, completa una fila por cada bien raíz arrendado y vuelve a subir el archivo.

La plantilla permite cargar los datos del inmueble, RUT del arrendador y los montos mensuales de arriendo.
""")

    # 🔹 Guía colapsable (mejor UX)
    with st.expander("Ver guía de llenado de la plantilla Excel"):
        st.markdown("""
Completa **una fila por cada bien raíz arrendado**.

### 📌 Campos principales

| Campo | Cómo completarlo |
|---|---|
| Rol_Parte_1 / Rol_Parte_2 | Rol del bien raíz separado en dos partes. Ej: `61` y `328`. |
| Codigo_Comuna / Comuna | Código y nombre de la comuna según SII. |
| Rut_Arrendador | RUT de quien recibe la renta. |
| Rut_Arrendatario | Solo si aplica (corredor/intermediario). |
| Monto_ENE a Monto_DIC | Monto pagado en cada mes. Si no hubo pago, dejar vacío o 0. |

### 🔢 Códigos importantes

| Campo | Código | Significado |
|---|---:|---|
| Amoblado | 1 | Sin amoblar |
| Amoblado | 2 | Amoblado o con instalaciones |
| Destino_Arriendo | 1 | Habitacional |
| Destino_Arriendo | 2 | Comercial |
| Destino_Arriendo | 3 | Estacionamiento |
| Destino_Arriendo | 4 | Bodega |
| Destino_Arriendo | 5 | Habitacional y comercial |
| Destino_Arriendo | 6 | Otro destino |
| DFL2 | X | Vivienda acogida a DFL N°2 |
| DFL2 | vacío | No aplica |
| Naturaleza_Bien_Raiz | 1 | Agrícola |
| Naturaleza_Bien_Raiz | 2 | No agrícola |

### ⚠️ Reglas importantes

- Ingresa los montos **exactos pagados cada mes**
- Si un mes no tiene pago → dejar vacío o 0
- No usar fórmulas en Excel (solo valores)
- Revisar que los RUT estén correctamente escritos
""")

    # 🔹 Botón descarga plantilla
    template_excel = crear_template_excel()

    st.download_button(
        label="📥 Descargar plantilla Excel DJ 1835",
        data=template_excel,
        file_name="Plantilla_DJ_1835_Arrendamientos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # 🔹 Upload archivo
    archivo_excel = st.file_uploader(
        "Sube la plantilla Excel completada",
        type=["xlsx"]
    )

    # 🔹 Procesamiento
    if archivo_excel:
        df_input = pd.read_excel(archivo_excel)

        st.markdown("### 🔍 Revisión de información cargada")

        df_editado = st.data_editor(
            df_input,
            use_container_width=True,
            num_rows="dynamic"
        )

        if st.button("Cargar Paso 2"):
            try:
                st.session_state.df_1835 = df_editado
                st.success("Paso 2 cargado correctamente")
                ir_a_paso(3)
            except Exception as e:
                st.error(f"Error en la carga: {e}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅️ Volver a elegir método"):
            ir_a_paso(2)

    with col2:
        if st.button("⬅️ Volver al Paso 1"):
            ir_a_paso(1)

def pantalla_carga_manual():
    st.title("Paso 2B: Carga manual en pantalla")

    st.markdown("""
    Ingresa directamente la información de cada bien raíz arrendado.

    Cada fila corresponde a un inmueble o registro informado en la DJ. Puedes agregar nuevas filas desde la tabla.
    """)

    df_input = crear_dataframe_vacio()

    df_editado = st.data_editor(
        df_input,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )

    if st.button("Validar y continuar"):
        procesar_y_validar_paso_2(df_editado)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Volver a elegir método"):
            ir_a_paso(2)

    with col2:
        if st.button("Volver al Paso 1"):
            ir_a_paso(1)


def pantalla_paso_3():
    st.title("Paso 3: Generar DJ 1835")

    datos_declarante = st.session_state.datos_declarante_1835
    df_base = st.session_state.df_base_1835.copy()

    st.markdown("""
    La información ya fue cargada y validada.

    Ahora puedes generar el resumen final de la Declaración Jurada 1835 y descargar el archivo Excel de respaldo.
    """)

    if st.button("Generar DJ 1835"):
        df_dj = generar_dj_1835(
            df_base,
            datos_declarante["tipo_declarante"],
        )

        total_casos = len(df_dj)
        total_monto_arriendo = df_dj["Monto_Arriendo"].sum()

        df_resumen = pd.DataFrame({
            "Campo": [
                "Total de casos informados",
                "Total de Monto Arriendo",
            ],
            "Monto": [
                total_casos,
                total_monto_arriendo,
            ],
        })

        st.session_state.df_dj_1835 = df_dj
        st.session_state.df_resumen_1835 = df_resumen

    if st.session_state.df_dj_1835 is not None:
        df_dj = st.session_state.df_dj_1835
        df_resumen = st.session_state.df_resumen_1835

        total_casos = len(df_dj)
        total_monto_arriendo = df_dj["Monto_Arriendo"].sum()

        st.success("DJ 1835 generada correctamente.")

        st.markdown("## Detalle consulta declaración jurada")

        st.markdown(f"""
        **Nombre o Razón Social:** {datos_declarante["nombre_declarante"]}  
        **RUT Empresa Declarante:** {datos_declarante["rut_declarante"]}  
        **Año Tributario:** {datos_declarante["anio_tributario"]}  
        **Año Comercial:** {datos_declarante["anio_comercial"]}
        """)

        st.markdown("## Resumen final de la declaración")
        st.markdown(
            tabla_html_resumen_1835(total_casos, total_monto_arriendo),
            unsafe_allow_html=True,
        )

        st.markdown("## Datos de los bienes raíces informados - DJ 1835")
        st.markdown(
            tabla_html_dj_1835(df_dj),
            unsafe_allow_html=True,
        )

        with st.expander("Ver base de cálculo mensual"):
            st.dataframe(
                df_base.reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )

        excel_data = convertir_a_excel(df_dj, df_resumen, df_base)

        st.download_button(
            label="📥 Descargar Excel DJ 1835",
            data=excel_data,
            file_name="DJ_1835_Arrendamientos_DD_Contable.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Volver al Paso 2"):
            ir_a_paso(2)

    with col2:
        if st.button("Reiniciar asistente"):
            st.session_state.paso_actual_1835 = 0
            st.session_state.datos_declarante_1835 = {}
            st.session_state.df_base_1835 = None
            st.session_state.df_dj_1835 = None
            st.session_state.df_resumen_1835 = None
            st.rerun()


# =====================================================
# 7. ROUTER PRINCIPAL
# =====================================================


def run_1835():
    paso = st.session_state.paso_actual_1835

    if paso == 0:
        pantalla_bienvenida()

    elif paso == 1:
        pantalla_paso_1()

    elif paso == 2:
        pantalla_selector_carga()

    elif paso == "2A":
        pantalla_carga_excel()

    elif paso == "2B":
        pantalla_carga_manual()

    elif paso == 3:
        pantalla_paso_3()
