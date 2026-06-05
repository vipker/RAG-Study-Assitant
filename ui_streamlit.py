import streamlit as st
import os
import mysql_message
import RAG_
def sidebar():
    with st.sidebar:
        st.title("RAG多模态学习助手")
        if st.button("新建会话", width="stretch", icon="🪶", key="cre"):
            if st.session_state.ui_messages:
                mysql_message.new_session()
                st.rerun()
        session_list = mysql_message.get_session_list()
        if session_list:
            for i in session_list:
                c1, c2 = st.columns([4, 1])
                with c1:
                    if st.button(i, width="stretch", key=f"show_{i}"):
                        mysql_message.swicth_session(i)
                        st.rerun()
                with c2:
                    if st.button("", width="stretch", icon="🗑️", key=f"del_{i}"):
                        mysql_message.delete_session(i)
                        st.rerun()
        assistant_name = st.text_input("助手类型", key="assistant_name")
        major = st.selectbox(
            "专业方向",
            ["Python编程", "大模型应用", "计算机基础", "数学", "英语四六级"],
            key="major"
        )
        style = st.radio(
            "回答风格",
            ["简洁专业", "幽默通俗", "详细回答", "分步引导"],
            key="style"
        )
        rag_switch = st.toggle("RAG检索", key="rag_switch")
        user_images = st.file_uploader("上传图片",
                                       type=["png", "jpg", "jpeg"],
                                       accept_multiple_files=True,
                                       key=f"user_image{len(st.session_state.ui_messages)}")
        user_files = st.file_uploader("上传文档（支持：pdf，md，txt,docx）",
                                      type=["pdf", "md", "txt", "docx"],
                                      accept_multiple_files=True,
                                      key=f"user_text{len(st.session_state.ui_messages)}")
        return user_images, user_files

def ui_history_chat(ui_messages):
    for i in ui_messages:
        if i["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(i["content"])
        elif i["role"] == "user":
            if i.get("image_urls"):
                cols = st.columns(len(i["image_urls"]))
                for id, imgae_url in enumerate(i["image_urls"]):
                    cols[id].image(imgae_url, caption=f"图片{id + 1}", width=100)
            if i.get("files"):
                cols = st.columns(len(i["files"]))
                for id, file in enumerate(i["files"]):
                    with cols[id]:
                        with st.popover(f"文档{file['filename']}"):
                            st.markdown(file["text"])
            with st.chat_message("user"):
                st.write(i["content"])

def now_show(user_images, user_files, user_input, a,msg):
    if user_images:
        cols = st.columns(len(user_images))
        for id, imgae_url in enumerate(user_images):
          cols[id].image(imgae_url, caption=f"图片{id + 1}", width=100)
    if user_files:
        col = st.columns(len(msg["files"]))
        for i, file in enumerate(msg["files"]):
            with col[i]:
                with st.popover(f"文档{file['filename']}"):
                    st.markdown(file["text"])
    with st.chat_message("user"):
        st.write(user_input)
    with st.chat_message("assistant"):
        liu = st.empty()
    air = ""
    for i in a:
        air += i.content
        liu.write(air)
    return  air

