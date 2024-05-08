import dash
from dash import dcc, html, Input, Output, State
import base64
import io
import datetime
from dash.exceptions import PreventUpdate
import pandas as pd

# Connect to main app.py file
from app import app

# Connect to your app pages
from apps import volume_vendido, preco_volume, area_vendida, preco_area
# Layout da aplicação
app.layout = html.Div([
    html.Div("Tributação de Produtos de Madeira Serrada no RN", className="titulo"),
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='data-store', storage_type='memory'),
    html.Div(id='nav-links', className="row"),
    html.Div([
        html.P('A classificação de produtos de madeira é um grande desafio devido à falta de padronização nas descrições dos produtos. No entanto, esse processo é imprescindível para projetos subsequentes, como o cálculo de preço médio e pauta fiscal.'),
        html.P('O objetivo deste projeto foi classificar os produtos de madeira em dois níveis específicos: espécie e apresentação, além de calcular o volume dos produtos classificados.'),
        html.P(['Por exemplo, considere a seguinte descrição:', html.Br(), html.B('Descrição: angelim linha 5x11cm 3mt'), html.Br(), 'Neste caso, devemos classificá-la como ', html.B('Espécie: angelim, Apresentação: linha, Unidade: 0.0165m³')]),
        html.P(['Para isso, foram utilizadas técnicas de processamento de linguagem natural, como expressões regulares em conjunto com o algoritmo de Levenshtein, para extrair do texto as informações de espécie e apresentação. Com isso, conseguimos identificar a espécie em ', html.B('77.5%'), ' e a apresentação em ', html.B('84%'), ' do conjunto de dados.']),
        html.P(['No cálculo do volume, aplicamos uma abordagem semelhante, buscando conjuntos de números que seguem certos padrões, como "número unidade x número unidade" ou "número unidade x número unidade x número unidade". Esses números são então multiplicados pelas unidades correspondentes (caso não haja uma unidade acompanhando os números, assume-se o padrão cm x cm x m). Os dois menores números são comparados à espessura e largura especificadas na ', html.B('NBR 14807'), '. Se estiverem dentro do intervalo especificado, o volume é calculado. No caso de padrões com apenas dois números, espessura e largura, calculamos apenas a área.', html.Br(), 'Dessa forma, conseguimos calcular corretamente o volume de ', html.B('25.5%'), ' de todo o conjunto de dados. Porém, se considerarmos apenas as descrições que contêm pelo menos um número, esse valor chega a ', html.B('37.7%'), '.']),
        html.P('Para acessar o conteúdo das outras páginas é necessário o CSV com os dados de madeira, para ficar mais simples alguns gráficos são gerados ao interagir com o primeiro gráfico ou o seletor, ao clicar em qualquer barra dos gráficos é gerado uma outra visualização utilizando o conteúdo selecionado.'),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                html.B('Arraste e solte ou '),
                html.A('selecione um arquivo CSV')
            ]),
            className="upload",
            # Allow multiple files to be uploaded
            multiple=False)
    ],id='principal', className="row"),

    html.Div(id='output-data-upload'),
    html.Div(id='page-content', children=[])
])


@app.callback(
    Output('nav-links', 'children'),
    [Input('url', 'pathname')]
)
def update_nav_links(pathname):
    links = [
        ('Início', '/'),
        ('Volume Vendido', '/apps/volume_vendido'),
        ('Preço Médio Volume', '/apps/preco_volume'),
        ('Área Vendida', '/apps/area_vendida'),
        ('Preço Médio Área', '/apps/preco_area')
    ]
    nav_links = []
    for link_text, link_href in links:
        active_class = 'active' if pathname == link_href else ''
        nav_links.append(
            dcc.Link(
                link_text,
                href=link_href,
                className=f"nav-link {active_class}"
            )
        )
    return nav_links


@app.callback(
    [Output('output-data-upload', 'children'),
     Output('data-store', 'data')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename'),
     State('upload-data', 'last_modified'),
     State('data-store', 'data')]
)
def update_output(content, filename, date, stored_data):
    if content is None:
        raise PreventUpdate
    else:
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        # Assuming that the user uploads a CSV file
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        # Convertendo a coluna 'NUMEROS' e 'PROFUNDIDADE' para listas
        df['NUMEROS'] = df['NUMEROS'].apply(lambda x: [float(num) for num in x.strip('[]').split(',')])
        df['PROFUNDIDADE'] = df['PROFUNDIDADE'].apply(lambda x: [float(num) for num in str(x).strip('[]').split(',') if num.strip()])
        df_vol = df[(df['NUMEROS'].str.len() > 2) | (df['PROFUNDIDADE'].str.len() > 0)]
        df_area = df[(df['NUMEROS'].str.len() <= 2) & (df['PROFUNDIDADE'].str.len() <= 0)]
        # Inicializar stored_data como um dicionário vazio se estiver vazio
        if not stored_data:
            stored_data = {}
        
        # Converter df_vol para uma lista de dicionários antes de armazenar
        stored_data['df_vol'] = df_vol.to_dict('records')
        stored_data['df_area'] = df_area.to_dict('records')
        
        mais_antigo = df.sort_values(by='SK_DATA')['SK_DATA'].iloc[0]
        mais_recente = df.sort_values(by='SK_DATA')['SK_DATA'].iloc[-1]
        # Converter o objeto datetime para uma string antes de retorná-lo
        formatted_date = datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S')
        
        return (
            html.Div([
                html.H5(filename + f' Upload finalizado com sucesso. Dados de {mais_antigo} a {mais_recente}'),
                html.H6(formatted_date),
            ]),
            stored_data
        )


@app.callback(Output('page-content', 'children'),
              Output('principal', 'style'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/volume_vendido':
        return volume_vendido.layout,{'display': 'none'}
    elif pathname == '/apps/preco_volume':
        return preco_volume.layout,{'display': 'none'}
    elif pathname == '/apps/area_vendida':
        return area_vendida.layout,{'display': 'none'}
    elif pathname == '/apps/preco_area':
        return preco_area.layout,{'display': 'none'}
    else:
        return "",  {'display': 'block'}


if __name__ == '__main__':
    app.run_server(debug=False)
