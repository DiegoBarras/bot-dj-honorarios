import streamlit as st

from app_1879 import run_1879
from app_1835 import run_1835
from app_1887 import run_1887

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

st.set_page_config(
    page_title="D&D Tax Suite",
    page_icon="📊",
    layout="wide",
)


# =====================================================
# ESTADO DE NAVEGACIÓN
# =====================================================

if "modulo_activo" not in st.session_state:
    st.session_state.modulo_activo = "home"


def ir_a(modulo):
    st.session_state.modulo_activo = modulo
    st.rerun()


# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }

    .hero {
        padding: 48px 42px;
        border-radius: 24px;
        background: linear-gradient(135deg, #073B53 0%, #0E1117 65%);
        border: 1px solid #1f3b4d;
        margin-bottom: 34px;
    }

    .hero h1 {
        font-size: 54px;
        font-weight: 850;
        color: #FFFFFF;
        margin-bottom: 14px;
    }

    .hero p {
        font-size: 20px;
        color: #D9E2E7;
        max-width: 950px;
        line-height: 1.55;
    }

    .badge {
        display: inline-block;
        background-color: #1E5168;
        color: #FFFFFF;
        padding: 8px 15px;
        border-radius: 999px;
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 18px;
    }

    .section-title {
        font-size: 30px;
        font-weight: 850;
        color: #FFFFFF;
        margin-top: 24px;
        margin-bottom: 8px;
    }

    .section-subtitle {
        font-size: 16px;
        color: #B8C7D1;
        margin-bottom: 24px;
        line-height: 1.55;
    }

    .module-card {
        background-color: #111827;
        border: 1px solid #263747;
        border-radius: 22px;
        padding: 28px;
        min-height: 305px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        margin-bottom: 18px;
    }

    .module-card h3 {
        color: #FFFFFF;
        font-size: 25px;
        margin-bottom: 10px;
    }

    .module-card p {
        color: #C8D3DA;
        font-size: 15px;
        line-height: 1.5;
    }

    .status-ready {
        color: #3DDC84;
        font-weight: 800;
        font-size: 14px;
    }

    .status-next {
        color: #F4C542;
        font-weight: 800;
        font-size: 14px;
    }

    .metric-card {
        background-color: #0F172A;
        border: 1px solid #263747;
        padding: 22px;
        border-radius: 18px;
        min-height: 120px;
    }

    .metric-card h4 {
        color: #FFFFFF;
        font-size: 18px;
        margin-bottom: 6px;
    }

    .metric-card p {
        color: #B8C7D1;
        font-size: 14px;
        line-height: 1.45;
    }

    .footer {
        margin-top: 44px;
        padding-top: 24px;
        border-top: 1px solid #263747;
        color: #8FA3B0;
        font-size: 14px;
    }

    div.stButton > button {
        border-radius: 12px;
        padding: 0.65rem 1rem;
        font-weight: 700;
        border: 1px solid #1E5168;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.markdown("## 📊 D&D Tax Suite")
    st.caption("Tax automation platform")

    st.markdown("---")

    if st.button("🏠 Inicio", use_container_width=True):
        ir_a("home")

    if st.button("DJ 1879 · Honorarios", use_container_width=True):
        ir_a("1879")

    if st.button("DJ 1835 · Arrendamientos", use_container_width=True):
        ir_a("1835")
    
    if st.button("DJ 1887 · Remuneraciones", use_container_width=True):
        ir_a("1887")

    st.markdown("---")
    st.caption("Módulos futuros")
    st.write("• DJ Sueldos / Remuneraciones")
    st.write("• DJ Dividendos")
    st.write("• DJ Retiros")
    st.write("• Declaraciones mensuales")


# =====================================================
# HOME
# =====================================================

def mostrar_home():

    st.markdown("""
    <div class="hero">
        <div class="badge">D&D Contable · Tax Automation Platform</div>
        <h1>📊 D&D Tax Suite</h1>
        <p>
            Una plataforma diseñada para automatizar, validar y preparar Declaraciones Juradas del SII
            con lógica tributaria, controles de consistencia y salidas listas para revisión profesional.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Bienvenido a tu centro de automatización tributaria</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="section-subtitle">
    D&D Tax Suite centraliza asistentes especializados para declaraciones juradas, cálculos tributarios,
    validaciones de datos y generación de reportes. La suite está pensada para estudios contables,
    equipos de finanzas y empresas que buscan reducir errores, ahorrar tiempo y mantener trazabilidad.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Automatización tributaria</h4>
            <p>Convierte procesos manuales en flujos guiados, validados y repetibles.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Validación tipo SII</h4>
            <p>Reglas de negocio, cuadraturas y alertas de consistencia antes de declarar.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Outputs profesionales</h4>
            <p>Tablas resumen, detalle por informado y archivos Excel para revisión.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Módulos disponibles</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="section-subtitle">
    Selecciona el asistente tributario que deseas utilizar. Cada módulo funciona como una solución especializada
    y forma parte del ecosistema D&D Tax Suite.
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown("""
        <div class="module-card">
            <p class="status-ready">● Disponible</p>
            <h3>DJ 1879 Honorarios</h3>
            <p>
                Automatiza la Declaración Jurada 1879 a partir de archivos mensuales de Boletas de Honorarios
                Recibidas descargados desde el SII.
            </p>
            <p>
                Consolida, excluye documentos no vigentes, actualiza retenciones y separa retenciones adicionales.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Abrir DJ 1879", use_container_width=True):
            ir_a("1879")

    with m2:
        st.markdown("""
        <div class="module-card">
            <p class="status-ready">● Disponible</p>
            <h3>DJ 1835 Arrendamientos</h3>
            <p>
                Asistente guiado para preparar la Declaración Jurada 1835 sobre bienes raíces arrendados.
            </p>
            <p>
                Permite carga manual o vía Excel, validación de datos y generación de resumen tipo SII.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Abrir DJ 1835", use_container_width=True):
            ir_a("1835")

    with m3:
        st.markdown("""
        <div class="module-card">
            <p class="status-ready">● Disponible</p>
            <h3>DJ 1887 Remuneraciones</h3>
            <p>
                Consolida los 12 archivos mensuales del Libro de Remuneraciones Electrónico,
                valida meses faltantes y genera una salida tipo SII.
            </p>
            <p>
                Incluye resumen anual, detalle por trabajador y comparación opcional contra propuesta SII.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Abrir DJ 1887", use_container_width=True):
            ir_a("1887")

        st.markdown(
            '<div class="section-title">Roadmap de producto</div>',
            unsafe_allow_html=True
        )

    r1, r2, r3, r4 = st.columns(4)

    with r1:
        st.markdown("""
        <div class="metric-card">
            <h4>1. Módulos DJ</h4>
            <p>Automatización por declaración jurada.</p>
        </div>
        """, unsafe_allow_html=True)

    with r2:
        st.markdown("""
        <div class="metric-card">
            <h4>2. Usuarios</h4>
            <p>Acceso privado para equipo y clientes autorizados.</p>
        </div>
        """, unsafe_allow_html=True)

    with r3:
        st.markdown("""
        <div class="metric-card">
            <h4>3. Historial</h4>
            <p>Declaraciones por cliente, año y módulo.</p>
        </div>
        """, unsafe_allow_html=True)

    with r4:
        st.markdown("""
        <div class="metric-card">
            <h4>4. Panel de control</h4>
            <p>Seguimiento de procesos tributarios y estados.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="footer">
        D&D Tax Suite · Automatización tributaria desarrollada para D&D Contable.
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# ROUTER PRINCIPAL
# =====================================================

if st.session_state.modulo_activo == "home":
    mostrar_home()

elif st.session_state.modulo_activo == "1879":
    st.button("← Volver al inicio", on_click=lambda: ir_a("home"))
    run_1879()

elif st.session_state.modulo_activo == "1835":
    st.button("← Volver al inicio", on_click=lambda: ir_a("home"))
    run_1835()
elif st.session_state.modulo_activo == "1887":
    st.button("← Volver al inicio", on_click=lambda: ir_a("home"))
    run_1887()
