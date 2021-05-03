import json

from jupyter_dash import JupyterDash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

__all__ = ['run_dash']

def run_dash(csv_dir,json_dir):

    ### Preload
    df = pd.read_csv(csv_dir, index_col=0)
    df.rename(columns={"Unit Process Name": "Unit_Process", "Case Study": "Case_Study"}, inplace=True)

    all_case = df['Case_Study'].unique()
    all_metric = df['Metric'].unique()
    unit_list = list((df['Metric'] +'_'+ df['Unit']).unique())
    unit_dict = {i.split('_')[0]:i.split('_')[1] for i in unit_list}

    filename = json_dir

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

    app = JupyterDash(__name__, external_stylesheets=external_stylesheets)

    ######################## START FUNCTION #########################

    ### function for bar plot
    def plot_graph(stack_on, percentage_on, selected_variable, selected_unit_process, 
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
            
            ### Define stack objects
            if stack_on == False:
                x_name = 'Unit_Process'; s_name = 'Variable' # default
            else:
                x_name = 'Variable'; s_name = 'Unit_Process'

            if len(selected_metric_type) == 1: 
                metric_name = selected_metric_type[0]
                unit_name = unit_dict.get(selected_metric_type[0])
                ddf4 = ddf3[ddf3['Metric'].isin([metric_name])]

                fig = px.bar(ddf4, x=x_name, y='Value', color=s_name)
                fig.update_xaxes(title=x_name)
                fig.update_yaxes(title='%s (%s)' % (metric_name, unit_name), type='linear')
                fig.update_layout(title_y=0.97, title_text="%s - %s - %s" % (metric_name, selected_case, selected_scenario))
            
            elif len(selected_metric_type) == 2:
                metric_name1 = selected_metric_type[0]
                metric_name2 = selected_metric_type[1]
                unit_name1 = unit_dict.get(selected_metric_type[0])
                unit_name2 = unit_dict.get(selected_metric_type[1])
                ddf4_1 = ddf3[ddf3['Metric'].isin([metric_name1])]
                ddf4_2 = ddf3[ddf3['Metric'].isin([metric_name2])]

                fig = make_subplots(specs=[[{"secondary_y": True}]])
                for var, group in ddf4_1.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name='%s - %s'%(metric_name1,var), offset=-0.2))
                for var, group in ddf4_2.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name='%s - %s'%(metric_name2,var), offset=0), secondary_y=True)
                fig.update_xaxes(title_text=x_name)
                fig.update_yaxes(title_text='%s (%s)' % (metric_name1, unit_name1), secondary_y=False)
                fig.update_yaxes(title_text='%s (%s)' % (metric_name2, unit_name2), secondary_y=True)
                fig.update_layout(barmode='stack', title_y=0.97,
                    title_text="%s & %s - %s - %s" % (metric_name1, metric_name2, selected_case, selected_scenario))
            
            elif len(selected_metric_type) > 2:

                fig = make_subplots() # empty

        fig.update_layout(margin={'l': 40, 'b': 30, 't': 40, 'r': 0}, hovermode='closest')

        return fig

    ### function for network
    def draw_network(filename=filename):

        with open(filename) as f:
            js_graph = json.load(f)

        # transform dict
        node = js_graph['nodes']
        link = js_graph['links']
        for n in node:
            n['label']= n['id']
        new_node = [{'data': i} for i in node]
        new_link = [{'data':i} for i in link]

        # get node order
        node_list = []
        for n in link:
            a = n['source']
            b = n['target']
            if a not in node_list:
                node_list.append(a)
            elif b not in node_list:
                node_list.append(b)
            else:
                pass

        # calculate pos - better solution: dfs algorithm
        x = 0; y = 0; c1 = 1
        pos = []
        for n in node_list: 
            if ('mixer' in n) or ('spliter' in n): # mix or seperate
                x = x + c1*200 
                pos.append([n,x,y])
                x = x - c1*200
                c1 = c1 * (-1)
            elif ('discharge' in n) or ('landfill' in n) or ('drinking' in n): # end use
                x = x + 200
                pos.append([n,x,y])
                x = x - 200
            else:
                y = y + 150
                pos.append([n,x,y])

        # put pos into dict
        df = pd.DataFrame(pos,columns=['node','x','y'])
        for i in range(len(df)):
            name = new_node[i]['data']['label']
            row = df[df['node']==name]
            x = row['x'].values[0]
            y = row['y'].values[0]
            new_node[i]['position'] = {'x': y,'y': x} # NOTE - change to horizontal

        both = new_node + new_link

        return both

    ######################## END OF FUNCTION #########################

    ######################## START LAYOUT #########################

    app.layout = html.Div([

        ######## ALL ABOUT SELECT ########
        html.Div([
            
            # Title
            html.Div([
                html.H4(children='WaterTAP3 Result'),
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
                    options=[ {'label': i, 'value': i} for i in all_metric],
                    labelStyle={'display': 'inline-flex'},
                ),        
            ], style={'padding': '5px 10px'}),        

            # Unit Process    
            html.Div([
                html.Label('Avaliable unit processes:'),
                dcc.Dropdown(
                    id='crossfilter-unit-process',
                    multi=True,              
                ),
            ], style={'width': '97.5%','padding': '5px 10px'}), 
            
            # Variable
            html.Div([            
                html.Label('Avaliable variables:'),
                dcc.Dropdown(
                    id='crossfilter-variable',
                    multi=True,
                ),
            ], style={'width': '97.5%','padding': '5px 10px'}), 

        ], style={
            'width': '90%',
            'borderBottom': 'thin lightgrey solid',
            'backgroundColor': 'rgb(250, 250, 250)',
            'padding': '0px 10px 15px 10px'}),
        
        ######## ALL ABOUT PLOT ########
        dcc.Tabs([
            
            # Case I & Scena I - 1
            dcc.Tab(
                label='Case Study - Scenario 1', 
                children=[
                    html.Div([
                        # SWITCH STACK
                        html.Div([ 
                            daq.BooleanSwitch(
                                id="boolean-switch-stack",
                                on=False,
                                label="Switch to stack unit process",
                                labelPosition="left"),
                            ], style={'display': 'inline-block',}
                        ), 
                        # SWITCH PCT - TODO: NOT USED
                        html.Div([
                            daq.BooleanSwitch(
                                id="boolean-switch-percentage",
                                on=False,
                                disabled=True,
                                label="Switch to percentage",
                                labelPosition="left"),
                            ], style={'display': 'inline-block',}
                        ), 
                    ], style={'width': '90%', 'padding': '15px 10px 0px 750px'}),
                    dcc.Graph(id='figure-bar',style={'width': '90%'}),
                    cyto.Cytoscape(
                        id='cytoscape-case1',
                        layout={'name': 'preset'},
                        style={'height': '350px'},
                        stylesheet=[
                            {'selector': 'edge','style': {
                                'curve-style': 'bezier',
                                'arrow-scale': 2,
                                'target-arrow-shape': 'triangle'}},
                            {'selector': 'node','style': {
                                'label': 'data(id)',
                                'background-color': '#1E90FF'}},]
                    ),
                ]),

            # Case II & Scena II - 2
            dcc.Tab(
                label='Case Study - Scenario 2', 
                children=[
                    html.Div([
                        # SWITCH STACK
                        html.Div([ 
                            daq.BooleanSwitch(
                                id="boolean-switch-stack2",
                                on=False,
                                label="Switch to stack unit process",
                                labelPosition="left"),
                            ], style={'display': 'inline-block',}
                        ), 
                        # SWITCH PCT - TODO: NOT USED
                        html.Div([
                            daq.BooleanSwitch(
                                id="boolean-switch-percentage2",
                                on=False,
                                disabled=True,
                                label="Switch to percentage",
                                labelPosition="left"),
                            ], style={'display': 'inline-block',}
                        ), 
                    ], style={'width': '90%', 'padding': '15px 10px 0px 750px'}),
                    dcc.Graph(id='figure-bar2',style={'width': '90%'}),
                    cyto.Cytoscape(
                        id='cytoscape-case2',
                        layout={'name': 'preset'},
                        style={'height': '350px'},
                        stylesheet=[
                            {'selector': 'edge','style': {
                                'curve-style': 'bezier',
                                'arrow-scale': 2,
                                'target-arrow-shape': 'triangle'}},
                            {'selector': 'node','style': {
                                'label': 'data(id)',
                                'background-color': '#1E90FF'}},]
                    ),                    
                ]),   

            # Compare - all param use 4 !!!    
            dcc.Tab(
                label='Compare', 
                children=[
                    html.Div([
                        # SWITCH STACK
                        html.Div([ 
                            daq.BooleanSwitch(
                                id="boolean-switch-stack4",
                                on=False,
                                label="Switch to stack unit process",
                                labelPosition="left"),
                            ], style={'display': 'inline-block',}
                        ), 
                        # SWITCH PCT - TODO: NOT USED
                        html.Div([
                            daq.BooleanSwitch(
                                id="boolean-switch-percentage4",
                                on=False,
                                disabled=True,
                                label="Switch to percentage",
                                labelPosition="left"),
                            ], style={'display': 'inline-block',}
                        ), 
                    ], style={'width': '90%', 'padding': '15px 10px 0px 750px'}),
                    dcc.Graph(id='figure-bar4',style={'width': '90%'}),
                ]),         
            
            # Difference - 3
            dcc.Tab(
                label='Difference', 
                children=[
                    html.Div([
                        # SWITCH STACK
                        html.Div([ 
                            daq.BooleanSwitch(
                                id="boolean-switch-stack3",
                                on=False,
                                label="Switch to stack unit process",
                                labelPosition="left"),
                            ], style={'display': 'inline-block',}
                        ), 
                        # SWITCH PCT - TODO: NOT USED
                        html.Div([
                            daq.BooleanSwitch(
                                id="boolean-switch-percentage3",
                                on=False,
                                disabled=True,
                                label="Switch to percentage",
                                labelPosition="left"),
                            ], style={'display': 'inline-block',}
                        ), 
                    ], style={'width': '90%', 'padding': '15px 10px 0px 750px'}),
                    dcc.Graph(id='figure-bar3',style={'width': '90%'}),
                ]),

        ], style={'width': '90%', 'padding': '0px 10px 15px 10px'}),

    ], style={
        'margin-top': '20px', 
        'margin-left': '50px'})

    ######################## END OF LAYOUT #########################

    ######################## START CALLBACK #########################

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
        Input('crossfilter-case1', 'value'),
        Input('crossfilter-scenario2', 'value'),
        Input('crossfilter-case2', 'value'),])
    def set_unit_process_options(selected_metric_type, selected_scenario1, selected_case1, 
                                            selected_scenario2, selected_case2):
        if selected_metric_type is None:
            ddf2_new = pd.DataFrame(columns={'Unit_Process'})
        
        else:
            selected_case = [selected_case1, selected_case2]
            selected_scenario = [selected_scenario1, selected_scenario2]
            
            ddf2 = df[(df['Case_Study'].isin(selected_case))&(df['Scenario'].isin(selected_scenario))]
            ddf2_new = pd.DataFrame()

            if selected_metric_type is None:
                ddf2_new = ddf2.copy()
            else:
                for i in list(all_metric):
                    if i in selected_metric_type:
                        ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']==i]])

        return [{'label': i, 'value': i} for i in ddf2_new['Unit_Process'].unique()]


    ### Available Variables
    @app.callback(
        Output('crossfilter-variable', 'options'),
        [Input('crossfilter-metric-type', 'value'),
        Input('crossfilter-unit-process', 'value'),
        Input('crossfilter-scenario1', 'value'),
        Input('crossfilter-case1', 'value'),
        Input('crossfilter-scenario2', 'value'),
        Input('crossfilter-case2', 'value'),])
    def set_variable_options(selected_metric_type, selected_unit_process,
                                    selected_scenario1, selected_case1, selected_scenario2, selected_case2):
        if selected_metric_type is None:
            ddf3 = pd.DataFrame(columns={'Variable'})
        
        else:
            selected_case = [selected_case1, selected_case2]
            selected_scenario = [selected_scenario1, selected_scenario2]
            
            ddf2 = df[(df['Case_Study'].isin(selected_case))&(df['Scenario'].isin(selected_scenario))]
            ddf2_new = pd.DataFrame()

            if (selected_metric_type is None) or (selected_unit_process is None):
                ddf3 = ddf2.copy()
            else:
                for i in list(all_metric):
                    if i in selected_metric_type:
                        ddf2_new = pd.concat([ddf2_new, ddf2[ddf2['Metric']==i]])
            
                ddf3 = ddf2_new[ddf2_new['Unit_Process'].isin(selected_unit_process)]

        return [{'label': i, 'value': i} for i in ddf3['Variable'].unique()]


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
        return plot_graph(stack_on, percentage_on, selected_variable, selected_unit_process, 
                        selected_scenario, selected_case, selected_metric_type)


    ### BarPlot II
    @app.callback(
        Output('figure-bar2', 'figure'),
        [Input('boolean-switch-stack2', 'on'),
        Input('boolean-switch-percentage2', 'on'), # TODO NOT USED
        Input('crossfilter-variable', 'value'),
        Input('crossfilter-unit-process', 'value'),
        Input('crossfilter-scenario2', 'value'),
        Input('crossfilter-case2', 'value'),
        Input('crossfilter-metric-type', 'value')])
    def update_graph2(stack_on, percentage_on, selected_variable, selected_unit_process, 
                                selected_scenario, selected_case, selected_metric_type):
        return plot_graph(stack_on, percentage_on, selected_variable, selected_unit_process, 
                        selected_scenario, selected_case, selected_metric_type)


    ### Network I
    @app.callback(
        Output('cytoscape-case1', 'elements'),
        Input('crossfilter-scenario1', 'value'),
        Input('crossfilter-case1', 'value'))
    def update_network1(selected_scenario, selected_case1):
        return draw_network(filename)


    ### Network II
    @app.callback(
        Output('cytoscape-case2', 'elements'),
        Input('crossfilter-scenario2', 'value'),
        Input('crossfilter-case2', 'value'))
    def update_network2(selected_scenario, selected_case1):
        return draw_network(filename)


    ### BarPlot III - diff
    @app.callback(
        Output('figure-bar3', 'figure'),
        [Input('boolean-switch-stack3', 'on'),
        Input('boolean-switch-percentage3', 'on'), # TODO NOT USED
        Input('crossfilter-variable', 'value'),
        Input('crossfilter-unit-process', 'value'),
        Input('crossfilter-scenario1', 'value'),
        Input('crossfilter-case1', 'value'),
        Input('crossfilter-scenario2', 'value'),
        Input('crossfilter-case2', 'value'),
        Input('crossfilter-metric-type', 'value')])
    def update_graph3(stack_on, percentage_on, selected_variable, selected_unit_process, 
                        selected_scenario1, selected_case1, selected_scenario2, selected_case2, selected_metric_type):
        
        if None in [selected_variable, selected_unit_process, selected_scenario1, 
                    selected_case1, selected_scenario2, selected_case2, selected_metric_type]:                
            fig = make_subplots()
        
        elif (selected_scenario1 == selected_scenario2) & (selected_case1 == selected_case2):
            fig = make_subplots()

        else:
            ### Select data
            df_a = df[(df['Case_Study']==selected_case1)
                        &(df['Scenario']==selected_scenario1)
                        &(df['Unit_Process'].isin(selected_unit_process))
                        &(df['Variable'].isin(selected_variable))]
            df_b = df[(df['Case_Study']==selected_case2)
                        &(df['Scenario']==selected_scenario2)
                        &(df['Unit_Process'].isin(selected_unit_process))
                        &(df['Variable'].isin(selected_variable))]
            df_both = pd.concat([df_a, df_b])        
            
            ### Calculate diff
            pivot = pd.pivot_table(df_both, values='Value', 
                                    index=['Unit_Process','Variable','Metric'], columns=['Case_Study','Scenario'])
            ddf3_diff = pivot[(selected_case1, selected_scenario1)] - pivot[(selected_case2, selected_scenario2)] 
            ddf3_diff = ddf3_diff.to_frame().reset_index()
            ddf3_diff.rename(columns={0: 'Value'},inplace=True)
        
            ### Define stack object
            if stack_on == False:
                x_name = 'Unit_Process'; s_name = 'Variable' # default
            else:
                x_name = 'Variable'; s_name = 'Unit_Process'

            if len(selected_metric_type) == 1:
                metric_name = selected_metric_type[0]
                unit_name = unit_dict.get(selected_metric_type[0])
                diff = ddf3_diff[ddf3_diff['Metric'].isin([metric_name])]

                fig = px.bar(diff, x=x_name, y='Value', color=s_name)
                fig.update_xaxes(title=x_name)
                fig.update_yaxes(title=unit_name, type='linear')
                fig.update_layout(title_y=0.97, title_text="%s Difference" % (metric_name))
            
            elif len(selected_metric_type) == 2:
                metric_name1 = selected_metric_type[0]
                metric_name2 = selected_metric_type[1]
                unit_name1 = unit_dict.get(selected_metric_type[0])
                unit_name2 = unit_dict.get(selected_metric_type[1])
                ddf4_1 = ddf3_diff[ddf3_diff['Metric'].isin([metric_name1])]
                ddf4_2 = ddf3_diff[ddf3_diff['Metric'].isin([metric_name2])]

                fig = make_subplots(specs=[[{"secondary_y": True}]])
                for var, group in ddf4_1.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name='%s - %s'%(metric_name1,var), offset=-0.1))
                for var, group in ddf4_2.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name='%s - %s'%(metric_name2,var), offset=0.1), secondary_y=True)
                
                fig.update_xaxes(title_text=x_name)
                fig.update_yaxes(title_text='%s (%s)' % (metric_name1, unit_name1), secondary_y=False)
                fig.update_yaxes(title_text='%s (%s)' % (metric_name2, unit_name2), secondary_y=True)
                fig.update_layout(barmode='stack', title_y=0.97,
                    title_text="%s & %s Difference" % (metric_name1, metric_name2))
                        
            elif len(selected_metric_type) > 2:
                
                fig = make_subplots() # empty

        fig.update_layout(margin={'l': 40, 'b': 30, 't': 40, 'r': 0}, hovermode='closest')

        return fig


    ### BarPlot IV - compare
    @app.callback(
        Output('figure-bar4', 'figure'),
        [Input('boolean-switch-stack4', 'on'),
        Input('boolean-switch-percentage4', 'on'), # TODO NOT USED
        Input('crossfilter-variable', 'value'),
        Input('crossfilter-unit-process', 'value'),
        Input('crossfilter-scenario1', 'value'),
        Input('crossfilter-case1', 'value'),
        Input('crossfilter-scenario2', 'value'),
        Input('crossfilter-case2', 'value'),
        Input('crossfilter-metric-type', 'value')])
    def update_graph4(stack_on, percentage_on, selected_variable, selected_unit_process, 
                        selected_scenario1, selected_case1, selected_scenario2, selected_case2, selected_metric_type):
        
        if None in [selected_variable, selected_unit_process, selected_scenario1, 
                    selected_case1, selected_scenario2, selected_case2, selected_metric_type]:                
            fig = make_subplots()

        else:
            ### Select data
            df_a = df[(df['Case_Study']==selected_case1)
                        &(df['Scenario']==selected_scenario1)
                        &(df['Unit_Process'].isin(selected_unit_process))
                        &(df['Variable'].isin(selected_variable))]
            df_b = df[(df['Case_Study']==selected_case2)
                        &(df['Scenario']==selected_scenario2)
                        &(df['Unit_Process'].isin(selected_unit_process))
                        &(df['Variable'].isin(selected_variable))]
            df_both = pd.concat([df_a, df_b])      
            
            ### Povit to compare
            df_both['id'] = df_both['Case_Study']+' - '+ df_both['Scenario']
            pivot = pd.pivot_table(df_both, values='Value', 
                                    index=['Unit_Process','Variable','Metric'], columns=['id']).reset_index()

            id1 = selected_case1+' - '+selected_scenario1
            id2 = selected_case2+' - '+selected_scenario2
            df1 = pivot[['Unit_Process','Variable','Metric',id1]]
            df2 = pivot[['Unit_Process','Variable','Metric',id2]]
            df1.rename(columns={id1:'Value'},inplace=True)
            df2.rename(columns={id2:'Value'},inplace=True)

            ### Define stack object
            if stack_on == False:
                x_name = 'Unit_Process'; s_name = 'Variable' # default
            else:
                x_name = 'Variable'; s_name = 'Unit_Process'

            if len(selected_metric_type) == 1:
                metric_name = selected_metric_type[0]
                unit_name = unit_dict.get(selected_metric_type[0])

                df1 = df1[df1['Metric']==metric_name]
                df2 = df2[df2['Metric']==metric_name]

                fig = make_subplots()
                for var, group in df1.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2, name='%s - %s'%(metric_name,var), offset=-0.1))
                
                uni_x = list(df2[x_name].unique())
                start_base = [0] * len(uni_x)
                base_dict = dict(zip(uni_x,start_base)) # each base value starts from 0  
                for var, group in df2.groupby(s_name):
                    add_dict = dict(zip(list(group[x_name]), list(group['Value'])))
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], width=0.2,
                                        base=[base_dict[i] for i in list(add_dict.keys())], 
                                        name='%s - %s'%(metric_name,var), offset=0.1))
                    for k in list(add_dict.keys()): 
                        base_dict[k] = base_dict[k] + add_dict[k]  # add value to base

                fig.update_xaxes(title=x_name)
                fig.update_yaxes(title=unit_name, type='linear')
                fig.update_layout(title_y=0.97, title_text="%s Compare" % (metric_name))

            elif len(selected_metric_type) == 2:
                metric_name1 = selected_metric_type[0]
                metric_name2 = selected_metric_type[1]
                unit_name1 = unit_dict.get(selected_metric_type[0])
                unit_name2 = unit_dict.get(selected_metric_type[1])

                df1_m1 = df1[df1['Metric'].isin([metric_name1])]
                df1_m2 = df1[df1['Metric'].isin([metric_name2])]
                df2_m1 = df2[df2['Metric'].isin([metric_name1])]
                df2_m2 = df2[df2['Metric'].isin([metric_name2])]

                fig = make_subplots(specs=[[{"secondary_y": True}]])

                for var, group in df1_m1.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'],
                                        width=0.1, name='%s - %s'%(metric_name1,var), offset=-0.2))
                
                uni_x = list(df2_m1[x_name].unique())
                start_base = [0] * len(uni_x)
                base_dict = dict(zip(uni_x,start_base)) # each base value starts from 0
                for var, group in df2_m1.groupby(s_name):                
                    add_dict = dict(zip(list(group[x_name]), list(group['Value'])))
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'], 
                                        base=[base_dict[i] for i in list(add_dict.keys())], # use base
                                        width=0.1, name='%s - %s'%(metric_name2,var), offset=-0.1))
                    for k in list(add_dict.keys()): 
                        base_dict[k] = base_dict[k] + add_dict[k]  # add value to base                 

                for var, group in df1_m2.groupby(s_name):
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'],
                                        width=0.1, name='%s - %s'%(metric_name1,var), offset=0.05, 
                                        marker_line_color='#595959', opacity=0.6), secondary_y=True)

                uni_x = list(df2_m2[x_name].unique())
                start_base = [0] * len(uni_x)
                base_dict = dict(zip(uni_x,start_base)) # each base value starts from 0            
                for var, group in df2_m2.groupby(s_name):
                    add_dict = dict(zip(list(group[x_name]), list(group['Value'])))
                    fig.add_trace(go.Bar(x=group[x_name], y=group['Value'],
                                        base=[base_dict[i] for i in list(add_dict.keys())], # use base
                                        width=0.1, name='%s - %s'%(metric_name2,var), offset=0.15, 
                                        marker_line_color='#595959', opacity=0.6), secondary_y=True)
                    for k in list(add_dict.keys()): 
                        base_dict[k] = base_dict[k] + add_dict[k]  # add value to base 
                
                fig.update_xaxes(title_text=x_name)
                fig.update_yaxes(title_text='%s (%s)' % (metric_name1, unit_name1), secondary_y=False, rangemode='nonnegative')
                fig.update_yaxes(title_text='%s (%s)' % (metric_name2, unit_name2), secondary_y=True, rangemode='nonnegative')
                fig.update_layout(barmode='stack', title_y=0.97,
                    title_text="%s & %s Compare" % (metric_name1, metric_name2))
                        
            elif len(selected_metric_type) > 2:
                
                fig = make_subplots() # empty

        fig.update_layout(margin={'l': 40, 'b': 30, 't': 40, 'r': 0}, hovermode='closest')

        return fig


    ######################## END OF CALLBACK #########################


    app.run_server(debug=True)
