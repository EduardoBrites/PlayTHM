import streamlit as st

# Alterar para a página
title = "Scout com Visão Computacional"
page_icon = ":material/eye_tracking:"

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

input_video = open("assets/video/input_video.mp4", "rb")
input_bytes = input_video.read()

output_video = open("assets/video/output.mp4", "rb")
output_bytes = output_video.read()

treinamento_url = "https://www.youtube.com/watch?v=L23oIHZE14w"

mapa_de_calor_url = "https://www.youtube.com/watch?v=K3CMPLp68fM"

tab1, tab2, tab3, tab4 = st.tabs(["Input", "Output", "Treinamento de Modelo", "Mapa de Calor"])

with tab1:
    st.video(input_bytes, autoplay=True, loop=True, muted=True)
    
with tab2:
    st.video(output_bytes, autoplay=True, loop=True, muted=True)
    
with tab3:
    st.video(treinamento_url, autoplay=True, muted=True)

with tab4:
    st.video(mapa_de_calor_url, autoplay=True, muted=True)