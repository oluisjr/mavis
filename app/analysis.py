from . import config

def analisar_tendencia(dados, eixo_y, sensor=None):
    """Analisa a tendência global e a variação instantânea dos dados."""
    if len(dados) < 4:
        return "Período selecionado muito curto para análise confiável."

    # --- Cálculo da Tendência Global ---
    inicio = dados[eixo_y].iloc[:2].mean() if sensor == "TEMPERATURA" else dados[eixo_y].iloc[:3].mean()
    fim = dados[eixo_y].iloc[-2:].mean() if sensor == "TEMPERATURA" else dados[eixo_y].iloc[-3:].mean()
    variacao_global = ((fim - inicio) / inicio) * 100 if inicio != 0 else 0

    # --- Cálculo da Variação Instantânea ---
    derivadas = dados[eixo_y].diff()
    derivadas_percentual = (derivadas / dados[eixo_y].shift(1)) * 100
    derivada_media = derivadas_percentual.mean()

    # --- Lógica para criar as descrições ---
    if variacao_global < -1:
        desc_global = f"**tendência de queda** (`{variacao_global:.2f}%`)"
    elif variacao_global > 1:
        desc_global = f"**tendência de alta** (`{variacao_global:.2f}%`)"
    else:
        desc_global = f"**tendência estável** (`{variacao_global:.2f}%`)"

    if derivada_media < -0.5:
        desc_inst = f"**variação negativa** (`{derivada_media:.2f}%` por passo)"
    elif derivada_media > 0.5:
        desc_inst = f"**variação positiva** (`{derivada_media:.2f}%` por passo)"
    else:
        desc_inst = f"**variação estável** (`{derivada_media:.2f}%` por passo)"

    return f"No período, apresenta {desc_global} com {desc_inst}"

def detectar_anomalia(df_filtrado, sensor):
    """Analisa a tendência de um sensor e retorna seu status individual."""
    LIMIAR_ANOMALIA = 10.0
    LIMIAR_ATENCAO = 5.0
    LIMIAR_CUIDADO = 1.0

    dados = df_filtrado[[sensor]].dropna()

    if len(dados) < 4:
        return "⚪ Análise de tendência indisponível (poucos dados)"

    inicio = dados[sensor].iloc[:3].mean()
    fim = dados[sensor].iloc[-3:].mean()
    variacao_global = abs(((fim - inicio) / inicio) * 100) if inicio != 0 else 0

    derivadas_percentual = (dados[sensor].diff() / dados[sensor].shift(1)) * 100
    derivada_media = derivadas_percentual.mean()

    if variacao_global > LIMIAR_ANOMALIA or abs(derivada_media) > LIMIAR_ANOMALIA:
        return "🔴 **Status:** Anomalia detectada!"
    elif variacao_global > LIMIAR_ATENCAO or abs(derivada_media) > LIMIAR_ATENCAO:
        return "🟠 **Status:** Atenção (tendência significativa)"
    elif variacao_global > LIMIAR_CUIDADO or abs(derivada_media) > LIMIAR_CUIDADO:
        return "🟡 **Status:** Atenção (leve tendência)"
    else:
        return "🟢 **Status:** Normal"

def calcular_health_score(risco: float):
    """Calcula um Health Score de 0 a 100 com base em um único risco."""
    if not isinstance(risco, (int, float)):
        return 100.0
    score = 100 - risco
    return round(max(0, score), 1)

def analisar_causa_raiz(sensor_com_maior_risco: str):
    """Busca em uma base de conhecimento as causas e ações para um sensor."""
    analise = config.BASE_CONHECIMENTO_CAUSA_RAIZ.get(sensor_com_maior_risco)
    if analise is None:
        analise = config.BASE_CONHECIMENTO_CAUSA_RAIZ.get('DEFAULT')

    # --- BLOCO DE SEGURANÇA ADICIONADO ---
    # Garante que, mesmo que o JSON esteja mal configurado, a função nunca retornará None.
    if analise is None:
        return {
            'causas_provaveis': ["- Base de conhecimento não configurada."],
            'acoes_recomendadas': ["- Verificar o arquivo root_cause_analysis.json."]
        }
    return analise

def calcular_impacto_financeiro(riscos: dict):
    """Calcula o impacto financeiro total e individual por sensor."""
    impacto_individual = {}
    impacto_total = 0
    if not riscos:
        return impacto_total, impacto_individual

    for sensor, risco in riscos.items():
        if isinstance(risco, (int, float)) and sensor in config.CUSTOS_OPERACIONAIS:
            impacto = (risco / 100) * config.CUSTOS_OPERACIONAIS[sensor]
            impacto_individual[sensor] = impacto
            impacto_total += impacto
    
    return impacto_total, impacto_individual

# def simular_risco_por_regras(df_dados, sensor: str):
#     """Simula uma pontuação de risco (0-100) com uma lógica de mapeamento direto e realista."""
#     dados = df_dados[[sensor]].dropna().tail(20)
#     if len(dados) < 4: return 0

#     inicio = dados[sensor].iloc[:3].mean()
#     fim = dados[sensor].iloc[-3:].mean()
#     risco_base = 0

#     # Lógica específica e linear para o sensor de TEMPERATURA
#     if sensor == 'TEMPERATURA':
#         variacao_absoluta = abs(fim - inicio)
#         volatilidade_absoluta = dados[sensor].diff().abs().mean()
#         risco_calculado = risco_base + (variacao_absoluta * 4.0) + (volatilidade_absoluta * 8.0)
    
#     # ### INÍCIO DA LÓGICA DE RISCO UNIFICADA E CORRIGIDA ###
#     else:
#         # A base do risco é a variação global, exatamente como na análise de tendência.
#         variacao_global_percentual = abs(((fim - inicio) / inicio) * 100) if inicio != 0 else 0
        
#         # Mapeamento direto da variação para o risco, alinhado com os status de anomalia.
#         if variacao_global_percentual > 5.0:  # Nível Anomalia
#             # Mapeia linearmente a variação de 10-20% para um risco de 75-100%
#             fator_agressividade = 5.2 if sensor == 'CORRENTE' else 1.0
#             risco_calculado = 75 + (variacao_global_percentual - 10) * 2.5 * fator_agressividade
#         elif variacao_global_percentual > 5.0:  # Nível Atenção Significativa
#             # Mapeia linearmente a variação de 5-10% para um risco de 50-75%
#             risco_calculado = 50 + (variacao_global_percentual - 5) * 15.0
#         elif variacao_global_percentual > 1.0:  # Nível Leve Tendência
#             # Mapeia linearmente a variação de 1-5% para um risco de 20-50%
#             risco_calculado = 20 + (variacao_global_percentual - 1) * 7.5
#         else:  # Nível Estável
#             risco_calculado = risco_base + variacao_global_percentual * 5.0

#         # Adiciona uma pequena penalidade pela volatilidade (ruído)
#         volatilidade_media_percentual = abs((dados[sensor].diff() / dados[sensor].shift(1)) * 100).mean()
#         penalidade_volatilidade = volatilidade_media_percentual * 0.5
#         risco_calculado += penalidade_volatilidade
#     # ### FIM DA LÓGICA DE RISCO UNIFICADA ###

#     risco_final = min(risco_calculado, 100.0)
    
#     return round(risco_final, 1)
def simular_risco_por_regras(df_dados, sensor: str):
    """
    Calcula o Potencial de Falha com base em limiares fixos da variação da tendência,
    garantindo consistência com o Status de Anomalia.
    """
    dados = df_dados[[sensor]].dropna()
    if len(dados) < 4: return 5.0

    inicio = dados[sensor].iloc[:3].mean()
    fim = dados[sensor].iloc[-3:].mean()
    
    # Lógica específica e linear para o sensor de TEMPERATURA
    if sensor == 'TEMPERATURA':
        variacao_absoluta = abs(fim - inicio)
        # Lógica de mapeamento para variação absoluta (em graus)
        if variacao_absoluta > 5: return 85.0
        elif variacao_absoluta >= 4: return 65.0
        elif variacao_absoluta >= 3: return 40.0
        elif variacao_absoluta > 1: return 25.0
        else: return 10.0
    
    # ### INÍCIO DA LÓGICA DE RISCO UNIFICADA E CORRIGIDA ###
    else:
        # A base do risco é a variação global, exatamente como na análise de tendência.
        variacao_global_percentual = abs(((fim - inicio) / inicio) * 100) if inicio != 0 else 0
        
        # Mapeamento direto da variação para uma pontuação de risco fixa.
        # Os valores de risco são representativos de cada categoria.
        if variacao_global_percentual > 10.0:
            return 85.0  # Anomalia
        elif variacao_global_percentual >= 8.0:
            return 65.0  # Risco Grave
        elif variacao_global_percentual >= 5.0:
            return 40.0  # Risco Moderado
        elif variacao_global_percentual > 1.0:
            return 25.0  # Risco Leve
        else:
            return 10.0  # Normal
