import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
df = pd.read_csv('./results_v3.csv')

all_case = df['Case_Study'].unique()

app.layout = html.Div([

    html.Div([
        html.Div([
            html.H4(children='Results Analysis for WaterTAP3'),
        ], style={'padding': '10px 0px 0px 10px'}),

        html.Div([
            html.Div([
                html.Label('Select study case:'),
                dcc.Dropdown(
                    id='crossfilter-case',
                    options=[{'label': i, 'value': i} for i in all_case],
                    value = 'Carlsbad'),
            ], style={
                'width': '49%', 
                'display': 'inline-block',
                'padding': '0px 15px 0px 0px'}),

            html.Div([    
                html.Label('Avaliable scenarios:'),
                dcc.Dropdown(
                    id='crossfilter-scenario',
                    value = 'S0'),
            ], style={
                'width': '49%', 
                'display': 'inline-block'}),

        ], style={'padding': '5px 10px'}),

        html.Div([
            html.Label('Outputs options:', style={'display': 'inline-block','padding':'0px 5px 0px 0px'}),
            html.Label('(choose up to two metrics to compare in the same chart)', style={'color':'#1E90FF','display': 'inline-block'}),
            dcc.Checklist(
                id='crossfilter-graph-type',
                options=[
                    {'label': 'Cost of Water Breakdown', 'value': 'Cost'},
                    {'label': 'Total Water Intensity', 'value': 'Waterflow'},
                    {'label': 'Energy Intensity', 'value': 'Energy'},
                    {'label': 'Environmental Impacts', 'value': 'Impact'},
                ],
                value=['Cost'],
                labelStyle={'display': 'inline-flex'},
            ),        
        ], style={'padding': '5px 10px'}),        
            
        html.Div([
            html.Label('Avaliable unit processes:'),
            dcc.Dropdown(
                id='crossfilter-unit-process',
                value = ['swoi','tri_media_filtration','cf'],
                multi=True,
            ),
        ], style={'padding': '5px 10px'}), 

        html.Div([            
            html.Label('Avaliable variables:'),
            dcc.Dropdown(
                id='crossfilter-variable',
                value = ['fixed_cap_inv','total_up_cost','inlet_flow'],
                multi=True,
            ),
        ], style={'padding': '5px 10px'}), 

    ], style={
        'width': '70%',
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(250, 250, 250)',
        'padding': '0px 10px 15px 10px'}),

    html.Div([
        html.Div([ 
            daq.BooleanSwitch(
                id="boolean-switch-stack",
                on=False,
                label="Switch stacked objects",
                labelPosition="left"),
        ], style={
            'display': 'inline-block',
            'padding': '15px 10px'}), 

        html.Div([
            daq.BooleanSwitch(
                id="boolean-switch-percentage",
                on=False,
                label="Switch to percentage",
                labelPosition="left"),
        ], style={ 
            'display': 'inline-block',
            'padding': '15px 10px'}), 

    ], style={
        'width': '62%',
        'float': 'right',
        'position': 'relative'}),
    
    html.Div([
        dcc.Graph(id='figure-bar')
    ], style={
        'width': '70%', 
        'padding': '30px 10px',
        'zIndex':'-1',
        'position': 'relative',}),

], style={
    'margin-top': '20px', 
    'margin-left': '50px'})


@app.callback(
    Output('crossfilter-scenario', 'options'),
    [Input('crossfilter-case', 'value')])
def set_scenario_options(selected_case):
    ddf = df[(df['Case_Study']==selected_case)]
    return [{'label': i, 'value': i} for i in ddf['Scenario'].unique()]

@app.callback(
    Output('crossfilter-unit-process', 'options'),
    [Input('crossfilter-scenario', 'value'),
     Input('crossfilter-case', 'value'),
     Input('crossfilter-graph-type', 'value')])
def set_unit_process_options(selected_scenario, selected_case, selected_graph_type):
    
    ddf2 = df[(df['Case_Study']==selected_case)&(df['Scenario']==selected_scenario)]

    if selected_graph_type == ['Cost']:
        ddf2_new = ddf2[ddf2['Unit']=='$MM']
    elif selected_graph_type == ['Waterflow']:
        ddf2_new = ddf2[ddf2['Unit']=='m3/s']
    else: 
        ddf2_new = ddf2.copy()

    return [{'label': i, 'value': i} for i in ddf2_new['Unit_Process'].unique()]

@app.callback(
    Output('crossfilter-variable', 'options'),
    [Input('crossfilter-scenario', 'value'),
     Input('crossfilter-case', 'value'),
     Input('crossfilter-graph-type', 'value')])
def set_variable_options(selected_scenario, selected_case, selected_graph_type):
    ddf2 = df[(df['Case_Study']==selected_case)&(df['Scenario']==selected_scenario)]

    if selected_graph_type == ['Cost']:
        ddf2_new = ddf2[ddf2['Unit']=='$MM']
    elif selected_graph_type == ['Waterflow']:
        ddf2_new = ddf2[ddf2['Unit']=='m3/s']
    else: 
        ddf2_new = ddf2.copy()

    return [{'label': i, 'value': i} for i in ddf2_new['Variable'].unique()]

@app.callback(
    Output('figure-bar', 'figure'),
    [Input('boolean-switch-stack', 'on'),
     Input('boolean-switch-percentage', 'on'),
     Input('crossfilter-unit-process', 'value'),
     Input('crossfilter-variable', 'value'),
     Input('crossfilter-scenario', 'value'),
     Input('crossfilter-case', 'value'),
     Input('crossfilter-graph-type', 'value')])
def update_graph(stack_on, percentage_on, selected_unit_process, selected_variable,
                    selected_scenario, selected_case, selected_graph_type):
    
    # ===== TODO: this is really stupid, will modify later =====
    
    # define val or pct
    if percentage_on == False:
        df_new = df[df['Unit']!='%']
    else:
        df_new = df[df['Unit']=='%']
    
    # select data
    ddf3 = df_new[(df_new['Case_Study']==selected_case)
                &(df_new['Scenario']==selected_scenario)
                &(df_new['Unit_Process'].isin(selected_unit_process))
                &(df_new['Variable'].isin(selected_variable))]
    
    # select type
    ddf3_c = ddf3[ddf3['Option']=='cost']
    ddf3_w = ddf3[ddf3['Option']=='water']
    
    # define stack objects
    if stack_on == True: #stack on var
        ddf4_c = ddf3_c[ddf3_c['Stack']=='var']
        ddf4_w = ddf3_w[ddf3_w['Stack']=='var']
        x_name = 'Unit_Process'; s_name = 'Variable'
    else: # default: stack on up
        ddf4_c = ddf3_c[ddf3_c['Stack']=='up']
        ddf4_w = ddf3_w[ddf3_w['Stack']=='up']
        x_name = 'Variable'; s_name = 'Unit_Process'

    if selected_graph_type == ['Cost']:

        fig = make_subplots()
        fig = px.bar(ddf4_c, x=x_name, y='Value', color=s_name)
        fig.update_xaxes(title=x_name)
        fig.update_yaxes(title='Cost (%s)'%(ddf4_c['Unit'].values[0]), type='linear')
        fig.update_layout(title_text="Cost of Water Breakdown")

    elif selected_graph_type == ['Waterflow']:
        
        fig = make_subplots()
        fig = px.bar(ddf4_w, x=x_name, y='Value', color=s_name)
        fig.update_xaxes(title=x_name)
        fig.update_yaxes(title='WaterFlow (%s)'%(ddf4_w['Unit'].values[0]), type='linear')
        fig.update_layout(title_text="Total Water Intensity")
    
    else:

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        for var, group in ddf4_c.groupby(s_name):
            fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.4, name=var, offset=-0.2))
        
        for var, group in ddf4_w.groupby(s_name):
            fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.4, name=var, offset=0.2),secondary_y=True,)
        
        fig.update_xaxes(title_text=x_name)
        fig.update_yaxes(title_text='Cost (%s)'%(ddf4_c['Unit'].values[0]), secondary_y=False)
        fig.update_yaxes(title_text='WaterFlow (%s)'%(ddf4_w['Unit'].values[0]), secondary_y=True)
        fig.update_layout(barmode='stack', title_text="Combined Results")

    fig.update_layout(margin={'l': 40, 'b': 30, 't': 30, 'r': 0}, hovermode='closest')

    return fig


if __name__ == '__main__':
    app.run_server(debug=True,port=8051)