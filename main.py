import os
import streamlit as st
import llm
import ui_streamlit
import base64
import RAG_
import Multi_modal_process
import mysql_message
st.set_page_config(
    page_title="基于RAG与多模态的AI学习助手",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)
mysql_message.init_session_state()
user_images, user_files = ui_streamlit.sidebar()
ui_streamlit.ui_history_chat(st.session_state.ui_messages)
user_input = st.chat_input("请输入你的问题")
if user_input:
    session_id = st.session_state.session_id
    input = [{"type": "text", "text": user_input}]
    msg = {"role": "user", "content": user_input, "image_urls": [], "files": []}
    if user_images:
        for i in user_images:
            image_url = Multi_modal_process.image_process(i)
            input.append({"type": "image_url", "image_url": {"url": image_url}})
            msg["image_urls"].append(image_url)
    if user_files:
        RAG_.rag_file_process(user_files, session_id)
        a = Multi_modal_process.ui_file_process(user_files)
        msg["files"].extend(a)
    if os.path.exists(f"./chroma_db/{session_id}") and os.listdir(f"./chroma_db/{session_id}"):
        vectordb = RAG_.load_vector(session_id)
        if st.session_state.rag_switch and vectordb._collection.count() > 0:
            input[0]["text"] = RAG_.rag_prompt(user_input, vectordb)
    a = llm.llm_io(input, st.session_state.assistant_name, st.session_state.major, st.session_state.style, session_id)
    air = ui_streamlit.now_show(user_images, user_files, user_input, a, msg)
    st.session_state.ui_messages.append(msg)
    st.session_state.ui_messages.append({"role": "assistant", "content": air})
    mysql_message.save_ui(msg, air, session_id)
