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
    # PESTAÑA: ACTUALIZAR (OPTIMIZADO CON DATA EDITOR)
    # ----------------------------------------
    with tab_update:
        st.subheader("Modificar Registro")

        # Mensaje de éxito persistido tras recarga limpia
        if "update_success_msg" in st.session_state:
            st.success(st.session_state.pop("update_success_msg"))

        # Consulta en tiempo real de los datos existentes para el editor
        try:
            res_update = supabase.table(table_name).select("*").order("FOLIO", desc=False).execute()
            data_to_edit = res_update.data
        except Exception as e:
            data_to_edit = []
            st.error(f"Error al cargar registros para modificar: {e}")

        if not data_to_edit:
            st.info(f"La tabla `{table_name}` no tiene registros para modificar.")
        else:
            st.caption("Selecciona cualquier celda para modificarla o borrar su texto. Al terminar, presiona guardar.")

            # Clave dinámica para reiniciar el buffer de edición tras cada guardado
            editor_version = st.session_state.get("editor_version", 0)
            editor_key = f"update_editor_{editor_version}"

            with st.form("update_form"):
                st.data_editor(
                    data_to_edit,
                    key=editor_key,
                    disabled=["FOLIO"], # El FOLIO se protege como llave única
                    use_container_width=True,
                    height=450
                )

                st.markdown("<br>", unsafe_allow_html=True)
                btn_update = st.form_submit_button("Actualizar en Supabase", type="primary", use_container_width=True)

                if btn_update:
                    editor_state = st.session_state.get(editor_key, {})
                    edited_rows = editor_state.get("edited_rows", {}) if isinstance(editor_state, dict) else getattr(editor_state, "edited_rows", {})

                    if not edited_rows:
                        st.warning("No realizaste ningún cambio en las celdas.")
                    else:
                        actualizados = 0
                        errores = []

                        for r_idx, cambios in edited_rows.items():
                            idx = int(r_idx)
                            if 0 <= idx < len(data_to_edit):
                                folio_reg = data_to_edit[idx].get("FOLIO")
                                if folio_reg is not None:
                                    update_payload = dict(cambios)
                                    update_payload.pop("FOLIO", None)

                                    # Asegurar compatibilidad de tipos en DIAS si fue editado o vaciado
                                    if "DIAS" in update_payload:
                                        val_dias = update_payload["DIAS"]
                                        if val_dias == "" or val_dias is None:
                                            update_payload["DIAS"] = None
                                        else:
                                            try:
                                                update_payload["DIAS"] = int(val_dias)
                                            except (ValueError, TypeError):
                                                update_payload["DIAS"] = None

                                    if update_payload:
                                        try:
                                            supabase.table(table_name).update(update_payload).eq("FOLIO", folio_reg).execute()
                                            actualizados += 1
                                        except Exception as e:
                                            errores.append(f"FOLIO {folio_reg}: {e}")

                        if actualizados > 0 and not errores:
                            st.session_state["update_success_msg"] = f"¡Se actualizaron {actualizados} registro(s) correctamente en Supabase!"
                            st.session_state["editor_version"] = editor_version + 1
                            if hasattr(st, "rerun"):
                                st.rerun()
                            else:
                                st.experimental_rerun()
                        elif actualizados > 0 and errores:
                            st.session_state["editor_version"] = editor_version + 1
                            st.warning(f"Se actualizaron {actualizados} registro(s), pero fallaron los siguientes:")
                            for err in errores:
                                st.error(err)
                            if hasattr(st, "rerun"):
                                st.rerun()
                            else:
                                st.experimental_rerun()
                        else:
                            for err in errores:
                                st.error(f"Error al actualizar: {err}")

    # ----------------------------------------
    # PESTAÑA: ELIMINAR (INTACTO)
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
