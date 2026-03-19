import streamlit as st

# Alterar para a página
title = "Estudo de Tecnologias"
page_icon = ":material/camera:"

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

def item(title, text, lista, image):
    st.markdown(f"""

                <style>
                    .secondary_title {{
                        font-size: 35px !important;   
                        color: {default_secondary_text_color} !important;
                    }}
                    .justify {{
                        display: flex;
                        flex-direction: column;
                        text-align: justify;
                        padding-left: 30px;
                        padding-top: 10px;
                        width: fix-content;
                        gap: 5px;
                    }}
                    .text {{
                        margin-left: 30px !important;
                    }}
                </style>

                <div class="justify">
                    <h1 class="secondary_title">{title}</h1>
                    <p class="text">{text}</p>
                </div>

                """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        for item in lista:
            if item == "SEPARATOR":
                break
            st.markdown(f"""

                    <style>
                        .list {{
                            padding-left: 100px;
                        }}
                    </style>

                    <div class="s">
                        <ul class="list">
                            <li>{item}</li>
                        </ul>
                    </div>

                    """, unsafe_allow_html=True)
    
    break_point = False
    with col2:
        for item in lista:
            if item == "SEPARATOR":
                break_point = True
            while break_point == True and item != "SEPARATOR":
                st.markdown(f"""

                        <style>
                            .list {{
                                padding-left: 100px;
                            }}
                        </style>

                        <div class="s">
                            <ul class="list">
                                <li>{item}</li>
                            </ul>
                        </div>

                        """, unsafe_allow_html=True)
                if item == lista[-1]:
                    break_point = False
                break

    with col3:
        st.image(image=image, use_container_width='stretch')

    st.write("")
    
item("Wingfield", "A ferramenta atualmente utilizada pela PlayTennis® dispõe das seguintes métricas estatísticas:", 
     ["1º Saques Dentro",
      "2º Saques Dentro",
      "Pontos ganhos no 1º saque",
      "Pontos ganhos no 2º saque",
      "Aces por pontos de saque",
      "Duplas faltas por pontos de saque",
      "Melhoras estratégias de saque",
      "Velocidades: você x seu adversário",
      "Todos os golpes Dentro",
      "Saques Dentro",
      "SEPARATOR",
      "Devoluções Dentro",
      "Forehands Dentro",
      "Voleios Dentro",
      "Total de pontos ganhos",
      "Pontos ganhos no saque",
      "Pontos ganhos na devolução",
      "Pontos ganhos na rede",
      "Winnesrs",
      "Erros"
      ], "assets/img/WingField1.png")
item("Sofascore", "A ferramenta Sofascore® disponibiliza também as seguintes métricas estatísticas", 
     ["Interface do sofascore"], "assets/img/SofaScore1.png")

#["Aces",
#      "Dupla falta",
#      "Primeiro serviço",
#      "Segundo Saque",
#      "Pontos em primeiro serviço",
#      "Segundos pontos de serviço",
#      "Serviços Jogados",
#      "Break points salvos",
#      "Pontos total"
#      ]