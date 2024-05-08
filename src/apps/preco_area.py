import pandas as pd
from dash import html, dcc, Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import pathlib
from app import app

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../datasets").resolve()

# Definir df_area como uma variável global na página
df_area = pd.DataFrame()

# Layout do aplicativo
layout = html.Div([
    dcc.RadioItems(
        id='radio-selection-area',
        options=[
            {'label': 'Apresentação', 'value': 'apresentacao'},
            {'label': 'Espécie', 'value': 'especie'}
        ],
        value='apresentacao',  # Valor padrão selecionado
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(id='dropdown-container-area'),
    html.Div(
        dcc.Graph(id='bar-preco-area'),
        id='bar-container-preco-area',
        style={'display': 'none'}),
    html.Div(
        dcc.Graph(id='line-preco_area'),
        id='lline-container-preco-area',
        style={'display': 'none'})  # Container vazio para o gráfico de pizza
])

# Função para atualizar o dataframe com base nos dados enviados pelo usuário
def update_dataframe(stored_data):
    global df_area
    if stored_data is not None and 'df_area' in stored_data:
        df_area = pd.DataFrame(stored_data['df_area'])

# Callback para atualizar o dropdown com base na seleção do botão de rádio
@app.callback(
    Output('dropdown-container-area', 'children'),
    [Input('radio-selection-area', 'value')],
    [State('data-store', 'data')]  # Adicione State para acessar os dados do dcc.Store
)
def update_dropdown(selection, stored_data):
    update_dataframe(stored_data)
    if df_area.empty:
        # Se não houver dados armazenados, retorna uma mensagem vazia
        return "Importe o arquivo csv primeiro"
    
    if selection == 'apresentacao':
        return dcc.Dropdown(
            id='dropdown-area',
            options=[{'label': apresentacao, 'value': idx} for idx, apresentacao in enumerate(df_area['APRESENTACAO_NOME'].unique())],
            value=None,  # Definir o valor inicial como None
            style={'width': '50%'},
            placeholder="Selecione a Apresentação",
        )
    else:
        return dcc.Dropdown(
            id='dropdown-area',
            options=[{'label': especie, 'value': idx} for idx, especie in enumerate(df_area['MADEIRA_NOME'].unique())],
            value=None,  # Definir o valor inicial como None
            style={'width': '50%'},
            placeholder="Selecione a Espécie",
        )

# Callback para atualizar a visibilidade do gráfico com base nas seleções do usuário
@app.callback(
    Output('bar-container-preco-area', 'style'),
    [Input('dropdown-area', 'value')]
)
def update_bar_visibility(seletor_index):
    if seletor_index is None:
        # Se o dropdown for None, oculta o contêiner do gráfico
        return {'display': 'none'}
    else:
        # Caso contrário, exibe o contêiner do gráfico
        return {'display': 'block'}

# Callback para atualizar o gráfico de barras com base na seleção do dropdown e do rádio
@app.callback(
    Output('bar-preco-area', 'figure'),
    [Input('dropdown-area', 'value'),
     Input('radio-selection-area', 'value')]  
)
def update_bar_chart(selection_index, radio_value):
    if selection_index is None or df_area.empty:
        # Retorna um gráfico vazio se nenhuma seleção for feita ou se o dataframe estiver vazio
        return go.Figure()

    if radio_value == 'apresentacao':
        nome = df_area['APRESENTACAO_NOME'].unique()[selection_index]
        dropdown = 'APRESENTACAO_NOME'
        agrupamento = 'MADEIRA_NOME'
        texto_titulo = 'para cada ESPECIE'
        x_title = 'ESPECIE'
    else:
        nome = df_area['MADEIRA_NOME'].unique()[selection_index]
        dropdown = 'MADEIRA_NOME'
        agrupamento = 'APRESENTACAO_NOME'
        texto_titulo = 'para cada APRESENTACAO'
        x_title = 'APRESENTACAO'

    quantidade_calculada = ((df_area[df_area[dropdown] == nome].groupby(agrupamento)['VL_UNIT_COMERCIAL'].sum())/(df_area[df_area[dropdown] == nome].groupby(agrupamento)['VOLUME'].sum()))

    # Ordenar quantidade_calculada de acordo com as apresentações de madeira
    quantidade_calculada = quantidade_calculada.reindex(df_area[agrupamento].unique())

    # Criar o gráfico de barras
    fig = go.Figure(data=[go.Bar(x=quantidade_calculada.index, 
                                  y=quantidade_calculada.values,
                                  marker=dict(color='#66B2FF'))])

    # Personalizar o layout do gráfico de barras
    fig.update_layout(title=f'Média de preço por área de ({nome}) '+ texto_titulo,
                        xaxis_title=f'{x_title} de Madeira',
                        yaxis_title='Média (R$/M²)',
                        plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)')

    return fig

# Callback para atualizar a visibilidade do gráfico de pizza com base no clique nas barras
@app.callback(
    Output('lline-container-preco-area', 'style'),
    [Input('bar-preco-area', 'clickData')]
)
def update_line_visibility(click_data):
    if click_data is None:
        # Se não houver clique nas barras, oculta o contêiner do gráfico de pizza
        return {'display': 'none'}
    else:
        # Caso contrário, exibe o contêiner do gráfico de pizza
        return {'display': 'block'}
    
# Callback para limpar o clique nas barras quando o dropdown é alterado
@app.callback(
    Output('bar-preco-area', 'clickData'),
    [Input('dropdown-area', 'value')]
)
def clear_bar_click_data(seletor_index):
    # Retorna None para limpar o clique nas barras ao alterar o dropdown
    return None

# Callback para criar o gráfico de linha com base no clique nas barras do gráfico de barras
@app.callback(
    Output('line-preco_area', 'figure'),  # Alterado para 'figure'
    [Input('bar-preco-area', 'clickData'),
     Input('dropdown-area', 'value'),
     Input('radio-selection-area', 'value')]
)
def update_line_chart(clickData, seletor_index, radio_value):
    if clickData is None or seletor_index is None or df_area.empty:
        # Retorna um gráfico vazio se nenhum ponto for clicado ou nenhuma espécie for selecionada
        return {}

    click_nome = clickData['points'][0]['x']

    ano_mes = []
    preco_volume_mes = []

    if radio_value == 'apresentacao':
        dropdown_selecionado = df_area['APRESENTACAO_NOME'].unique()[seletor_index]
        # Filtrar o DataFrame para obter os dados relevantes
        dados_selecionados = df_area[(df_area['APRESENTACAO_NOME'] == dropdown_selecionado) & (df_area['MADEIRA_NOME'] == click_nome)]
    else:
        dropdown_selecionado = df_area['MADEIRA_NOME'].unique()[seletor_index]
        # Filtrar o DataFrame para obter os dados relevantes
        dados_selecionados = df_area[(df_area['APRESENTACAO_NOME'] == click_nome) & (df_area['MADEIRA_NOME'] == dropdown_selecionado)]
    
    
    #SK_DATA to datetime
    dados_selecionados['SK_DATA'] = pd.to_datetime(dados_selecionados['SK_DATA'], format='%Y%m%d')
    # Extrair o ano e o mês da coluna SK_DATA
    dados_selecionados['ANO'] = dados_selecionados['SK_DATA'].dt.year
    dados_selecionados['MES'] = dados_selecionados['SK_DATA'].dt.month
    for ano in sorted(dados_selecionados['ANO'].unique()):
        for mes in sorted(dados_selecionados['MES'].unique()):
            dados_temporais = dados_selecionados[(dados_selecionados['ANO'] == ano) & (dados_selecionados['MES'] == mes)]
            # Calculando e adicionando o preço médio por volume à lista
            if len(dados_temporais) > 0:
                preco_volume_mes.append((dados_temporais['VL_UNIT_COMERCIAL'].sum()) / (dados_temporais['VOLUME'].sum()))
                # Adicionando o ano e o mês formatados como 'ANO/MES' à lista
                ano_mes.append(f'{ano}/{mes}')

    # Criar o gráfico de linha
    fig_line = px.line(x=ano_mes, y=preco_volume_mes, 
                labels={'y': 'Média (R$/M²)', 'x': 'Ano/Mês'})

    # Adicionar título
    fig_line.update_layout(title=f'Preço Médio por Área ao Longo do Tempo - {dropdown_selecionado} ({click_nome})',
                        plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)')

    # Transformando Plotly Express figure em Plotly Graph Objects figure
    fig_line = go.Figure(fig_line)

    # Mostrar o gráfico
    return fig_line
