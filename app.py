import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from pandas_datareader import data
import plotly.express as px
import numpy as np
import dash_core_components as dcc
import plotly.graph_objects as go


# get stylesheetd
#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

# setup app
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

# import ticks
tick_list = pd.read_csv('C:/Users/hicom/Documents/Side Projects/AS_hackathon_8.1/companylist.csv')

# get tick list for dropdown
available_stocks = tick_list['Name'].unique()


def calculate_frontier(ticks):
    # get stock closing data 
    df = data.DataReader(ticks, 'yahoo', start='2015/01/01', end='2020/12/31')
    df = df['Adj Close']
    
    # Yearly returns for individual companies
    ind_er = df.resample('Y').last().pct_change().mean()
    
    # Volatility is given by the annual standard deviation. We multiply by 250 because there are 250 trading days/year.
    ann_sd = df.pct_change().apply(lambda x: np.log(1+x)).std().apply(lambda x: x*np.sqrt(250))
    
    assets = pd.concat([ind_er, ann_sd], axis=1) # Creating a table for visualising returns and volatility of assets
    assets.columns = ['Returns', 'Volatility']
    assets['ESG'] = np.random.randint(0,50,size = assets.shape[0])
    
    p_ret = [] # Define an empty array for portfolio returns
    p_vol = [] # Define an empty array for portfolio volatility
    p_weights = [] # Define an empty array for asset weights
    p_esg = []
    
    num_assets = len(df.columns)
    num_portfolios = 1000
    
    cov_matrix = df.pct_change().apply(lambda x: np.log(1+x)).cov()
    
    for portfolio in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights = weights/np.sum(weights)
        p_weights.append(weights)
        returns = np.dot(weights, ind_er) # Returns are the product of individual expected returns of asset and its 
                                          # weights 
        p_ret.append(returns)
        var = cov_matrix.mul(weights, axis=0).mul(weights, axis=1).sum().sum()# Portfolio Variance
        sd = np.sqrt(var) # Daily standard deviation
        ann_sd = sd*np.sqrt(250) # Annual standard deviation = volatility
        p_vol.append(ann_sd)
        
        esg = np.dot(weights, assets['ESG'])
        p_esg.append(esg)
        
    dat = {'Returns':p_ret, 'Volatility':p_vol, 'ESG': p_esg}

    for counter, symbol in enumerate(df.columns.tolist()):
        #print(counter, symbol)
        dat[symbol+' weight'] = [w[counter] for w in p_weights]
        
    dff  = pd.DataFrame(dat)
    return dff


# App Layout
app.layout = html.Div(children = [
    
    # header section
    html.Div(children=[
    html.H1(children="Portfolio Impact Assessment", className ='header-title'),
    
    html.P(children='Analyze the efficiency & impact potential of your portfolio', className ='header-description'),
    ],className="header",
        ),
    
    
    # Dropdown menu to choose companies
    html.Div(children =[
        html.Div(children =
        dcc.Dropdown(
            id = 'stock-drop',
            options=[{'label': i, 'value': i} for i in available_stocks],
            placeholder="Select stocks",
            value=['Stocks'],
            multi=True
        ), 
            style={'width': '30%', 'display': 'inline-block', 'float': 'left'},
            className="card")],
        className = 'wrapper'
        ),
    
    # numbers
    html.Div(id='result', style = {'width': '30%', 'display': 'inline-block', 'float': 'left'}),
    html.Div(id='esg'),
    
    # Scatterplot
    html.Div([
    dcc.Graph(
        id='efficient-frontier'
    )],
        style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),


])
    
    
@app.callback([
    dash.dependencies.Output('efficient-frontier', 'figure'),
    dash.dependencies.Output('result', 'children'),
    dash.dependencies.Output('esg', 'children')],
    [dash.dependencies.Input('stock-drop', 'value')])
def update_scatter(stock_drop):
    
    # get ticks for selected companies
    ticks = list(tick_list[tick_list.Name.isin(stock_drop)].Symbol)

    dff = calculate_frontier(ticks)
    rf = 0.01
    idx_sharp = ((dff['Returns']-rf)/dff['Volatility']).idxmax()
    
    normal_marks = dict(
            color = dff['ESG'],    # Changed marker color to look cleaner with a boundary
            size=12,
            symbol='circle',
            opacity=0.4,      # Brought down the opacity and boundaries often allow for this
           # line = raw_line   # We give the pre-defined dictionary to this attribute.
    )
    
    special_mark = dict(
    color = 'red',
    size =18,
    symbol = 'star'
    )
    
    fig = go.Figure()

    # Add traces
    fig.add_trace(go.Scatter( x=dff['Volatility'], y=dff['Returns'],mode ='markers', name='Raw Data',
                  # Instead of all the code we had before, just the pre-defined dictionary
                  marker = normal_marks))
    fig.add_trace(go.Scatter(x=[dff['Volatility'][idx_sharp]], y=[dff['Returns'][idx_sharp]], mode='markers', name='Optimal Sharp', marker = special_mark))   
    #fig = px.scatter(dff, x='Volatility', y='Returns', color='ESG', opacity =0.8)
    fig.update_layout(title = 'Portfolio Distribution')

    
    sharp = (dff.iloc[idx_sharp].Returns -rf)/dff.iloc[idx_sharp].Volatility

    text = 'Current SHARP value of the portfolio: ' + str(sharp)
    esg = 'Current ESG value: ' + str(dff.iloc[idx_sharp].ESG)
    return fig, text, esg
    #print(stock_drop)


  
if __name__ == '__main__':
    app.run_server(debug=True)