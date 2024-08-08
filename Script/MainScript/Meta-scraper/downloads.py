import dash
from dash import dcc, html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Button("Download", id="btn"),
    dcc.Download(id="download")
])

@app.callback(
    Output("download", "data"),
    [Input("btn", "n_clicks")]
)
def func(n_clicks):
    if n_clicks is None:
        return dash.no_update
    return dcc.send_file("/path/to/file.txt")

if __name__ == '__main__':
    app.run_server(debug=True)
