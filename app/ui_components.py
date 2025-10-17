import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import HeatMap
from . import config
from . import analysis
from app import data_loader

from pyecharts import options as opts
from pyecharts.charts import Liquid
from pyecharts.commons.utils import JsCode


def render_mavis_header(theme='light'):
    """Renderiza o cabeçalho interativo 'MAVIS' com CSS e JS embutidos para garantir a renderização correta."""
    
    # Define a cor do gradiente com base no tema selecionado
    if theme == 'dark':
        gradient_color = "linear-gradient(90deg, #FFFFFF, #B0B0B0)" # Branco para modo escuro
    else:
        gradient_color = "linear-gradient(90deg, #1a1a1a, #707070)" # Escuro para modo claro

    # O código HTML, CSS e JS original e funcional foi colocado diretamente aqui.
    mavis_html = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&family=Outfit:wght@100..900&family=Sansation:ital,wght@0,300;0,400;0,700;1,300;1,400;1,700&display=swap');
    
    .header-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 120px;
        border-radius: 12px;
        margin: 20px;
    }
    
    .mavis-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 3rem;
        font-weight: 300;
        background: {gradient_color};
        -webkit-background-clip: text;
        display: flex;
        gap: 5px;
        cursor: pointer;
    }
    
    /* animação de entrada para cada letra */
    .mavis-char, .mavis-hidden-text {
        opacity: 0;
        transform: translateY(20px);
        animation: fadeUp 0.8s forwards;
    }

    /* delays para letras grandes */
    .mavis-char:nth-child(1) { animation-delay: 0.1s; }
    .mavis-char:nth-child(3) { animation-delay: 0.3s; }
    .mavis-char:nth-child(5) { animation-delay: 0.5s; }
    .mavis-char:nth-child(7) { animation-delay: 0.7s; }
    .mavis-char:nth-child(9) { animation-delay: 0.9s; }

    /* delays para palavras escondidas (um pouco depois das letras) */
    .mavis-hidden-text:nth-child(2) { animation-delay: 0.2s; }
    .mavis-hidden-text:nth-child(4) { animation-delay: 0.4s; }
    .mavis-hidden-text:nth-child(6) { animation-delay: 0.6s; }
    .mavis-hidden-text:nth-child(8) { animation-delay: 0.8s; }
    .mavis-hidden-text:nth-child(10){ animation-delay: 1s; }

    @keyframes fadeUp {
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* hover glow futurista para letras e palavras */
    .mavis-char:hover, .mavis-hidden-text:hover {
        text-shadow: 5px 10px 12px rgba(110, 109, 109, 0.8);
        transform: scale(1.1);
        transition: all 0.4s ease-in-out;
    }
    
    /* significado escondido */
    .mavis-hidden-text {
        opacity: 0;
        max-width: 0;
        overflow: hidden;
        white-space: nowrap;
        font-size: 0.9rem;
        font-weight: 300;
        background: linear-gradient(90deg, #404959, #707070);
        -webkit-background-clip: text;
        color: transparent; /* cor mais escura para versão clara */
        align-self: center;
        transition: all 0.5s ease-in-out;
    }
    
    /* expandido = aparece */
    .mavis-hidden-text.expanded {
        opacity: 1;
        max-width: 200px;
        padding: 0 2px;
        align-self: center;
    }
    </style>
    
    <div class="header-container" onclick="toggleMavis()">
        <div class="mavis-title">
            <span class="mavis-char">M</span><span class="mavis-hidden-text">onitoramento,</span>
            <span class="mavis-char">A</span><span class="mavis-hidden-text">nálise e</span>
            <span class="mavis-char">V</span><span class="mavis-hidden-text">isualização de</span>
            <span class="mavis-char">I</span><span class="mavis-hidden-text">ndicadores de</span>
            <span class="mavis-char">S</span><span class="mavis-hidden-text">olda</span>
        </div>
    </div>
    
    <script>
    function toggleMavis() {
        const hiddenTexts = document.querySelectorAll('.mavis-hidden-text');
        hiddenTexts.forEach(text => {
            text.classList.toggle('expanded');
        });
    }
    </script>
    """
    components.html(mavis_html, height=160)

# O restante do arquivo (gerar_gauge_individual_html, render_sensor_layout, etc.) permanece o mesmo.
def gerar_gauge_individual_html(score, titulo):
    """Gera o código HTML para um gráfico de gauge individual."""
    if score <= 25: cor_progresso = "#a61d24"
    elif score <= 50: cor_progresso = "#ff4d4f"
    elif score <= 75: cor_progresso = "#faad14"
    else: cor_progresso = "#52c41a"
    chart_id = f"gauge_individual_{titulo.replace(' ', '_')}"

    return f"""
    <!DOCTYPE html><html><head><meta charset="utf-8" /><script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script></head><body><div id="{chart_id}" style="width:175px;height:160px;"></div><script type="text/javascript">var myChart=echarts.init(document.getElementById('{chart_id}'));var option={{series:[{{type:'gauge',startAngle:180,endAngle:0,min:0,max:100,radius:'100%',itemStyle:{{color:'{cor_progresso}'}},progress:{{show:!0,roundCap:!0,width:12}},pointer:{{show:!1}},axisLine:{{roundCap:!0,lineStyle:{{width:12,color:[[0.25,'#a61d24'],[0.50,'#ff4d4f'],[0.75,'#faad14'],[1,'#52c41a']]}}}},axisTick:{{show:!1}},splitLine:{{show:!1}},axisLabel:{{show:!1}},title:{{show:!0,offsetCenter:[0,'20%'],fontSize:13,color:'#555'}},detail:{{offsetCenter:[0,'-15%'],valueAnimation:!0,formatter:function(e){{return e.toFixed(0)+'%'}},fontSize:24,fontWeight:'bolder',color:'#333'}},data:[{{value:{score},name:'{titulo}'}}]}}]}};myChart.setOption(option);window.addEventListener('resize',myChart.resize);</script></body></html>
    """

def gerar_gauge_foco_html(score, titulo):
    """Gera o código HTML para um gráfico de gauge de destaque."""
    if score <= 25: cor_progresso = "#a61d24"
    elif score <= 50: cor_progresso = "#ff4d4f"
    elif score <= 75: cor_progresso = "#faad14"
    else: cor_progresso = "#52c41a"
    chart_id = f"gauge_foco_{titulo.replace(' ', '_')}"

    return f"""
    <!DOCTYPE html><html><head><meta charset="utf-8" /><script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script></head><body><div id="{chart_id}" style="width:250px;height:200px;"></div><script type="text/javascript">var myChart=echarts.init(document.getElementById('{chart_id}'));var option={{series:[{{type:'gauge',startAngle:180,endAngle:0,min:0,max:100,radius:'100%',itemStyle:{{color:'{cor_progresso}'}},progress:{{show:!0,roundCap:!0,width:15}},pointer:{{show:!1}},axisLine:{{roundCap:!0,lineStyle:{{width:15,color:[[0.25,'#a61d24'],[0.50,'#ff4d4f'],[0.75,'#faad14'],[1,'#52c41a']]}}}},axisTick:{{show:!1}},splitLine:{{show:!1}},axisLabel:{{show:!1}},title:{{show:!0,offsetCenter:[0,'25%'],fontSize:18,color:'#555',fontWeight:'bold'}},detail:{{offsetCenter:[0,'-10%'],valueAnimation:!0,formatter:function(e){{return e.toFixed(0)+'%'}},fontSize:45,fontWeight:'bolder',color:'#333'}},data:[{{value:{score},name:'{titulo}'}}]}}]}};myChart.setOption(option);window.addEventListener('resize',myChart.resize);</script></body></html>
    """

def render_sensor_layout(df, sensor, risco, data_col_name):
    """Renderiza a UI para um único sensor (título, status, gráfico e expander de análise)."""
    st.write(f"## {config.NOMES_SENSORES.get(sensor, sensor)}")
    st.markdown(analysis.detectar_anomalia(df, sensor))
    st.line_chart(df.set_index(data_col_name)[sensor])
    
    with st.expander("Ver análise detalhada da IA"):
        st.caption(analysis.analisar_tendencia(df, df[sensor], sensor))
        st.markdown("---")
        
        st.write("**Potencial de falha iminente (%)**")
        if risco is not None:
            if risco > 75: st.error(f"**Risco Elevado:** {risco:.1f}%")
            elif risco > 50: st.warning(f"**Atenção:** {risco:.1f}%")
            elif risco > 20: st.info(f"**Risco Moderado:** {risco:.1f}%")
            else: st.success(f"**Risco Baixo:** {risco:.1f}%")
        else:
            st.info("Simulação de risco indisponível.")
            
        status_sensor = analysis.detectar_anomalia(df, sensor)
        if "Normal" not in status_sensor:
            st.markdown("---")
            st.write("**Análise de Causa Raiz:**")
            rca_sensor = analysis.analisar_causa_raiz(sensor)
            causas = '\n'.join(rca_sensor['causas_provaveis'])
            acoes = '\n'.join(rca_sensor['acoes_recomendadas'])
            st.caption(f"**Causas Prováveis:**\n{causas}")
            st.caption(f"**Ações Recomendadas:**\n{acoes}")
        else:
            st.info("Tudo normal por aqui...")

def render_heatmap_temperatura(df_semanal_filtrado):
    """Renderiza o mapa de calor para o sensor de temperatura."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("Mapa de Calor da Temperatura (Semanal x Mensal)")
       
    heatmap_data = []
    semanas = sorted(df_semanal_filtrado['SEMANA_NUM'].dropna().unique().tolist())
    meses = df_semanal_filtrado['SEMANA'].dt.to_period("M").astype(str).unique().tolist()

    for i, semana in enumerate(semanas):
        for j, mes in enumerate(meses):
            media_temp = df_semanal_filtrado[
                (df_semanal_filtrado['SEMANA_NUM'] == semana) &
                (df_semanal_filtrado['SEMANA'].dt.to_period("M").astype(str) == mes)
            ]['TEMPERATURA'].mean()
            if pd.notna(media_temp):
                heatmap_data.append([j, i, round(media_temp)])

    if heatmap_data:
        valores = [p[2] for p in heatmap_data]
        valor_min = min(valores)
        valor_max = max(valores)
    
        heatmap = (
            HeatMap()
            .add_xaxis(meses)
            .add_yaxis("Semanas", semanas, heatmap_data)
            .set_global_opts(
                title_opts=opts.TitleOpts(title="Temperatura Média (ºC)"),
                visualmap_opts=opts.VisualMapOpts(
                    min_=valor_min,
                    max_=valor_max,
                    orient="vertical",
                    pos_top="center",
                    pos_left="left"
                ),
                xaxis_opts=opts.AxisOpts(type_="category", name="Mês"),
                yaxis_opts=opts.AxisOpts(type_="category", name="Semana")
            )
        )
        heatmap.height = "440px"
        heatmap.width = "100%"
        components.html(heatmap.render_embed(), height=480, width=1400, scrolling=True)
    else:
        st.warning("Não há dados suficientes para gerar o mapa de calor.")
        
def hide_main_page_nav_and_footer():
    """
    Usa CSS para esconder o link da página principal (main.py) na barra de navegação
    e o rodapé 'Made with Streamlit'. Esta função deve ser usada em TODAS as páginas
    INTERNAS do dashboard.
    """
    hide_style = """
        <style>
        [data-testid="stSidebarNav"] ul > li:first-child { display: none; }
        footer { visibility: hidden; }
        </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)

def hide_sidebar_nav():
    """
    Usa CSS para esconder TODA a navegação da barra lateral.
    Esta função deve ser usada EXCLUSIVAMENTE na página de login (main.py).
    """
    hide_nav_style = """
        <style>
            [data-testid="stSidebarNav"] {display: none;}
        </style>
    """
    st.markdown(hide_nav_style, unsafe_allow_html=True)

def render_filter_form(df_total_completo):
    """Renderiza um formulário completo na sidebar para filtrar os dados."""
    with st.sidebar.form("filter_form"):
        st.markdown(":blue[**Filtros de Análise**]")

        # --- Filtro de Receita ---
        receitas_disponiveis = data_loader.obter_top_4_receitas_formatadas()
        # Lógica para encontrar o valor padrão '123' ou o valor já salvo
        default_receita_fmt = st.session_state.filtros_aplicados['receita_fmt']
        if default_receita_fmt not in receitas_disponiveis:
             default_receita_fmt = next((r for r in receitas_disponiveis if r.startswith("123 ")), receitas_disponiveis[0])

        receita_selecionada_fmt = st.selectbox(
            "Selecione a Receita:",
            receitas_disponiveis,
            index=receitas_disponiveis.index(default_receita_fmt)
        )

        receita_num = 'Todas' if receita_selecionada_fmt == 'Todas' else receita_selecionada_fmt.split(' ')[0]
        df_filtrado_receita = df_total_completo[df_total_completo['PROGRAM_Nº'] == receita_num] if receita_num != 'Todas' else df_total_completo

        # --- Filtros de Código ---
        codigos_entry = sorted(df_filtrado_receita['code ENTRY'].dropna().astype(str).unique().tolist())
        codigos_exit = sorted(df_filtrado_receita['code EXIT'].dropna().astype(str).unique().tolist())
        
        entry_code_selecionado = st.selectbox("Código de Entrada:", ['Todos'] + codigos_entry, index=0)
        exit_code_selecionado = st.selectbox("Código de Saída:", ['Todos'] + codigos_exit, index=0)
        
        st.markdown("---")

        # --- Filtros de Período ---
        anos_disponiveis = sorted(df_total_completo['DATA'].dt.year.unique())
        anos_selecionados = st.multiselect(
            "Ano(s):", 
            anos_disponiveis, 
            default=st.session_state.filtros_aplicados['anos']
        )
        
        df_filtrado_ano = df_total_completo[df_total_completo['DATA'].dt.year.isin(anos_selecionados)]
        
        semanas_disponiveis = sorted(df_filtrado_ano['DATA'].dt.isocalendar().week.unique())
        semanas_selecionadas = st.multiselect("Semanas:", semanas_disponiveis, default=semanas_disponiveis)

        dias_disponiveis = sorted(df_filtrado_ano['DATA'].dt.day.unique())
        dias_selecionados = st.multiselect("Dias:", dias_disponiveis, default=dias_disponiveis)
        
        # --- Botão de Submissão ---
        submitted = st.form_submit_button("✅ Aplicar Filtros")
        if submitted:
            st.session_state.filtros_aplicados['receita_fmt'] = receita_selecionada_fmt
            st.session_state.filtros_aplicados['entry_code'] = entry_code_selecionado
            st.session_state.filtros_aplicados['exit_code'] = exit_code_selecionado
            st.session_state.filtros_aplicados['anos'] = anos_selecionados
            st.session_state.filtros_aplicados['semanas'] = semanas_selecionadas
            st.session_state.filtros_aplicados['dias'] = dias_selecionados
            st.rerun()

def render_sidebar(df_total_completo, page_name: str):
    """Renderiza a sidebar completa, com filtros dinâmicos e o toggle de tema."""
    with st.sidebar.form("filter_form"):
        st.markdown(":blue[**Filtros de Análise**]")

        receitas_disponiveis = data_loader.obter_top_4_receitas_formatadas()
        if 'Todas' in receitas_disponiveis: receitas_disponiveis.remove('Todas')
        
        default_receita_fmt = st.session_state.filtros_aplicados.get('receita_fmt', '123')
        default_receita_full = next((r for r in receitas_disponiveis if r.startswith(default_receita_fmt)), receitas_disponiveis[0])
        receita_selecionada_fmt = st.selectbox("Receita:", ["123"], index=0, disabled=True)

        receita_num = receita_selecionada_fmt.split(' ')[0]
        df_filtrado_receita = df_total_completo[df_total_completo['PROGRAM_Nº'] == receita_num]

        codigos_entry = sorted(df_filtrado_receita['code ENTRY'].dropna().astype(str).unique().tolist())
        codigos_exit = sorted(df_filtrado_receita['code EXIT'].dropna().astype(str).unique().tolist())
        entry_code_selecionado = st.selectbox("Código de Entrada:", ['Todos'] + codigos_entry)
        exit_code_selecionado = st.selectbox("Código de Saída:", ['Todos'] + codigos_exit)
        
        st.markdown("---")

        anos_disponiveis = sorted(df_total_completo['DATA'].dt.year.unique())
        anos_selecionados = st.multiselect("Ano(s):", anos_disponiveis, default=st.session_state.filtros_aplicados.get('anos', anos_disponiveis))
        df_filtrado_ano = df_total_completo[df_total_completo['DATA'].dt.year.isin(anos_selecionados)]
        
        meses_selecionados, semanas_selecionadas, dias_selecionados = [], [], []

        if page_name in ['diaria', 'semanal', 'mensal']:
            meses_disponiveis = sorted(df_filtrado_ano['DATA'].dt.month.unique())
            selecionar_todos_meses = st.checkbox("Selecionar todos os meses", value=True, key="select_all_months_sidebar")
            if selecionar_todos_meses:
                meses_selecionados = meses_disponiveis
                st.multiselect("Mês(es):", meses_disponiveis, default=meses_disponiveis, disabled=True)
            else:
                meses_selecionados = st.multiselect("Mês(es):", meses_disponiveis, default=st.session_state.filtros_aplicados.get('meses', []))

        if page_name == 'semanal':
            semanas_disponiveis = sorted(df_filtrado_ano['DATA'].dt.isocalendar().week.unique())
            selecionar_todas_semanas = st.checkbox("Selecionar todas as semanas", value=True, key="select_all_weeks_sidebar")
            if selecionar_todas_semanas:
                semanas_selecionadas = semanas_disponiveis
                st.multiselect("Semana(s):", semanas_disponiveis, default=semanas_disponiveis, disabled=True)
            else:
                semanas_selecionadas = st.multiselect("Semana(s):", semanas_disponiveis, default=st.session_state.filtros_aplicados.get('semanas', []))
        
        if page_name == 'diaria':
            dias_disponiveis = sorted(df_filtrado_ano['DATA'].dt.day.unique())
            selecionar_todos_dias = st.checkbox("Selecionar todos os dias", value=True, key="select_all_days_sidebar")
            if selecionar_todos_dias:
                dias_selecionados = dias_disponiveis
                st.multiselect("Dia(s):", dias_disponiveis, default=dias_disponiveis, disabled=True)
            else:
                dias_selecionados = st.multiselect("Dia(s):", dias_disponiveis, default=st.session_state.filtros_aplicados.get('dias', []))

        submitted = st.form_submit_button("✅ Aplicar Filtros")
        if submitted:
            st.session_state.filtros_aplicados.update({
                'receita_fmt': receita_selecionada_fmt.split(' ')[0], 'entry_code': entry_code_selecionado,
                'exit_code': exit_code_selecionado, 'anos': anos_selecionados, 'meses': meses_selecionados,
                'semanas': semanas_selecionadas, 'dias': dias_selecionados
            })
            st.rerun()
    
    st.sidebar.markdown("---")

def render_liquid_chart_individual(score: float, titulo: str) -> str:
    """Renderiza um gráfico Liquid individual para o Health Score."""
    score_decimal = score / 100

    # Define a cor da onda com base no score
    if score < 50:
        wave_color = '#ff4d4f' # Vermelho
    elif score < 75:
        wave_color = '#faad14' # Laranja
    else:
        wave_color = '#52c41a' # Verde

    c = (
        Liquid()
        .add(
            "Health Score",
            [score_decimal],
            is_outline_show=False,
            color=[wave_color],
            label_opts=opts.LabelOpts(
                font_size=25,
                formatter=JsCode(
                    """function (param) {
                           return Math.floor(param.value * 100) + '%';
                       }"""
                ),
                position="inside",
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title=titulo,
                pos_left="center",
                pos_bottom="10%",
                title_textstyle_opts=opts.TextStyleOpts(font_size=14, color="#666")
            )
        )
    )
    return c.render_embed()

def render_liquid_chart_foco(score: float, titulo: str) -> str:
    """Renderiza um gráfico Liquid de destaque para o ponto crítico."""
    score_decimal = score / 100

    if score < 50: wave_color = '#a61d24'
    elif score < 75: wave_color = '#faad14'
    else: wave_color = '#52c41a'
        
    c = (
        Liquid()
        .add(
            "Health Score",
            [score_decimal],
            is_outline_show=False,
            color=[wave_color],
            label_opts=opts.LabelOpts(
                font_size=50,
                formatter=JsCode("""function (param) { return Math.floor(param.value * 100) + '%'; }"""),
                position="inside",
            ),
        )
        .set_global_opts(
             title_opts=opts.TitleOpts(
                title=titulo,
                pos_left="center",
                pos_bottom="15%",
                title_textstyle_opts=opts.TextStyleOpts(font_size=20, font_weight="bold", color="#333")
            )
        )
    )
    return c.render_embed()

def render_mini_liquid_chart(score: float) -> str:
    """Renderiza um gráfico Liquid pequeno, sem título, para ser usado ao lado de textos."""
    score_decimal = score / 100

    # Lógica de cores consistente
    if score >= 75: wave_color = '#52c41a'  # Verde
    elif score >= 50: wave_color = '#faad14'  # Amarelo/Laranja
    elif score >= 25: wave_color = '#ff4d4f'  # Vermelho
    else: wave_color = '#a61d24'  # Vermelho Escuro

    c = (
        Liquid()
        .add(
            "Análise",
            [score_decimal],
            is_outline_show=False,
            color=[wave_color],
            label_opts=opts.LabelOpts(
                font_size=11,
                formatter=JsCode("""function (param) { return Math.floor(param.value * 100) + '%'; }"""),
                position="inside",
            ),
        )
        # Removemos o set_global_opts para não ter título próprio
    )
    # Retorna o HTML do gráfico para ser incorporado
    return c.render_embed()


