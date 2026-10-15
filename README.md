# MAVIS | Monitoramento e Análise de Variáveis Industriais de Soldagem

Dashboard de dados históricos de processo implementado em Python, Streamlit e Pandas.

## O que esta versão faz

- Analisa séries de velocidade, corrente, pressão de solda, pressão do martelador e temperatura, quando disponíveis.
- Permite selecionar receita, período e, se houver leituras brutas, códigos de entrada e saída.
- Recalcula agregações **após os filtros** quando há dados de origem adequados; sem essa possibilidade, limita a interpretação e informa a restrição.
- Exibe tendências descritivas e um **índice heurístico de desvio**, de 0 a 100, baseado em diferenças robustas contra uma referência histórica temporária.
- Sugere hipóteses técnicas a partir de uma base de conhecimento em JSON. A origem das hipóteses não é um diagnóstico automatizado.

**Importante:** o índice de desvio **não é probabilidade de falha**, nem um Health Score validado, e não autoriza decisões automáticas de parada, produção, segurança ou manutenção. Não substitui limites técnicos por receita homologados pela engenharia. Sem histórico rotulado de falhas e sem avaliação prospectiva, o sistema não faz predição comprovada.

## Como funciona a análise

1. Descarta registros com datas inválidas e organiza as séries temporalmente.
2. A tendência compara medianas do início e do fim (20% dos registros de cada ponta, mínimo de 2).
3. Com ao menos 8 registros, usa os primeiros 60% para determinar mediana e dispersão robusta (MAD e IQR), e os últimos 20% para obter o deslocamento da mediana.
4. Converte o deslocamento padronizado para um índice descritivo de 0 a 100. Limiares visuais são heurísticos, não tolerâncias físicas ou probabilidades.
5. Se a amostra é insuficiente, mostra **indisponível**, em vez de assumir risco zero ou saúde máxima.
6. Para avaliar causas e intervenções, consulte equipe de manutenção/engenharia.

A escala de conversão de leituras originais é configurada em `app/config.py` e deve ser conferida contra o sistema de aquisição (unidades de engenharia).

## Execução

Requer Python 3.11+ e acesso autorizado à base de dados:

```bash
python -m venv .venv
# ative seu ambiente virtual e instale:
pip install -r requirements.txt
streamlit run inicio.py
```

Defina em `.env` (local) ou no painel de Secrets do Streamlit:

```text
VALID_PASSWORDS=uma-senha-forte
caminho_excel=/caminho/privado/dados_resumidos_gerado.xlsx
estatistica=/caminho/privado/estatisticas_por_programa.xlsx
SENSORES_INDISPONIVEIS=TEMPERATURA
```

Não publique o arquivo `.env` nem os dados industriais. `caminho_excel` também aceita URL HTTP(S), mas **a URL deve ter controle de acesso**. O carregador exige a aba `Dados Completos`, com `DATA` e, idealmente, `PROGRAM_Nº` e colunas dos sensores. Se essas colunas estiverem presentes, calcula séries diárias/semanais/mensais/anuais a partir da base bruta. Se não estiverem, tenta as abas históricas de médias: `Médias Diárias`, `Médias Semanais`, `Médias Mensais`, `Médias Anuais` ou as abas específicas da receita.

## Testes

```bash
pip install pytest
python -m pytest -q
```

## Proteção de dados e acesso

O repositório já possuía arquivos em `data/` versionados, apesar do `.gitignore`. **Ignorar um diretório não remove o que já foi publicado, nem apaga o histórico Git.** Se forem dados corporativos, restrinja o repositório e trate a exposição com os responsáveis pela informação. Evite publicar históricos de produção em URLs abertas. A autenticação por senha compartilhada é provisória; para implantação corporativa, use autenticação de identidade individual, autorização por perfil, HTTPS e trilhas de auditoria.

## Escopo de validação

Os testes automatizados verificam a lógica sobre dados sintéticos. Antes de uso operacional, confronte médias e séries com o processo de aquisição, valide escala/unidades, limites por receita, períodos de calibração, falhas rotuladas, variações normais de processo, amostras perdidas e alarmes falsos. A disponibilidade física do pirômetro deve ser confirmada antes de removê-lo de `SENSORES_INDISPONIVEIS`.

## Curvas individuais e alertas de variação

Abra **Análise por Solda** na navegação do Streamlit. Os arquivos
`data/dados_detalhados_<receita>.parquet` são lidos individualmente.
Cada `WELDNº` possui pontos sucessivos em `ID_PONTO`. O horário `DATAHORA`
é da solda inteira e não da amostra. Não inferir frequência de oscilação em Hz.

A nova análise não depende da média diária. Avalia, para cada sensor habilitado,
o patamar (mediana), a dispersão dentro da solda (P95-P05), a variação ponto a
ponto (P95 do delta absoluto) e os picos locais (P99 do resíduo para a mediana
móvel). Compara o resultado exclusivamente com até 48 soldas **anteriores**
da mesma receita, código de entrada, saída e `MeasP`, exigindo pelo menos
12 referências válidas. O painel permite examinar o registro original e o
envelope empírico por `ID_PONTO`, também restrito às soldas anteriores.

Os limiares atuais são *candidatos para triagem*, não limites de engenharia.
Amplitude robusta não equivale à probabilidade de falha, e a ausência de
sinalização não garante integridade física. O sistema pode observar oscilações
de corrente compatíveis com várias causas, mas não concluir "fusível trincado"
sem evidência elétrica e inspeção. Para classificar risco iminente são necessários
eventos rotulados, dados de manutenção, limites por receita e validação física.

Os Parquets versionados contêm informações industriais. Avalie a necessidade de
restringir acesso e higienizar o histórico público do Git antes de publicar dados novos.
