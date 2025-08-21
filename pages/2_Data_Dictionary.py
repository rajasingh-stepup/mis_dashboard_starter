import streamlit as st
import json

st.set_page_config(page_title="Data Dictionary", page_icon="📚", layout="wide")
st.title("📚 Data Dictionary")

DEFAULT_MAPPING = st.session_state.get("mapping", {})
mapping_text = json.dumps(DEFAULT_MAPPING, indent=2)
txt = st.text_area("Edit your standard → candidate column mapping (JSON)", value=mapping_text, height=400)
if st.button("Save mapping"):
    try:
        obj = json.loads(txt)
        st.session_state["mapping"] = obj
        st.success("Saved in session. Persist by downloading below.")
    except Exception as e:
        st.error(f"Invalid JSON: {e}")

st.download_button("⬇️ Download mapping.json", data=json.dumps(st.session_state.get("mapping", {}), indent=2), file_name="mapping.json")