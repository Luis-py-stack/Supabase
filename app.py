import streamlit as st
from supabase import create_client, Client

# ==========================================
# Configuración de la página
# ==========================================
st.set_page_config(
    page_title="Visor y Gestor Supabase",
    page_icon="⚡",
    layout="wide"
)

st.title("Visor y Gestor de Datos")
#st.markdown("""
#Esta interfaz funciona exclusivamente como un visor. **No almacena ni cachea datos en memoria**.
#Todas las lecturas y escrituras se hacen en tiempo real directamente hacia Supabase.
#""")

# ==========================================
# 1. Inputs de Configuración (Barra Lateral)
# ==========================================
st.sidebar.header("🔑 Configuración de Conexión")
supabase_url = st.sidebar.text_input("SUPABASE_URL", placeholder="https://xyz.supabase.co")
supabase_key = st.sidebar.text_input("SUPABASE_KEY", type="password", placeholder="sb_secret_...")
table_name = st.sidebar.text_input("TABLE_NAME", value="Pantallas_De_Mcdonalds")

# Verificación de credenciales
if not supabase_url or not supabase_key or not table_name:
    st.info("👈 Por favor, ingresa tus credenciales de Supabase en la barra lateral para comenzar.")
    st.stop() # Detiene la ejecución hasta que haya credenciales

# ==========================================
# Inicialización del Cliente Supabase
# ==========================================
try:
    # Se inicializa el cliente en cada ejecución (stateless) usando los inputs actuales
    supabase: Client = create_client(supabase_url, supabase_key)
except Exception as e:
    st.error(f"Error al inicializar el cliente de Supabase: {e}")
    st.stop()

st.divider()

# Layout en dos columnas para mejor experiencia de usuario
col_form, col_view = st.columns([1, 5.001], gap="large")

# ==========================================
# 2. Área de Carga / Modificación / Borrado
# ==========================================
with col_form:
    # Usamos pestañas para mantener el diseño delgado y ordenado
    tab_insert, tab_update, tab_delete = st.tabs(["➕ Insertar", "✏️ Actualizar", "🗑️ Eliminar"])

    # ----------------------------------------
    # PESTAÑA: INSERTAR (INTACTO)
    # ----------------------------------------
    with tab_insert:
        st.subheader("Nuevo Registro")
        with st.form("insert_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            
            with f_col1:
                input_folio = st.text_input("FOLIO")
                input_cliente = st.text_input("CLIENTE")
                input_clasificacion = st.text_input("CLASIFICACION")
                input_f_visita = st.text_input("F_VISITA")
                input_f_entrega = st.text_input("F_ENTREGA")
                input_avance = st.text_input("AVANCE")
                
            with f_col2:
                input_area = st.text_input("AREA")
                input_concepto = st.text_input("CONCEPTO")
                input_vendedor = st.text_input("VENDEDOR")
                input_f_inicio = st.text_input("F_INICIO")
                input_dias = st.number_input("DIAS", step=1, value=0)

            st.markdown("<br>", unsafe_allow_html=True) 
            btn_submit = st.form_submit_button("Guardar en Supabase", type="primary", use_container_width=True)

            if btn_submit:
                data_to_insert = {
                    "FOLIO": input_folio,
                    "AREA": input_area,
                    "CLIENTE": input_cliente,
                    "CONCEPTO": input_concepto,
                    "CLASIFICACION": input_clasificacion,
                    "VENDEDOR": input_vendedor,
                    "F_VISITA": input_f_visita,
                    "F_INICIO": input_f_inicio,
                    "F_ENTREGA": input_f_entrega,
                    "DIAS": input_dias,
                    "AVANCE": input_avance
                }
                try:
                    response = supabase.table(table_name).insert(data_to_insert).execute()
                    st.success(f"¡Datos insertados! (FOLIO: {input_folio})")
                except Exception as e:
                    st.error("Error al insertar los datos.")
                    st.error(f"Detalle técnico: {e}")

    # ----------------------------------------
    # PESTAÑA: ACTUALIZAR (NUEVO)
    # ----------------------------------------
    with tab_update:
        st.subheader("Modificar Registro")
        with st.form("update_form", clear_on_submit=True):
            update_folio = st.text_input("🔍 FOLIO a modificar (Obligatorio)*")
            st.caption("Llena **solo** los campos que deseas cambiar:")
            
            u_col1, u_col2 = st.columns(2)
            with u_col1:
                u_cliente = st.text_input("NUEVO CLIENTE")
                u_clasificacion = st.text_input("NUEVA CLASIFICACION")
                u_f_visita = st.text_input("NUEVA F_VISITA")
                u_f_entrega = st.text_input("NUEVA F_ENTREGA")
                u_avance = st.text_input("NUEVO AVANCE")
            with u_col2:
                u_area = st.text_input("NUEVA AREA")
                u_concepto = st.text_input("NUEVO CONCEPTO")
                u_vendedor = st.text_input("NUEVO VENDEDOR")
                u_f_inicio = st.text_input("NUEVA F_INICIO")
                u_dias = st.text_input("NUEVOS DIAS") # Usamos texto para permitir que se deje en blanco

            st.markdown("<br>", unsafe_allow_html=True)
            btn_update = st.form_submit_button("Actualizar en Supabase", type="primary", use_container_width=True)

            if btn_update:
                if not update_folio:
                    st.error("Debes ingresar el FOLIO que deseas modificar.")
                else:
                    # Construimos el payload dinámicamente solo con los campos que no están vacíos
                    update_payload = {}
                    if u_cliente: update_payload["CLIENTE"] = u_cliente
                    if u_clasificacion: update_payload["CLASIFICACION"] = u_clasificacion
                    if u_f_visita: update_payload["F_VISITA"] = u_f_visita
                    if u_f_entrega: update_payload["F_ENTREGA"] = u_f_entrega
                    if u_avance: update_payload["AVANCE"] = u_avance
                    if u_area: update_payload["AREA"] = u_area
                    if u_concepto: update_payload["CONCEPTO"] = u_concepto
                    if u_vendedor: update_payload["VENDEDOR"] = u_vendedor
                    if u_f_inicio: update_payload["F_INICIO"] = u_f_inicio
                    if u_dias: 
                        try:
                            update_payload["DIAS"] = int(u_dias)
                        except ValueError:
                            st.warning("El campo DIAS no se actualizó porque no es un número entero.")

                    if not update_payload:
                        st.warning("No ingresaste ningún dato nuevo para actualizar.")
                    else:
                        try:
                            response = supabase.table(table_name).update(update_payload).eq("FOLIO", update_folio).execute()
                            if len(response.data) > 0:
                                st.success(f"¡Registro {update_folio} actualizado correctamente!")
                            else:
                                st.error(f"No se encontró el FOLIO: {update_folio}")
                        except Exception as e:
                            st.error("Error al actualizar los datos.")
                            st.error(f"Detalle técnico: {e}")

    # ----------------------------------------
    # PESTAÑA: ELIMINAR (NUEVO)
    # ----------------------------------------
    with tab_delete:
        st.subheader("Borrar Registro")
        with st.form("delete_form", clear_on_submit=True):
            delete_folio = st.text_input("🗑️ FOLIO a eliminar (Obligatorio)*")
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_delete = st.form_submit_button("Eliminar Definitivamente", type="primary", use_container_width=True)

            if btn_delete:
                if not delete_folio:
                    st.error("Debes ingresar el FOLIO que deseas eliminar.")
                else:
                    try:
                        response = supabase.table(table_name).delete().eq("FOLIO", delete_folio).execute()
                        if len(response.data) > 0:
                            st.success(f"¡El registro {delete_folio} ha sido eliminado!")
                        else:
                            st.warning(f"No se encontró el FOLIO: {delete_folio}")
                    except Exception as e:
                        st.error("Error al eliminar los datos.")
                        st.error(f"Detalle técnico: {e}")

# ==========================================
# 3. Vista de los Datos Existentes (INTACTO)
# ==========================================
with col_view:
    st.subheader("📊 Vista de Datos (Tiempo Real)")

    try:
        response = supabase.table(table_name).select("*").order("FOLIO", desc=False).execute()
        datos_actuales = response.data

        if datos_actuales:
            st.dataframe(datos_actuales, use_container_width=True, height=1000)
            st.caption(f"Mostrando todos los registros de la tabla `{table_name}`.")
        else:
            st.info(f"La tabla `{table_name}` está conectada pero actualmente está vacía.")

    except Exception as e:
        st.error("Ocurrió un error al intentar leer los datos de Supabase.")
        st.error(f"Asegúrate de que la tabla '{table_name}' exista y las políticas RLS permitan lectura. Detalle: {e}")
