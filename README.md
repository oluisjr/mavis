# MAVIS - Dashboard de Monitoramento

Dashboard para Monitoramento, Análise e Visualização de Indicadores de Solda.

## Descrição

Esta aplicação Streamlit fornece uma análise detalhada de dados de sensores de um processo de solda, incluindo visualizações diárias, semanais, mensais e anuais. Além disso, utiliza modelos de inteligência artificial (simulados) para prever riscos, calcular o impacto financeiro e sugerir análises de causa raiz.

## Instalação e Execução

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-seu-repositorio>
    cd mavis_dashboard
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    - Renomeie o arquivo `.env.example` para `.env`.
    - Edite o arquivo `.env` e adicione os caminhos ou URLs para seus arquivos de dados (`caminho_excel`, `estatistica`).

5.  **Execute a aplicação Streamlit:**
    ```bash
    streamlit run main.py
    ```

A aplicação estará disponível em seu navegador no endereço `http://localhost:8501`.