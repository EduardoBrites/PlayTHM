from pathlib import Path
from collections import Counter

import pandas as pd
import streamlit as st

# =========================================================
# CONFIG
# =========================================================
title = "Estudo de Tecnologias"
page_icon = ":material/camera:"

PRIMARY = "rgb(15, 13, 66)"
SECONDARY = "#e67c3e"
ACCENT = "#293473"
BG_SOFT = "#F7F8FC"
CARD_BORDER = "rgba(0,0,0,0.06)"
TEXT_MUTED = "#6b7280"
GREEN = "#1f7a3e"

st.set_page_config(page_title=title, page_icon=page_icon, layout="wide")


# =========================================================
# CSS
# =========================================================
st.markdown(
    f"""
    <style>
        .main-title {{
            font-size: 58px !important;
            color: {PRIMARY} !important;
            font-weight: 800 !important;
            margin-bottom: 0.1rem;
        }}

        .subtitle {{
            font-size: 1.08rem;
            color: {TEXT_MUTED};
            margin-bottom: 1.2rem;
        }}

        .top-line {{
            width: 120px;
            height: 6px;
            background: linear-gradient(90deg, {SECONDARY}, {PRIMARY});
            border-radius: 999px;
            margin-bottom: 1rem;
        }}

        .hero-box {{
            background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
            border: 1px solid {CARD_BORDER};
            border-radius: 22px;
            padding: 24px 26px 20px 26px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
        }}

        .kpi-card {{
            border-radius: 18px;
            padding: 18px 18px 14px 18px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.07);
            border: 1px solid {CARD_BORDER};
            background: #ffffff;
            min-height: 128px;
        }}

        .kpi-title {{
            font-size: 0.95rem;
            color: #5f6368;
            margin-bottom: 10px;
        }}

        .kpi-value {{
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.05;
            color: {PRIMARY};
        }}

        .kpi-sub {{
            margin-top: 8px;
            color: {TEXT_MUTED};
            font-size: 0.82rem;
            line-height: 1.35;
        }}

        .insight-card {{
            border-radius: 18px;
            padding: 18px;
            border: 1px solid {CARD_BORDER};
            background: #ffffff;
            box-shadow: 0 4px 14px rgba(0,0,0,0.05);
            margin-bottom: 12px;
            min-height: 168px;
        }}

        .insight-title {{
            font-size: 1rem;
            font-weight: 800;
            margin-bottom: 10px;
            color: {PRIMARY};
        }}

        .insight-text {{
            color: {TEXT_MUTED};
            font-size: 0.92rem;
            line-height: 1.55;
        }}

        .study-card {{
            border-radius: 18px;
            padding: 20px;
            border: 1px solid {CARD_BORDER};
            background: #ffffff;
            box-shadow: 0 6px 18px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }}

        .study-title {{
            font-size: 1.15rem;
            font-weight: 800;
            color: {PRIMARY};
            margin-bottom: 6px;
        }}

        .study-meta {{
            font-size: 0.86rem;
            color: {TEXT_MUTED};
            margin-bottom: 12px;
        }}

        .study-text {{
            color: #2f3542;
            font-size: 0.95rem;
            line-height: 1.6;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            background: #eef5ff;
            color: #24406a;
            font-size: 0.8rem;
            margin: 4px 6px 0 0;
            border: 1px solid #d4e2ff;
        }}

        .section-title {{
            font-size: 1.6rem;
            font-weight: 800;
            color: {PRIMARY};
            margin-top: 0.5rem;
            margin-bottom: 0.4rem;
        }}

        .section-sub {{
            color: {TEXT_MUTED};
            margin-bottom: 1rem;
        }}

        .tech-card {{
            border-radius: 20px;
            padding: 20px;
            background: white;
            border: 1px solid {CARD_BORDER};
            box-shadow: 0 5px 16px rgba(0,0,0,0.05);
            min-height: 100%;
        }}

        .tech-title {{
            font-size: 1.18rem;
            font-weight: 800;
            color: {SECONDARY};
            margin-bottom: 8px;
        }}

        .tech-text {{
            color: {TEXT_MUTED};
            font-size: 0.92rem;
            line-height: 1.55;
            margin-bottom: 12px;
        }}

        .small-note {{
            color: {TEXT_MUTED};
            font-size: 0.84rem;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================
def find_refs_dir():
    candidates = [
        Path("refs"),
        Path("./refs"),
        Path("/mnt/data/refs"),
        Path("."),
        Path("/mnt/data"),
    ]
    for p in candidates:
        if p.exists():
            pdfs = list(p.glob("*.pdf"))
            if pdfs:
                return p
    return Path("refs")


def read_bytes(file_path: Path):
    with open(file_path, "rb") as f:
        return f.read()


def badge_row(items):
    if not items:
        return ""
    return " ".join([f"<span class='badge'>{x}</span>" for x in items])


def render_kpi(title, value, subtitle):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# METADADOS CURADOS DAS REFERÊNCIAS
# =========================================================
STUDY_METADATA = {
    "159523_danielcouri.pdf": {
        "titulo": "Análise Biomecânica de Tenistas: Fundamentos e Desenvolvimento de uma Plataforma de Baixo Custo",
        "ano": "2016",
        "tipo": "Tese / plataforma aplicada",
        "tema": "Biomecânica + Sensores + Plataforma",
        "resumo_curto": (
            "Apresenta uma plataforma de baixo custo para análise biomecânica do tênis, combinando "
            "modelo musculoesquelético em OpenSim, sensores na raquete e no membro superior, "
            "plataforma Arduino e interface em LabVIEW."
        ),
        "principais_achados": [
            "Mostra que câmera + sensores inerciais + sensores de força/ângulo ampliam a leitura biomecânica do gesto.",
            "Foca especialmente em ombro, cotovelo e punho, com ligação direta à prevenção de lesões.",
            "Sugere que dados biomecânicos podem apoiar treino técnico, monitoramento e discussão de risco."
        ],
        "aplicacao_playtennis": [
            "Construção de produto de biomecânica visual de baixo custo",
            "Métricas para saque, forehand, backhand e risco de sobrecarga",
            "Base conceitual para scouting + biomecânica visual"
        ],
        "tags": ["OpenSim", "Arduino", "EMG", "raquete instrumentada", "baixo custo"],
    },
    "dines2015.pdf": {
        "titulo": "Tennis Injuries: Epidemiology, Pathophysiology, and Treatment",
        "ano": "2015",
        "tipo": "Review clínica",
        "tema": "Lesões no tênis",
        "resumo_curto": (
            "Revisão das lesões mais frequentes no tênis, seus mecanismos e opções de manejo. "
            "Relaciona regiões anatômicas e gestos técnicos que aumentam carga e risco."
        ),
        "principais_achados": [
            "Associa lesões de ombro a movimentos repetidos acima da cabeça.",
            "Relaciona epicondilalgia lateral a backhand com punho flexionado.",
            "Mostra que o saque e o gesto técnico influenciam também abdômen e lombar."
        ],
        "aplicacao_playtennis": [
            "Explicar risco biomecânico por golpe",
            "Educação do aluno / treinador com base clínica",
            "Criação de alertas e conteúdo preventivo"
        ],
        "tags": ["ombro", "cotovelo", "punho", "saque", "sobrecarga"],
    },
    "common_injuries_in_tennis_players__exercises_to.6.pdf": {
        "titulo": "Common Injuries in Tennis Players: Exercises to Address Muscular Imbalances and Reduce Injury Risk",
        "ano": "2009",
        "tipo": "Review aplicada / prevenção",
        "tema": "Prevenção + condicionamento",
        "resumo_curto": (
            "Discute padrões de lesão no tênis e propõe exercícios para reduzir desequilíbrios musculares, "
            "com ênfase em ombro, cotovelo, tronco e cadeia cinética."
        ),
        "principais_achados": [
            "A potência do golpe não deve ser atribuída só a punho/antebraço, mas à cadeia cinética como um todo.",
            "Aponta alta frequência de lesões em ombro e cotovelo em tenistas.",
            "Defende exercícios específicos de manguito, escápula, antebraço e core para prevenção."
        ],
        "aplicacao_playtennis": [
            "Conteúdo educativo com exercícios preventivos",
            "Relatórios com foco em desequilíbrios",
            "Conectar desempenho técnico com preparação física"
        ],
        "tags": ["cadeia cinética", "manguito", "cotovelo", "core", "prevenção"],
    },
    "kaiser-et-al-2021-acute-tennis-injuries-in-the-recreational-tennis-player.pdf": {
        "titulo": "Acute Tennis Injuries in the Recreational Tennis Player",
        "ano": "2021",
        "tipo": "Estudo observacional",
        "tema": "Epidemiologia de lesões agudas",
        "resumo_curto": (
            "Analisa lesões agudas em tenistas recreacionais e mostra que o padrão do recreativo é diferente "
            "do atleta de elite, com forte presença de membros inferiores, torções e quedas."
        ),
        "principais_achados": [
            "Lesões agudas ocorreram majoritariamente em membros inferiores.",
            "Torções e quedas apareceram como mecanismos centrais.",
            "Entorses de tornozelo, fraturas e algumas lesões que exigem cirurgia merecem atenção em prevenção."
        ],
        "aplicacao_playtennis": [
            "Programas de aquecimento e prevenção para recreacionais",
            "Conteúdo voltado a segurança de quadra e deslocamento",
            "Produtos segmentados por perfil recreativo"
        ],
        "tags": ["recreacional", "tornozelo", "quedas", "torções", "agudo"],
    },
    "pas2020.pdf": {
        "titulo": "Effectiveness of an e-health Tennis-Specific Injury Prevention Programme",
        "ano": "2020",
        "tipo": "RCT",
        "tema": "Prevenção digital",
        "resumo_curto": (
            "Teste randomizado de um programa digital de prevenção de lesões no tênis. "
            "O formato não supervisionado não reduziu a prevalência de lesões."
        ),
        "principais_achados": [
            "Programa e-health não supervisionado não reduziu lesões de forma relevante.",
            "Adesão e controle de qualidade da execução parecem críticos.",
            "Sugere que prevenção digital sozinha pode não ser suficiente sem supervisão."
        ],
        "aplicacao_playtennis": [
            "Produto digital precisa de engajamento e validação prática",
            "Treinador e feedback visual podem ser diferenciais",
            "Evitar solução puramente passiva sem acompanhamento"
        ],
        "tags": ["e-health", "prevenção", "adesão", "RCT", "produto digital"],
    },
    "journal.pone.0290320.pdf": {
        "titulo": "Biomechanical Analyses of Different Serve and Groundstroke Techniques in Tennis: A Systematic Scoping Review",
        "ano": "2023",
        "tipo": "Scoping review",
        "tema": "Biomecânica de golpes",
        "resumo_curto": (
            "Revisão sobre diferenças biomecânicas entre tipos de saque e groundstrokes, "
            "incluindo tipo de golpe, direção e stance."
        ),
        "principais_achados": [
            "Tipo de saque, direção e stance alteram variáveis cinemáticas, cinéticas e EMG.",
            "Há espaço para estudos mais integrados e comparações mais completas.",
            "A literatura suporta o uso de análise técnica específica por golpe."
        ],
        "aplicacao_playtennis": [
            "Comparar flat, slice, topspin, open stance etc.",
            "Estruturar dashboards por gesto técnico",
            "Apoiar feedback técnico mais segmentado"
        ],
        "tags": ["saque", "groundstroke", "stance", "cinemática", "EMG"],
    },
    "jfmk-09-00034-v2.pdf": {
        "titulo": "Core Stability, Insoles and Postural Stability in Competitive Adolescent Tennis Players",
        "ano": "2024",
        "tipo": "Intervenção",
        "tema": "Core + postura + prevenção",
        "resumo_curto": (
            "Estudo com jovens competitivos mostrando melhora de estabilidade postural após protocolo "
            "de treino de core combinado com palmilhas proprioceptivas."
        ),
        "principais_achados": [
            "Treino de core melhorou indicadores de estabilidade postural.",
            "Os ganhos foram mantidos após curto período sem treino.",
            "Sugere impacto potencial na prevenção de lesões e no controle corporal."
        ],
        "aplicacao_playtennis": [
            "Conteúdo de preparação física complementar",
            "Integração entre técnica, postura e estabilidade",
            "Base para trilhas preventivas por perfil"
        ],
        "tags": ["core", "estabilidade", "postura", "adolescentes", "prevenção"],
    },
    "jcm-13-01456-v2.pdf": {
        "titulo": "Movement Quality and Body Posture as Injury-Related Factors",
        "ano": "2024",
        "tipo": "Estudo observacional",
        "tema": "Qualidade de movimento + postura",
        "resumo_curto": (
            "Mostra que a combinação entre boa qualidade de movimento e boa postura corporal "
            "se associa a menor frequência de lesões."
        ),
        "principais_achados": [
            "Abordagem multifatorial parece mais útil do que um único indicador isolado.",
            "Boa postura e boa qualidade de movimento reduzem frequência de lesões.",
            "Reforça a ideia de rastrear assimetrias, padrão de movimento e postura."
        ],
        "aplicacao_playtennis": [
            "Screening funcional simples antes da análise técnica",
            "Combinar biomecânica visual com avaliação postural",
            "Criar score composto de risco / qualidade"
        ],
        "tags": ["postura", "movimento", "screening", "risco", "multifatorial"],
    },
}


# =========================================================
# CARGA DOS ARQUIVOS
# =========================================================
refs_dir = find_refs_dir()
pdf_files = sorted(refs_dir.glob("*.pdf"), key=lambda x: x.name.lower())

if not pdf_files:
    st.warning("Nenhum PDF foi encontrado na pasta de referências.")
    st.stop()

studies = []
for pdf in pdf_files:
    key = pdf.name.lower()
    meta = STUDY_METADATA.get(key, {})
    studies.append(
        {
            "file_name": pdf.name,
            "path": pdf,
            "titulo": meta.get("titulo", pdf.stem.replace("_", " ").replace("-", " ").title()),
            "ano": meta.get("ano", "—"),
            "tipo": meta.get("tipo", "Referência"),
            "tema": meta.get("tema", "Literatura"),
            "resumo_curto": meta.get(
                "resumo_curto",
                "Referência adicionada à biblioteca. Se desejar, podemos complementar este resumo com uma leitura mais detalhada."
            ),
            "principais_achados": meta.get("principais_achados", []),
            "aplicacao_playtennis": meta.get("aplicacao_playtennis", []),
            "tags": meta.get("tags", []),
        }
    )

df_studies = pd.DataFrame(studies)

# =========================================================
# RESUMO GERAL DA LITERATURA
# =========================================================
temas_count = Counter(df_studies["tema"].tolist())

literature_highlights = [
    {
        "title": "O que a literatura sugere sobre lesões",
        "text": (
            "Os estudos convergem em dois blocos: lesões por sobrecarga no membro superior "
            "e lesões agudas ligadas a deslocamento, torção e quedas em recreacionais."
        ),
    },
    {
        "title": "O que a literatura sugere sobre técnica",
        "text": (
            "Tipo de saque, direção do golpe, stance e cadeia cinética alteram a biomecânica. "
            "Não faz sentido analisar “o tênis” como um bloco único."
        ),
    },
    {
        "title": "O que a literatura sugere sobre prevenção",
        "text": (
            "Programas de prevenção funcionam melhor quando há supervisão, preparação física específica "
            "e leitura integrada de postura, movimento e carga."
        ),
    },
    {
        "title": "Oportunidade para a PlayTennis",
        "text": (
            "Há espaço claro para um produto que una biomecânica visual, interpretação técnica "
            "e conteúdo preventivo aplicável ao aluno e ao treinador."
        ),
    },
]

# =========================================================
# HERO
# =========================================================
st.markdown(
    f"""
    <div class="hero-box">
        <div class="top-line"></div>
        <div class="main-title">{title}</div>
        <div class="subtitle">
            Biblioteca estratégica de referências, benchmarks e evidências para apoiar a discussão
            de produto, biomecânica visual, prevenção de lesões e posicionamento técnico da PlayTennis.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# KPIs
# =========================================================
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi("Estudos na biblioteca", str(len(df_studies)), "Arquivos PDF disponíveis para leitura e comparação")
with c2:
    render_kpi("Temas principais", str(len(temas_count)), "Biomecânica, lesões, prevenção, postura e tecnologia")
with c3:
    render_kpi("Foco mais frequente", max(temas_count, key=temas_count.get), "Tema com maior recorrência entre as referências")
with c4:
    render_kpi("Uso prático", "Produto + conteúdo", "Aplicações diretas para tecnologia, treino e prevenção")

st.write("")

# =========================================================
# INSIGHTS GERAIS
# =========================================================
st.markdown('<div class="section-title">Resumo executivo da literatura</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Síntese inicial do que aparece de forma mais consistente nas referências selecionadas.</div>',
    unsafe_allow_html=True,
)

ins1, ins2 = st.columns(2)
with ins1:
    for card in literature_highlights[:2]:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">{card['title']}</div>
                <div class="insight-text">{card['text']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
with ins2:
    for card in literature_highlights[2:]:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">{card['title']}</div>
                <div class="insight-text">{card['text']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# =========================================================
# FILTROS
# =========================================================
f1, f2 = st.columns([1, 2])

with f1:
    tema_escolhido = st.selectbox(
        "Filtrar por tema",
        options=["Todos"] + sorted(df_studies["tema"].dropna().unique().tolist()),
        index=0,
    )

with f2:
    estudos_filtrados = df_studies.copy()
    if tema_escolhido != "Todos":
        estudos_filtrados = estudos_filtrados[estudos_filtrados["tema"] == tema_escolhido].copy()

    estudo_escolhido = st.selectbox(
        "Selecionar estudo / referência",
        options=estudos_filtrados["file_name"].tolist(),
        index=0,
    )

selected = estudos_filtrados[estudos_filtrados["file_name"] == estudo_escolhido].iloc[0]
selected_path = Path(selected["path"])

# =========================================================
# ESTUDO SELECIONADO
# =========================================================
st.markdown('<div class="section-title">Estudo selecionado</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Resumo prático, implicações para a PlayTennis e opção de baixar o PDF da referência.</div>',
    unsafe_allow_html=True,
)

st.download_button(
        label="⬇️ Baixar PDF da referência",
        data=read_bytes(selected_path),
        file_name=selected_path.name,
        mime="application/pdf",
        use_container_width=True,
        )

st.divider()

# =========================================================
# BIBLIOTECA RESUMIDA
# =========================================================
st.markdown('<div class="section-title">Biblioteca resumida</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Visão geral das referências para navegação rápida.</div>',
    unsafe_allow_html=True,
)

for _, row in estudos_filtrados.iterrows():
    st.markdown(
        f"""
        <div class="study-card">
            <div class="study-title">{row['titulo']}</div>
            <div class="study-meta">{row['tipo']} • {row['ano']} • {row['tema']}</div>
            <div class="study-text">{row['resumo_curto']}</div>
            <div style="margin-top:10px;">{badge_row(row['tags'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# =========================================================
# BENCHMARKS DE MERCADO / TECNOLOGIAS
# =========================================================
st.markdown('<div class="section-title">Benchmarks e tecnologias de mercado</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Organização visual mais limpa do material que você já vinha mostrando para Daniel.</div>',
    unsafe_allow_html=True,
)

wingfield_metrics = [
    "1º saques dentro",
    "2º saques dentro",
    "Pontos ganhos no 1º saque",
    "Pontos ganhos no 2º saque",
    "Aces por pontos de saque",
    "Duplas faltas por pontos de saque",
    "Melhores estratégias de saque",
    "Velocidades: você x adversário",
    "Todos os golpes dentro",
    "Saques dentro",
    "Devoluções dentro",
    "Forehands dentro",
    "Voleios dentro",
    "Total de pontos ganhos",
    "Pontos ganhos no saque",
    "Pontos ganhos na devolução",
    "Pontos ganhos na rede",
    "Winners",
    "Erros",
]

sofasc_metrics = [
    "Aces",
    "Dupla falta",
    "Primeiro serviço",
    "Segundo saque",
    "Pontos em primeiro serviço",
    "Pontos em segundo serviço",
    "Break points salvos",
    "Pontos totais",
    "Interface de acompanhamento estatístico",
]

img_wingfield = Path("assets/img/WingField1.png")
img_sofa = Path("assets/img/SofaScore1.png")

tc1, tc2 = st.columns(2)

with tc1:
    st.markdown(
        """
        <div class="tech-card">
            <div class="tech-title">Wingfield</div>
            <div class="tech-text">
                Benchmark com foco em estatísticas de jogo, saque, precisão, velocidade e leitura
                dos principais eventos da partida.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if img_wingfield.exists():
        st.image(str(img_wingfield), use_container_width=True)
    st.markdown("**Métricas observadas**")
    for item in wingfield_metrics:
        st.markdown(f"- {item}")

with tc2:
    st.markdown(
        """
        <div class="tech-card">
            <div class="tech-title">Sofascore</div>
            <div class="tech-text">
                Referência de interface esportiva e comunicação simples de estatísticas, útil como
                inspiração de UX e consumo rápido de dados.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if img_sofa.exists():
        st.image(str(img_sofa), use_container_width=True)
    st.markdown("**Elementos observados**")
    for item in sofasc_metrics:
        st.markdown(f"- {item}")

st.write("")
st.markdown(
    """
    <div class="small-note">
        Observação: a página lê automaticamente os PDFs disponíveis na pasta <b>refs</b>.
        As referências com resumo curado aparecem com texto executivo; as demais entram com fallback automático.
    </div>
    """,
    unsafe_allow_html=True,
)