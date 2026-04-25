import streamlit as st

st.set_page_config(
    page_title="D&D Tax Suite",
    page_icon="📊",
    layout="wide",
)

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>
    .main {
        background-color: #0E1117;
    }

    .hero {
        padding: 48px 40px;
        border-radius: 22px;
        background: linear-gradient(135deg, #073B53 0%, #0E1117 60%);
        border: 1px solid #1f3b4d;
        margin-bottom: 32px;
    }

    .hero h1 {
        font-size: 52px;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 12px;
    }

    .hero p {
        font-size: 20px;
        color: #D9E2E7;
        max-width: 900px;
        line-height: 1.55;
    }

    .badge {
        display: inline-block;
        background-color: #1E5168;
        color: #FFFFFF;
        padding: 8px 14px;
        border-radius: 999px;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 18px;
    }

    .section-title {
        font-size: 30px;
        font-weight: 800;
        color: #FFFFFF;
        margin-top: 18px;
        margin-bottom: 8px;
    }

    .section-subtitle {
        font-size: 17px;
        color: #B8C7D1;
        margin-bottom: 24px;
    }

    .module-card {
        background-color: #111827;
        border: 1px solid #263747;
        border-radius: 20px;
        padding: 26px;
        min-height: 275px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }

    .module-card h3 {
        color: #FFFFFF;
        font-size: 24px;
        margin-bottom: 8px;
    }

    .module-card p {
        color: #C8D3DA;
        font-size: 15px;
        line-height: 1.5;
    }

    .status-ready {
        color: #3DDC84;
        font-weight: 700;
        font-size: 14px;
    }

    .status-next {
        color: #F4C542;
        font-weight: 700;
        font-size: 14px;
    }

    .status-soon {
        color: #8FA3B0;
        font-weight: 700;
        font-size: 14px;
    }

    .metric-card {
        background-color: #0F172A;
        border: 1px solid #263747;
        padding: 22px;
        border-radius: 18px;
    }

    .metric-card h4 {
        color: #FFFFFF;
        font-size: 18px;
        margin-bottom: 6px;
    }

    .metric-card p {
        color: #B8C7D1;
        font-size: 14px;
    }

    .footer {
        margin-top: 44px;
        padding-top: 24px;
        border-top: 1px solid #263747;
        color: #8FA3B0;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================
# HERO
# =====================================================

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


# =====================================================
# INTRO
# =====================================================

st.markdown('<div class="section-title">Bienvenido a tu centro de automatización tributaria</div>', unsafe_allow_html=True)

st.markdown("""
<div class="section-subtitle">
D&D Tax Suite centraliza asistentes especializados para declaraciones juradas, cálculos tributarios,
validaciones de datos y generación de reportes. La suite está pensada para estudios contables,
equipos de finanzas y empresas que buscan reducir errores, ahorrar tiempo y mantener trazabilidad.
</div>
""", unsafe_allow_html=True)


# =====================================================
# VALUE PROPOSITION
# =====================================================

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
        <p>Los módulos incorporan reglas de negocio, cuadraturas y alertas de consistencia.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h4>Outputs profesionales</h4>
        <p>Genera tablas resumen, detalle por informado y archivos Excel para revisión.</p>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# MODULES
# =====================================================

st.markdown('<div class="section-title">Módulos disponibles</div>', unsafe_allow_html=True)
st.markdown("""
<div class="section-subtitle">
Selecciona el asistente tributario que deseas utilizar. Cada módulo está diseñado como una solución independiente,
pero preparada para integrarse dentro de una plataforma única.
</div>
""", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown("""
    <div class="module-card">
        <p class="status-ready">● Disponible</p>
        <h3>DJ 1879 Honorarios</h3>
        <p>
            Automatiza la preparación de la Declaración Jurada 1879 a partir de archivos mensuales
            de Boletas de Honorarios Recibidas del SII.
        </p>
        <p>
            Incluye consolidación anual, exclusión de documentos no vigentes, actualización monetaria,
            separación de retenciones adicionales y Excel final.
        </p>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown("""
    <div class="module-card">
        <p class="status-ready">● Disponible</p>
        <h3>DJ 1835 Arrendamientos</h3>
        <p>
            Asistente guiado para preparar la Declaración Jurada 1835 sobre bienes raíces arrendados.
        </p>
        <p>
            Permite carga manual o masiva vía Excel, validación de datos, cálculo de montos anuales
            y salida tipo SII.
        </p>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown("""
    <div class="module-card">
        <p class="status-next">● Próximo módulo</p>
        <h3>DJ Sueldos / Remuneraciones</h3>
        <p>
            Futuro asistente para declaraciones asociadas a remuneraciones, sueldos, impuestos únicos
            y cuadraturas laborales.
        </p>
        <p>
            Diseñado para integrarse con planillas de remuneraciones y reportes contables.
        </p>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# ROADMAP
# =====================================================

st.markdown('<div class="section-title">Roadmap de la Suite</div>', unsafe_allow_html=True)

r1, r2, r3, r4 = st.columns(4)

with r1:
    st.markdown("""
    <div class="metric-card">
        <h4>1. Módulos DJ</h4>
        <p>Honorarios, arrendamientos y futuras declaraciones anuales.</p>
    </div>
    """, unsafe_allow_html=True)

with r2:
    st.markdown("""
    <div class="metric-card">
        <h4>2. Hall integrado</h4>
        <p>Acceso centralizado a todos los asistentes desde una sola interfaz.</p>
    </div>
    """, unsafe_allow_html=True)

with r3:
    st.markdown("""
    <div class="metric-card">
        <h4>3. Login usuarios</h4>
        <p>Acceso privado para equipo D&D Contable y clientes autorizados.</p>
    </div>
    """, unsafe_allow_html=True)

with r4:
    st.markdown("""
    <div class="metric-card">
        <h4>4. Historial cliente</h4>
        <p>Control de declaraciones, años tributarios, archivos y respaldos.</p>
    </div>
    """, unsafe_allow_html=True)


# =====================================================
# CTA / NEXT STEP
# =====================================================

st.markdown("---")

st.markdown("""
### Estado actual

Esta es la primera versión del **Hall de Entrada** de D&D Tax Suite.

Los módulos ya existen como archivos separados:

- `app_1879.py` → DJ 1879 Honorarios
- `app_1835.py` → DJ 1835 Arrendamientos

El siguiente paso será conectar estos módulos al hall para que el usuario pueda navegar dentro de una sola aplicación.
""")

st.info("Siguiente paso recomendado: integrar navegación interna entre módulos dentro de la misma app.")

st.markdown("""
<div class="footer">
    D&D Tax Suite · Automatización tributaria desarrollada para D&D Contable.
</div>
""", unsafe_allow_html=True)
