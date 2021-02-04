from jupyter_dash import JupyterDash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def run_dash(csv_dir,json_dir):
    
    ### Preload
    df = pd.read_csv(csv_dir, index_col=0)
    df.rename(columns={"Unit Process Name": "Unit_Process", "Case Study": "Case_Study"}, inplace=True)

    all_case = df['Case_Study'].unique()

    metric_dict = {'COST':'Cost', 'ACOST':'Annual Cost', 'ELEC':'Electricity', 'WATER':'Water Flow', 'LCOW':'LCOW'}
    unit_dict = {'COST':'$MM', 'ACOST':'$MM/yr', 'ELEC':'kWh/m3', 'WATER':'m3/s', 'LCOW':'$/m3'}

    ######################## START APP #########################

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = JupyterDash(__name__, external_stylesheets=external_stylesheets)


    ######################## START LAYOUT #########################

    app.layout = html.Div([

        ######## ALL ABOUT SELECT ########
        html.Div([
            
            # Title
            html.Div([
                html.H4(children='Results Analysis for WaterTAP3'),
            ], style={'padding': '10px 0px 0px 10px'}),

            # Case I & Scena I
            html.Div([
                html.Div([
                    html.Label('Select study case:'),
                    dcc.Dropdown(
                        id='crossfilter-case1', 
                        options=[{'label': i, 'value': i} for i in all_case], 
                        placeholder="Case Study 1"),
                ], style={
                    'width': '49%', 
                    'display': 'inline-block',
                    'padding': '0px 15px 0px 0px'}),

                html.Div([    
                    html.Label('Avaliable scenarios:'),
                    dcc.Dropdown(id='crossfilter-scenario1', placeholder="Scenario 1"),
                ], style={
                    'width': '49%', 
                    'display': 'inline-block'}),
            ], style={'padding': '5px 10px'}),
            
            # Case II & Scena II
            html.Div([
                html.Div([
                    html.Label('Select study case:'),
                    dcc.Dropdown(
                        id='crossfilter-case2', 
                        options=[{'label': i, 'value': i} for i in all_case],
                        placeholder="Case Study 2"),
                ], style={
                    'width': '49%', 
                    'display': 'inline-block',
                    'padding': '0px 15px 0px 0px'}),

                html.Div([    
                    html.Label('Avaliable scenarios:'),
                    dcc.Dropdown(id='crossfilter-scenario2', placeholder="Scenario 2"),
                ], style={
                    'width': '49%', 
                    'display': 'inline-block'}),
            ], style={'padding': '5px 10px'}),

            # Metric
            html.Div([
                html.Label('Output metrics:', style={'display': 'inline-block','padding':'0px 5px 0px 0px'}),
                html.Label('(choose up to two metrics to compare in the same chart)', style={'color':'#1E90FF','display': 'inline-block'}),
                dcc.Checklist(
                    id='crossfilter-metric-type',
                    options=[ 
                        {'label': 'Cost', 'value': 'COST'},   # TODO: limit 2
                        {'label': 'Annual Cost', 'value': 'ACOST'},
                        {'label': 'Electricity', 'value': 'ELEC'},
                        {'label': 'Water Flow', 'value': 'WATER'},
                        {'label': 'LCOW', 'value': 'LCOW'},
                    ],
                    labelStyle={'display': 'inline-flex'},
                ),        
            ], style={'padding': '5px 10px'}),        

            # Unit Process    
            html.Div([
                html.Label('Avaliable unit processes:'),
                dcc.Dropdown(
                    id='crossfilter-unit-process',
                    multi=True
                ),
            ], style={'padding': '5px 10px'}), 
            
            # Variable
            html.Div([            
                html.Label('Avaliable variables:'),
                dcc.Dropdown(
                    id='crossfilter-variable',
                    multi=True,
                ),
            ], style={'padding': '5px 10px'}), 

        ], style={
            'width': '70%',
            'borderBottom': 'thin lightgrey solid',
            'backgroundColor': 'rgb(250, 250, 250)',
            'padding': '0px 10px 15px 10px'}),

        ######## ALL ABOUT SWITCH BUTTON ########
        html.Div([

            # SWITCH STACK
            html.Div([ 
                daq.BooleanSwitch(
                    id="boolean-switch-stack",
                    on=False,
                    label="Switch to stack unit process",
                    labelPosition="left"),
            ], style={
                'display': 'inline-block',
                'padding': '15px 10px'}), 

            # SWITCH PCT - TODO: NOT USED
            html.Div([
                daq.BooleanSwitch(
                    id="boolean-switch-percentage",
                    on=False,
                    disabled=True,
                    label="Switch to percentage",
                    labelPosition="left"),
            ], style={ 
                'display': 'inline-block',
                'padding': '15px 10px'}), 

        ], style={
            'width': '64%',
            'float': 'right',
            'position': 'relative'}),
        
        ######## ALL ABOUT PLOT ########
        html.Div([
            dcc.Graph(id='figure-bar'),
            dcc.Graph(id='figure-bar2'),
            dcc.Graph(id='figure-bar3')

        ], style={
            'width': '70%', 
            'padding': '50px 10px',
            'zIndex':'-1',
            'position': 'relative',}),

    ], style={
        'margin-top': '20px', 
        'margin-left': '50px'})

    ######################## END OF LAYOUT #########################

    ######################## START FUNCTION #########################

    ### Scena I Options
    @app.callback(
        Output('crossfilter-scenario1', 'options'),
        Input('crossfilter-case1', 'value'))
    def set_scenario1_options(selected_case):
        ddf = df[(df['Case_Study']==selected_case)]

        return [{'label': i, 'value': i} for i in ddf['Scenario'].unique()]


    ### Scena II Options
    @app.callback(
        Output('crossfilter-scenario2', 'options'),
        Input('crossfilter-case2', 'value'))
    def set_scenario2_options(selected_case):
        ddf = df[(df['Case_Study']==selected_case)]

        return [{'label': i, 'value': i} for i in ddf['Scenario'].unique()]


    ### Available Unit Process
    @app.callback(
        Output('crossfilter-unit-process', 'options'),
        [Input('crossfilter-metric-type', 'value'),
        Input('crossfilter-scenario1', 'value'),
        Input('crossfilter-case1', 'value'),]) # Order: all Outputs first, then Inputs, then States
    def set_unit_process_options(selected_metric_type, selected_scenario, selected_case):
        
        ddf2 = df[(df['Case_Study']==selected_case)&(df['Scenario']==selected_scenario)]
        ddf2_new = pd.DataFrame()

        # TODO: share ddf2_new between callbacks with a hidden Div
        # https://dash.plotly.com/sharing-data-between-callbacks

        if selected_metric_type is None:
            ddf2_new = ddf2.copy()
        else: 
            if 'COST' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='Cost']])
            if 'WATER' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='Water Flow']])
            if 'ELEC' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='Electricity']]) 
            if 'ACOST' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='Annual Cost']])
            if 'LCOW' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='LCOW']])               


        return [{'label': i, 'value': i} for i in ddf2_new['Unit_Process'].unique()]


    ### Available Variables
    @app.callback(
        Output('crossfilter-variable', 'options'),
        [Input('crossfilter-metric-type', 'value'),
        Input('crossfilter-scenario1', 'value'),
        Input('crossfilter-case1', 'value'),])
    def set_variable_options(selected_metric_type, selected_scenario, selected_case):
        ddf2 = df[(df['Case_Study']==selected_case)&(df['Scenario']==selected_scenario)]
        ddf2_new = pd.DataFrame()

        if selected_metric_type is None:
            ddf2_new = ddf2.copy()
        else:
            if 'COST' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='Cost']])
            if 'WATER' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='Water Flow']])
            if 'ELEC' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='Electricity']]) 
            if 'ACOST' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='Annual Cost']])
            if 'LCOW' in selected_metric_type:
                ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']=='LCOW']]) 

        return [{'label': i, 'value': i} for i in ddf2_new['Variable'].unique()]


    ### Barplot I
    @app.callback(
        Output('figure-bar', 'figure'),
        [Input('boolean-switch-stack', 'on'),
        Input('boolean-switch-percentage', 'on'), # TODO NOT USED
        Input('crossfilter-variable', 'value'),     
        Input('crossfilter-unit-process', 'value'),
        Input('crossfilter-scenario1', 'value'),
        Input('crossfilter-case1', 'value'),
        Input('crossfilter-metric-type', 'value')])
    def update_graph(stack_on, percentage_on, selected_variable, selected_unit_process, 
                        selected_scenario, selected_case, selected_metric_type):
        
        # ### Define val or pct
        # if percentage_on == False:
        #     df_new = df[df['Unit']!='%']
        # else:
        #     df_new = df[df['Unit']=='%']
        df_new = df.copy()

        if (selected_unit_process is None) or (selected_variable is None):
            fig = make_subplots()
        
        else:
        ### Select data
            ddf3 = df_new[(df_new['Case_Study']==selected_case)
                        &(df_new['Scenario']==selected_scenario)
                        &(df_new['Unit_Process'].isin(selected_unit_process))
                        &(df_new['Variable'].isin(selected_variable))]
            
            # # Select metric - NO NEED ANY MORE
            # ddf3_cost = ddf3[ddf3['Metric']=='Cost']
            # ddf3_water = ddf3[ddf3['Metric']=='Water Flow']
            # ddf3_elec = ddf3[ddf3['Metric']=='Electricity']
            # ddf3_chem = ddf3[ddf3['Metric']=='Constituent Flow']
            
            # Define stack objects
            if stack_on == False:
                x_name = 'Unit_Process'; s_name = 'Variable' # default
            else:
                x_name = 'Variable'; s_name = 'Unit_Process'

            if len(selected_metric_type) == 1:
                
                metric_name = metric_dict.get(selected_metric_type[0])
                unit_name = unit_dict.get(selected_metric_type[0])

                ddf4 = ddf3[ddf3['Metric'].isin([metric_name])]

                fig = make_subplots()
                fig = px.bar(ddf4, x=x_name, y='Value', color=s_name)
                fig.update_xaxes(title=x_name)
                fig.update_yaxes(title=unit_name, type='linear')
                fig.update_layout(title_text="%s Result for %s - %s" % (metric_name, selected_case, selected_scenario))
            
            elif len(selected_metric_type) == 2:

                metric_name1 = metric_dict.get(selected_metric_type[0])
                metric_name2 = metric_dict.get(selected_metric_type[1])
                unit_name1 = unit_dict.get(selected_metric_type[0])
                unit_name2 = unit_dict.get(selected_metric_type[1])

                ddf4_1 = ddf3[ddf3['Metric'].isin([metric_name1])]
                ddf4_2 = ddf3[ddf3['Metric'].isin([metric_name2])]

                fig = make_subplots(specs=[[{"secondary_y": True}]])

                for var, group in ddf4_1.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name=var, offset=-0.1))
                
                for var, group in ddf4_2.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name=var, offset=0.1), secondary_y=True)
                
                fig.update_xaxes(title_text=x_name)
                fig.update_yaxes(title_text=unit_name1, secondary_y=False)
                fig.update_yaxes(title_text=unit_name2, secondary_y=True)
                fig.update_layout(barmode='stack', 
                    title_text="Combined %s & %s Results for %s - %s" % (metric_name1, metric_name2, selected_case, selected_scenario))
            
            elif len(selected_metric_type) > 2:
                
                fig = make_subplots() # empty

        fig.update_layout(margin={'l': 40, 'b': 30, 't': 70, 'r': 0}, hovermode='closest')

        return fig


    ### BarPlot II
    @app.callback(
        Output('figure-bar2', 'figure'),
        [Input('boolean-switch-stack', 'on'),
        Input('boolean-switch-percentage', 'on'), # TODO NOT USED
        Input('crossfilter-variable', 'value'),
        Input('crossfilter-unit-process', 'value'),
        Input('crossfilter-scenario2', 'value'),
        Input('crossfilter-case2', 'value'),
        Input('crossfilter-metric-type', 'value')])
    def update_graph2(stack_on, percentage_on, selected_variable, selected_unit_process, 
                        selected_scenario, selected_case, selected_metric_type):
        df_new = df.copy()
        
        if (selected_unit_process is None) or (selected_variable is None):
            fig = make_subplots()
        
        else:
            ### Select data
            ddf3 = df_new[(df_new['Case_Study']==selected_case)
                        &(df_new['Scenario']==selected_scenario)
                        &(df_new['Unit_Process'].isin(selected_unit_process))
                        &(df_new['Variable'].isin(selected_variable))]
            
            # Define stack object
            if stack_on == False:
                x_name = 'Unit_Process'; s_name = 'Variable' # default
            else:
                x_name = 'Variable'; s_name = 'Unit_Process'

            if len(selected_metric_type) == 1:
                
                metric_name = metric_dict.get(selected_metric_type[0])
                unit_name = unit_dict.get(selected_metric_type[0])

                ddf4 = ddf3[ddf3['Metric'].isin([metric_name])]

                fig = make_subplots()
                fig = px.bar(ddf4, x=x_name, y='Value', color=s_name)
                fig.update_xaxes(title=x_name)
                fig.update_yaxes(title=unit_name, type='linear')
                fig.update_layout(title_text="%s Result for %s - %s" % (metric_name, selected_case, selected_scenario))
            
            elif len(selected_metric_type) == 2:

                metric_name1 = metric_dict.get(selected_metric_type[0])
                metric_name2 = metric_dict.get(selected_metric_type[1])
                unit_name1 = unit_dict.get(selected_metric_type[0])
                unit_name2 = unit_dict.get(selected_metric_type[1])

                ddf4_1 = ddf3[ddf3['Metric'].isin([metric_name1])]
                ddf4_2 = ddf3[ddf3['Metric'].isin([metric_name2])]

                fig = make_subplots(specs=[[{"secondary_y": True}]])

                for var, group in ddf4_1.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name=var, offset=-0.1))
                
                for var, group in ddf4_2.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name=var, offset=0.1), secondary_y=True)
                
                fig.update_xaxes(title_text=x_name)
                fig.update_yaxes(title_text=unit_name1, secondary_y=False)
                fig.update_yaxes(title_text=unit_name2, secondary_y=True)
                fig.update_layout(barmode='stack', 
                    title_text="Combined %s & %s Results for %s - %s" % (metric_name1, metric_name2, selected_case, selected_scenario))
            
            elif len(selected_metric_type) > 2:
                
                fig = make_subplots() # empty

        fig.update_layout(margin={'l': 40, 'b': 30, 't': 50, 'r': 0}, hovermode='closest')

        return fig


    ### BarPlot III - diff
    @app.callback(
        Output('figure-bar3', 'figure'),
        [Input('boolean-switch-stack', 'on'),
        Input('boolean-switch-percentage', 'on'), # TODO NOT USED
        Input('crossfilter-variable', 'value'),
        Input('crossfilter-unit-process', 'value'),
        Input('crossfilter-scenario1', 'value'),
        Input('crossfilter-case1', 'value'),
        Input('crossfilter-scenario2', 'value'),
        Input('crossfilter-case2', 'value'),
        Input('crossfilter-metric-type', 'value')])
    def update_graph3(stack_on, percentage_on, selected_variable, selected_unit_process, 
                        selected_scenario1, selected_case1, selected_scenario2, selected_case2, selected_metric_type):
        df_new = df.copy()
        
        if (selected_unit_process is None) or (selected_variable is None):
            fig = make_subplots()
        
        else:
            ### Select data
            ddf3_a = df_new[(df_new['Case_Study']==selected_case1)
                        &(df_new['Scenario']==selected_scenario1)
                        &(df_new['Unit_Process'].isin(selected_unit_process))
                        &(df_new['Variable'].isin(selected_variable))]

            ddf3_b = df_new[(df_new['Case_Study']==selected_case2)
                        &(df_new['Scenario']==selected_scenario2)
                        &(df_new['Unit_Process'].isin(selected_unit_process))
                        &(df_new['Variable'].isin(selected_variable))]
            
            ddf3 = ddf3_a.copy()
            ddf3['Value'] = ddf3_a['Value'] - ddf3_b['Value'] # calculate diff
            
            # Define stack object
            if stack_on == False:
                x_name = 'Unit_Process'; s_name = 'Variable' # default
            else:
                x_name = 'Variable'; s_name = 'Unit_Process'

            if len(selected_metric_type) == 1:
                
                metric_name = metric_dict.get(selected_metric_type[0])
                unit_name = unit_dict.get(selected_metric_type[0])

                ddf4 = ddf3[ddf3['Metric'].isin([metric_name])]

                fig = make_subplots()
                fig = px.bar(ddf4, x=x_name, y='Value', color=s_name)
                fig.update_xaxes(title=x_name)
                fig.update_yaxes(title=unit_name, type='linear')
                fig.update_layout(title_text="%s Result Difference" % (metric_name))
            
            elif len(selected_metric_type) == 2:

                metric_name1 = metric_dict.get(selected_metric_type[0])
                metric_name2 = metric_dict.get(selected_metric_type[1])
                unit_name1 = unit_dict.get(selected_metric_type[0])
                unit_name2 = unit_dict.get(selected_metric_type[1])

                ddf4_1 = ddf3[ddf3['Metric'].isin([metric_name1])]
                ddf4_2 = ddf3[ddf3['Metric'].isin([metric_name2])]

                fig = make_subplots(specs=[[{"secondary_y": True}]])

                for var, group in ddf4_1.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name=var, offset=-0.1))
                
                for var, group in ddf4_2.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name=var, offset=0.1), secondary_y=True)
                
                fig.update_xaxes(title_text=x_name)
                fig.update_yaxes(title_text=unit_name1, secondary_y=False)
                fig.update_yaxes(title_text=unit_name2, secondary_y=True)
                fig.update_layout(barmode='stack', 
                    title_text="Combined %s & %s Difference for two Scenarios" % (metric_name1, metric_name2))
                       
            elif len(selected_metric_type) > 2:
                
                fig = make_subplots() # empty

        fig.update_layout(margin={'l': 40, 'b': 30, 't': 30, 'r': 0}, hovermode='closest')

        return fig


    ######################## END OF FUNCTION #########################


    app.run_server(debug=True)
