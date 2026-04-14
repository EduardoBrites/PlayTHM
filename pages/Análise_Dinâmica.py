import streamlit as st

# Alterar para a página
title = "Análise Dinâmica"
page_icon = ":material/mystery:"

default_text_color = "rgb(15, 13, 66)"
default_secondary_text_color = "#e67c3e"

st.set_page_config(page_title=title, page_icon=page_icon)

st.markdown(f"""
            
            <style>
                .main_title {{
                    font-size: 65px !important;   
                    color: {default_text_color} !important;
                }}
                .center {{
                    display: flex;
                    justify-content: center;
                    padding-left: 15px;
                    width: fit-content;
                    border-bottom: 5px solid {default_text_color};
                }}
            </style>
           
            <div class="center">
                <h1 class="main_title">{title}</h1>
            </div>
            
            """, unsafe_allow_html=True)

st.write("")

col1, col2 = st.columns(2)

with col1:
    st.image(image="./assets/img/3D_capture.jpeg")
    st.video(data="./assets/video/3d_capture_vid.mp4", loop=True, muted=True, autoplay=True)
    
with col2:
    st.image(image="./assets/img/3D_capture_2.jpeg")
    st.video(data="./assets/video/ball.mp4", loop=True, muted=True, autoplay=True)