import pandas as pd
from dash import html, dcc, Input, Output, State
import plotly.graph_objs as go
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
        id='radio-selection-area-vendido',
        options=[
            {'label': 'Apresentação', 'value': 'apresentacao'},
            {'label': 'Espécie', 'value': 'especie'}
        ],
        value='apresentacao',  # Valor padrão selecionado
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(id='warning-message-area', style={'display': 'block'}),
    html.Div(
        dcc.Graph(id='bar-pai-area'),
        id='bar-container-pai-area',
        style={'display': 'none'}),
    html.Div([
        html.Div(
            dcc.Graph(id='bar-chart-area-vendido'),
            id='bar-container-area-vendido',
            style={'display': 'none'}),
        html.Div(
            dcc.Graph(id='pie-chart_area_vendido'),
            id='pie-container-area-vendido',
            style={'display': 'none'})  # Container vazio para o gráfico de pizza
    ], className="multiplos-graph")
])

# Função para atualizar o dataframe com base nos dados enviados pelo usuário
def update_dataframe(stored_data):
    global df_area
    if stored_data is not None and 'df_area' in stored_data:
        df_area = pd.DataFrame(stored_data['df_area'])

@app.callback(
    Output('warning-message-area', 'children'),
    [Input('data-store', 'data')]
)
def display_warning_message(stored_data):
    if df_area.empty:
        # Se não houver dados armazenados, retorna uma mensagem
        return "Importe o arquivo csv primeiro"
    else:
        return ""
    
@app.callback(
    Output('bar-container-pai-area', 'style'),
    [Input('data-store', 'data')]
)
def update_bar_visibility_pai(stored_data):
    if not stored_data:
        return {'display': 'none'}
    else:
        return {'display': 'block'}
    
@app.callback(
    Output('bar-pai-area', 'figure'),
    [Input('radio-selection-area-vendido', 'value')],
    [State('data-store', 'data')]  # Adicione State para acessar os dados do dcc.Store
)
def update_bar_chart_pai(radio_value, stored_data):
    update_dataframe(stored_data)
    
    if radio_value == 'apresentacao':
        quantidade_calculada = df_area.groupby('APRESENTACAO_NOME')['VOLUME'].sum()
        # Ordenar quantidade_calculada de acordo com a seleção 
        quantidade_calculada = quantidade_calculada.reindex(df_area['APRESENTACAO_NOME'].unique())
    else:
        quantidade_calculada = df_area.groupby('MADEIRA_NOME')['VOLUME'].sum()
        # Ordenar quantidade_calculada de acordo com a seleção 
        quantidade_calculada = quantidade_calculada.reindex(df_area['MADEIRA_NOME'].unique())
        
    
    
    # Criar o gráfico de barras
    fig = go.Figure(data=[go.Bar(x=quantidade_calculada.index, 
                                  y=quantidade_calculada.values,
                                  marker=dict(color='#66B2FF'))])
    
    # Personalizar o layout do gráfico de barras
    fig.update_layout(title=f'Soma da Área por {radio_value.upper()}',
                      xaxis_title=f'{radio_value.upper()} de Madeira',
                      yaxis_title='Soma do Área',
                      plot_bgcolor='rgba(0,0,0,0)', 
                      paper_bgcolor='rgba(0,0,0,0)')
    return fig


# Callback para atualizar a visibilidade do gráfico com base nas seleções do usuário
@app.callback(
    Output('bar-container-area-vendido', 'style'),
    [Input('bar-pai-area', 'clickData')]
)
def update_bar_visibility(click_data):
    if click_data is None:
        # Se não houver clique nas barras, oculta o contêiner do gráfico de pizza
        return {'display': 'none'}
    else:
        # Caso contrário, exibe o contêiner do gráfico de pizza
        return {'display': 'block'}

# Callback para atualizar o gráfico de barras com base na espécie de madeira selecionada
@app.callback(
    Output('bar-chart-area-vendido', 'figure'),
    [Input('bar-pai-area', 'clickData'),
     Input('radio-selection-area-vendido', 'value')]
)
def update_bar_chart_filho(clickData, radio_value):
    if clickData is None or df_area.empty:
        # Retorna um gráfico vazio se nenhum ponto for clicado ou nenhuma espécie for selecionada
        return {}

    click_index = clickData['points'][0]['pointIndex']

    if radio_value == 'apresentacao':
        nome = df_area['APRESENTACAO_NOME'].unique()[click_index]
        seletor = 'APRESENTACAO_NOME'
        agrupamento = 'MADEIRA_NOME'
        texto_titulo = 'para cada ESPECIE'
        x_title = 'ESPECIE'
    else:
        nome = df_area['MADEIRA_NOME'].unique()[click_index]
        seletor = 'MADEIRA_NOME'
        agrupamento = 'APRESENTACAO_NOME'
        texto_titulo = 'para cada APRESENTACAO'
        x_title = 'APRESENTACAO'

    quantidade_calculada = df_area[df_area[seletor] == nome].groupby(agrupamento)['VOLUME'].sum()

    # Ordenar quantidade_calculada de acordo com a seleção 
    quantidade_calculada = quantidade_calculada.reindex(df_area[agrupamento].unique())

    # Criar o gráfico de barras
    fig = go.Figure(data=[go.Bar(x=quantidade_calculada.index, 
                                  y=quantidade_calculada.values,
                                  marker=dict(color='#66B2FF'))])

    # Personalizar o layout do gráfico de barras
    fig.update_layout(title=f'Distribuição do área de ({nome}) ' + texto_titulo,
                      xaxis_title=f'{x_title} de Madeira',
                      yaxis_title='Soma do Área',
                      plot_bgcolor='rgba(0,0,0,0)', 
                      paper_bgcolor='rgba(0,0,0,0)')

    return fig

# Callback para atualizar a visibilidade do gráfico de pizza com base no clique nas barras
@app.callback(
    Output('pie-container-area-vendido', 'style'),
    [Input('bar-chart-area-vendido', 'clickData')]
)
def update_pie_visibility(click_data):
    if click_data is None:
        # Se não houver clique nas barras, oculta o contêiner do gráfico de pizza
        return {'display': 'none'}
    else:
        # Caso contrário, exibe o contêiner do gráfico de pizza
        return {'display': 'block'}


# Callback para criar o gráfico de pizza com base no clique nas barras do gráfico de barras
@app.callback(
    Output('pie-chart_area_vendido', 'figure'),  # Alterado para 'figure'
    [Input('bar-pai-area', 'clickData'),
     Input('bar-chart-area-vendido', 'clickData'),
     Input('radio-selection-area-vendido', 'value')]
)
def update_pie_chart(clickDataPai, clickDataFilho, radio_value):
    if clickDataPai is None or clickDataFilho is None or df_area.empty:
        # Retorna um gráfico vazio se nenhum ponto for clicado ou nenhuma espécie for selecionada
        return {}

    click_pai = clickDataPai['points'][0]['x']
    click_filho = clickDataFilho['points'][0]['x']

    if radio_value == 'apresentacao':
        texto_adicional = f'{click_pai} ({click_filho})'
        # Filtrar o DataFrame para obter os dados relevantes
        dados_selecionados = df_area[(df_area['APRESENTACAO_NOME'] == click_pai) & (df_area['MADEIRA_NOME'] == click_filho)]
    else:
        texto_adicional = f'{click_filho} ({click_pai})'
        # Filtrar o DataFrame para obter os dados relevantes
        dados_selecionados = df_area[(df_area['APRESENTACAO_NOME'] == click_filho) & (df_area['MADEIRA_NOME'] == click_pai)]

        # Contar as categorias de df_area_final['COD_MODELO']
    contagem_categorias = dados_selecionados['COD_MODELO'].value_counts()

    # Criar o gráfico de pizza
    fig_pie = go.Figure(data=[go.Pie(labels=['Prestação de Serviços', 'Varejo'], 
                                     values=contagem_categorias.values,
                                     marker=dict(colors=['#FF9999', '#99FF99']))])
    fig_pie.update_layout(title=f'Tipo de venda para - '+texto_adicional,
                      paper_bgcolor='rgba(0,0,0,0)')

    return fig_pie