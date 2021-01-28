import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

raw = pd.read_csv('./cost_results.csv',index_col=0)
raw.index.names=['unit']
raw = raw.reset_index()
df = pd.melt(raw, id_vars=['unit'], value_vars=raw.columns.to_list()[1:])

all_uni = df['unit'].unique()
all_var = df['variable'].unique()

app.layout = html.Div([
    html.Div([
        html.H2(children='Cost results for WaterTAP3'
        ), 
    ], style={'width': '60%', 'textAlign': 'center'}),

    html.Div([
        html.Label('Select units:'),
        dcc.Dropdown(
            id='crossfilter-xaxis-column',
            options=[{'label': i, 'value': i} for i in all_uni],
            value = ['swoi','tri_media_filtration','cf'],
            multi=True
        ),
    ], style={'width': '60%'}),
    
    html.Div([
        html.Label('Select cost types:'),
        dcc.Dropdown(
            id='crossfilter-yaxis-column',
            options=[{'label': j, 'value': j} for j in all_var],
            value = ['fixed_cap_inv','total_up_cost','total_fixed_op_cost'],
            multi=True
        ),
    ], style={'width': '60%'}),

    html.Div([
        dcc.Graph(
            id='crossfilter-bar',
        )
    ], style={'width': '60%', 'display': 'inline-block', 'padding': '0 50'}),

], style={'margin-top': '20px', 'margin-left': '50px'})

@app.callback(
    dash.dependencies.Output('crossfilter-bar', 'figure'),
    [dash.dependencies.Input('crossfilter-xaxis-column', 'value'),
     dash.dependencies.Input('crossfilter-yaxis-column', 'value')])
def update_graph(xaxis_column_name, yaxis_column_name):
    
    ddf = df[(df['unit'].isin(xaxis_column_name))&(df['variable'].isin(yaxis_column_name))]
    fig = px.bar(ddf, x='unit',y='value',color='variable')

    fig.update_xaxes(title='unit')
    fig.update_yaxes(title='value', type='linear')
    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)