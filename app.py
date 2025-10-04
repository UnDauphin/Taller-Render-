import os
import warnings
warnings.filterwarnings('ignore')

# Importar librerías
try:
    import pandas as pd
    import geopandas as gpd
    import plotly.express as px
    import plotly.graph_objects as go
    from dash import Dash, dcc, html, Input, Output, callback
    print("✅ Todas las librerías importadas correctamente")
except ImportError as e:
    print(f"❌ Error importando librerías: {e}")
    raise

# Configurar la aplicación
app = Dash(__name__)
server = app.server

# Variables globales para almacenar datos
df = None
merged_data = None
regimenes = ['Contributivo', 'Subsidiado', 'Especial']
data_loaded = False

# Función para cargar datos (se llama una sola vez)
def load_data():
    global df, merged_data, data_loaded
    
    try:
        print("📂 Cargando datos CSV...")
        df = pd.read_csv('afiliados_por_departamento_y_regimen_limpio.csv', dtype={"CodDepto": "str"})
        print(f"✅ CSV cargado: {len(df)} filas")
        
        print("🗺️ Cargando shapefile...")
        # Optimizar la carga del shapefile
        shape_colombia = gpd.read_file('coordenadas/COLOMBIA/COLOMBIA.shp')
        print(f"✅ Shapefile cargado: {len(shape_colombia)} geometrías")
        
        # Merge con shapefile
        merged_data = shape_colombia.merge(
            df,
            left_on='DPTO_CCDGO',
            right_on='CodDepto'
        )
        print("✅ Merge completado exitosamente")
        data_loaded = True
        
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        data_loaded = False

# Cargar datos al iniciar (pero no bloquear el inicio de la app)
import threading
def load_data_async():
    thread = threading.Thread(target=load_data)
    thread.daemon = True
    thread.start()

load_data_async()

# Layout de la aplicación (sin bloquear en la carga de datos)
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
    
    # Estado de carga
    html.Div(id='loading-state', children=[
        html.P("🔄 Cargando datos...", style={'textAlign': 'center', 'color': '#666'})
    ]),
    
    # Contenido principal (oculto inicialmente)
    html.Div(id='main-content', style={'display': 'none'}, children=[
        # Filtro
        html.Div([
            html.H3('Filtro', style={'marginTop': 20, 'marginBottom': 10}),
            dcc.Dropdown(
                id='filtro-regimen',
                options=[{'label': regimen, 'value': regimen} for regimen in regimenes],
                value=regimenes[0],
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
        
        # Mapa y boxplot
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
    ])
], style={'padding': '20px'})

# Callback para mostrar contenido cuando los datos estén listos
@app.callback(
    Output('main-content', 'style'),
    Output('loading-state', 'style'),
    Input('main-content', 'id')
)
def show_content(_):
    if data_loaded:
        return {'display': 'block'}, {'display': 'none'}
    else:
        return {'display': 'none'}, {'display': 'block'}

# Callback para actualizar componentes
@app.callback(
    [Output('mapa-colombia', 'figure'),
     Output('boxplot-kpi', 'figure'),
     Output('kpi-cards', 'children'),
     Output('narrativa-texto', 'children')],
    [Input('filtro-regimen', 'value')]
)
def update_dashboard(regimen_seleccionado):
    # Verificar si los datos están cargados
    if not data_loaded or merged_data is None or df is None:
        error_fig = go.Figure()
        error_fig.add_annotation(text="🔄 Los datos aún se están cargando...", showarrow=False)
        error_message = "Los datos se están cargando. Por favor espera unos segundos."
        
        error_card = html.Div([
            html.H4("⏳"),
            html.P("Cargando datos...")
        ], style={
            'padding': '15px', 
            'backgroundColor': '#fff3cd', 
            'borderRadius': '5px',
            'textAlign': 'center',
            'width': '100%'
        })
        
        return error_fig, error_fig, error_card, error_message
    
    # Crear mapa
    try:
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
    except Exception as e:
        fig_mapa = go.Figure()
        fig_mapa.add_annotation(text=f"Error creando mapa: {str(e)}", showarrow=False)
    
    # Crear boxplot
    try:
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
    except Exception as e:
        fig_box = go.Figure()
        fig_box.add_annotation(text=f"Error creando boxplot: {str(e)}", showarrow=False)
    
    # Calcular KPIs
    try:
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
    except Exception as e:
        kpi_cards = html.Div(f"Error calculando KPIs: {str(e)}")
    
    # Narrativa
    try:
        if regimen_seleccionado == 'Contributivo':
            narrativa = f"El régimen Contributivo presenta un total de {total_afiliados:,.0f} afiliados, distribuidos en {departamentos_con_afiliados} departamentos. El promedio de afiliados por departamento es de {promedio_por_depto:,.0f} personas. Este régimen, financiado por aportes de trabajadores y empleadores, muestra su mayor concentración en {depto_max} con {max_afiliados:,.0f} afiliados."
        elif regimen_seleccionado == 'Subsidiado':
            narrativa = f"El régimen Subsidiado cuenta con {total_afiliados:,.0f} afiliados en total, cubriendo {departamentos_con_afiliados} departamentos. El promedio por departamento es de {promedio_por_depto:,.0f} personas. Este régimen, dirigido a población vulnerable con subsidio estatal, tiene su mayor presencia en {depto_max} con {max_afiliados:,.0f} afiliados."
        else:  # Especial
            narrativa = f"El régimen Especial registra {total_afiliados:,.0f} afiliados en total, presentes en {departamentos_con_afiliados} departamentos. El promedio por departamento es de {promedio_por_depto:,.0f} personas. Este régimen, diseñado para grupos específicos como fuerzas armadas y docentes, concentra su mayor número en {depto_max} con {max_afiliados:,.0f} afiliados."
    except:
        narrativa = "No se pudo generar la narrativa para el régimen seleccionado."
    
    return fig_mapa, fig_box, kpi_cards, narrativa

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)










