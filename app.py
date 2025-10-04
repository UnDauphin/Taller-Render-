import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback
import warnings
warnings.filterwarnings('ignore')

# Cargar datos
df = pd.read_csv('afiliados_por_departamento_y_regimen_limpio.csv', dtype={"CodDepto":"str"})
shape_colombia = gpd.read_file('coordenadas/COLOMBIA/COLOMBIA.shp')

# 1. Merge con shapefile
merged_data = shape_colombia.merge(
    df,
    left_on='DPTO_CCDGO',
    right_on='CodDepto'
)

# Lista de regímenes disponibles
regimenes = ['Contributivo', 'Subsidiado', 'Especial']

# Aplicación Dash optimizada
app = Dash(__name__)

app.layout = html.Div([
    html.H1('Dashboard Colombia - Afiliados por Régimen', 
            style={'textAlign': 'center', 'marginBottom': 20}),
    
    # Sección de Contexto
    html.Div([
        html.H2('Contexto', style={'marginTop': 30, 'marginBottom': 15}),
        html.P([
            "Este dashboard analiza la distribución de afiliados al sistema de salud en Colombia según los tres regímenes existentes: ",
            html.Strong("Contributivo"),
            ", ",
            html.Strong("Subsidiado"),
            " y ",
            html.Strong("Especial"),
            ". Los datos provienen del ",
            html.A("Portal de Datos Abiertos de Colombia", 
                   href="https://www.datos.gov.co/Salud-y-Protecci-n-Social/N-mero-de-afiliados-por-departamento-municipio-y-r/hn4i-593p/about_data",
                   target="_blank"),
            " y representan la situación actual del sistema de salud colombiano a nivel departamental."
        ]),
        html.P("El régimen Contributivo se financia con aportes de trabajadores y empleadores, el Subsidiado está dirigido a población vulnerable con subsidio estatal, y el Especial cubre grupos específicos como fuerzas armadas y docentes.")
    ], style={'padding': '20px', 'backgroundColor': '#f0f8ff', 'borderRadius': '10px', 'marginBottom': '20px'}),
    
    # Filtro
    html.Div([
        html.H3('Filtro', style={'marginTop': 20, 'marginBottom': 10}),
        dcc.Dropdown(
            id='filtro-regimen',
            options=[{'label': regimen, 'value': regimen} for regimen in regimenes],
            value=regimenes[0],  # Valor por defecto
            placeholder='Seleccionar régimen...',
            style={'width': '50%', 'margin': 'auto'}
        )
    ]),
    
    # KPIs con unidades
    html.Div([
        html.Div(id='kpi-cards', style={
            'display': 'flex', 
            'justifyContent': 'space-around',
            'margin': '20px 0'
        })
    ]),
    
    # Mapa y boxplot en fila
    html.Div([
        html.Div([
            html.H4('Mapa de Distribución'),
            dcc.Graph(
                id='mapa-colombia',
                config={'scrollZoom': False}
            )
        ], style={'width': '60%', 'display': 'inline-block'}),
        
        html.Div([
            html.H4('Distribución por Departamento'),
            dcc.Graph(
                id='boxplot-kpi',
                config={'staticPlot': False}
            )
        ], style={'width': '38%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ]),
    
    # Narrativa contextual
    html.Div([
        html.H4('Análisis y Narrativa'),
        html.P(id='narrativa-texto', style={'textAlign': 'justify'})
    ], style={'marginTop': 20, 'padding': '15px', 'backgroundColor': '#f9f9f9'}),
    
    # Sección de Conclusiones
    html.Div([
        html.H2('Conclusiones', style={'marginTop': 40, 'marginBottom': 15}),
        html.Ul([
            html.Li("Existen disparidades significativas en la distribución de afiliados entre departamentos, reflejando diferencias poblacionales y de desarrollo económico."),
            html.Li("El régimen contributivo muestra mayor concentración en áreas urbanas y económicamente desarrolladas."),
            html.Li("El régimen subsidiado presenta una distribución más homogénea a nivel nacional, indicando una cobertura amplia de población vulnerable."),
            html.Li("El régimen especial, aunque con menores números absolutos, es crucial para grupos poblacionales específicos con necesidades particulares."),
            html.Li("La visualización de datos permite identificar oportunidades para mejorar la equidad en el acceso a servicios de salud across el territorio nacional.")
        ]),
        html.P("Estos insights pueden informar la toma de decisiones en políticas públicas de salud y la asignación de recursos para reducir las brechas identificadas.")
    ], style={'padding': '20px', 'backgroundColor': '#fff0f5', 'borderRadius': '10px', 'marginTop': '30px'})
], style={'padding': '20px'})

# Callback para actualizar todos los componentes
@callback(
    [Output('mapa-colombia', 'figure'),
     Output('boxplot-kpi', 'figure'),
     Output('kpi-cards', 'children'),
     Output('narrativa-texto', 'children')],
    [Input('filtro-regimen', 'value')]
)
def update_dashboard(regimen_seleccionado):
    # Asegurar que tenemos datos
    if merged_data.empty:
        return go.Figure(), go.Figure(), "No hay datos", "No hay datos disponibles"
    
    # 1. Mapa coroplético optimizado
    fig_mapa = px.choropleth_mapbox(
        merged_data,
        geojson=merged_data.geometry,
        locations=merged_data.index,
        color=regimen_seleccionado,
        color_continuous_scale='Viridis',
        mapbox_style='carto-positron',
        zoom=4,
        center={'lat': 4.6, 'lon': -74},
        opacity=0.7,
        labels={regimen_seleccionado: f'Afiliados {regimen_seleccionado}'},
        hover_data=['Departamento', regimen_seleccionado]
    )
    fig_mapa.update_layout(
        margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
        height=500
    )
    
    # 2. Boxplot optimizado
    fig_box = px.box(
        df,
        y=regimen_seleccionado,
        title=f'Distribución - Régimen {regimen_seleccionado}',
        points=False
    )
    fig_box.update_layout(
        showlegend=False,
        height=500,
        margin={'t': 50}
    )
    
    # 3. KPIs con unidades
    total_afiliados = df[regimen_seleccionado].sum()
    promedio_por_depto = df[regimen_seleccionado].mean()
    departamentos_con_afiliados = df[df[regimen_seleccionado] > 0].shape[0]
    max_afiliados = df[regimen_seleccionado].max()
    depto_max = df.loc[df[regimen_seleccionado].idxmax(), 'Departamento']
    
    kpi_cards = [
        html.Div([
            html.H4(f"{total_afiliados:,.0f}"),
            html.P("Total Afiliados")
        ], style={
            'padding': '15px', 
            'backgroundColor': '#e8f4fd', 
            'borderRadius': '5px',
            'textAlign': 'center',
            'width': '22%'
        }),
        html.Div([
            html.H4(f"{promedio_por_depto:,.0f}"),
            html.P("Promedio por Depto")
        ], style={
            'padding': '15px', 
            'backgroundColor': '#e8f4fd', 
            'borderRadius': '5px',
            'textAlign': 'center',
            'width': '22%'
        }),
        html.Div([
            html.H4(f"{departamentos_con_afiliados}"),
            html.P("Deptos con Afiliados")
        ], style={
            'padding': '15px', 
            'backgroundColor': '#e8f4fd', 
            'borderRadius': '5px',
            'textAlign': 'center',
            'width': '22%'
        }),
        html.Div([
            html.H4(f"{max_afiliados:,.0f}"),
            html.P(f"Máx: {depto_max}"[:15] + "...")
        ], style={
            'padding': '15px', 
            'backgroundColor': '#e8f4fd', 
            'borderRadius': '5px',
            'textAlign': 'center',
            'width': '22%'
        })
    ]
    
    # 4. Narrativa contextual - sin formato markdown
    if regimen_seleccionado == 'Contributivo':
        narrativa = f"""
        El régimen Contributivo presenta un total de {total_afiliados:,.0f} afiliados, distribuidos 
        en {departamentos_con_afiliados} departamentos. El promedio de afiliados por departamento es de 
        {promedio_por_depto:,.0f} personas. Este régimen, financiado por aportes de trabajadores y empleadores,
        muestra su mayor concentración en {depto_max} con {max_afiliados:,.0f} afiliados.
        La distribución geográfica evidencia mayores densidades en zonas urbanas y económicamente activas.
        """
    elif regimen_seleccionado == 'Subsidiado':
        narrativa = f"""
        El régimen Subsidiado cuenta con {total_afiliados:,.0f} afiliados en total, 
        cubriendo {departamentos_con_afiliados} departamentos. El promedio por departamento es de 
        {promedio_por_depto:,.0f} personas. Este régimen, dirigido a población vulnerable con subsidio estatal,
        tiene su mayor presencia en {depto_max} con {max_afiliados:,.0f} afiliados.
        Se observa una distribución más homogénea a nivel nacional, reflejando la cobertura de población vulnerable.
        """
    else:  # Especial
        narrativa = f"""
        El régimen Especial registra {total_afiliados:,.0f} afiliados en total, 
        presentes en {departamentos_con_afiliados} departamentos. El promedio por departamento es de 
        {promedio_por_depto:,.0f} personas. Este régimen, diseñado para grupos específicos como fuerzas armadas
        y docentes, concentra su mayor número en {depto_max} con {max_afiliados:,.0f} afiliados.
        La distribución puede reflejar la ubicación de bases militares, instituciones educativas y otros grupos específicos.
        """
    
    return fig_mapa, fig_box, kpi_cards, narrativa

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)










