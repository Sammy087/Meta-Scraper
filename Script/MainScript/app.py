import base64
import os
import logging
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
from src.video_processing import clean_video
from src.mass_automation import init_accounts, run_bot, dump_screen  # Import functions
import download_video


# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("TikTok Video Downloader & Cleaner", className="text-center mb-4"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("TikTok Video URL:"),
                    dbc.Input(id='video-url', type='text', placeholder='Enter TikTok video URL or upload a file with URLs')
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Upload File with URLs:"),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        multiple=False
                    ),
                    html.Div(id='file-name', className='mt-2'),
                    html.Div(id='upload-status', className='mt-2')
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button('Download and Clean', id='submit-val', n_clicks=0, color='primary', className="btn-block")
                ])
            ]),
        ], md=6, className="offset-md-3")
    ], className="mt-5"),
    dbc.Row([
        dbc.Col([
            html.H4("What the Bot Does:", className="text-center mt-5 mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.H5("Video Download and Processing", className="card-title"),
                    html.Ul([
                        html.Li("Downloads the TikTok video using yt-dlp."),
                        html.Li("Removes all metadata to enhance privacy."),
                        html.Li("Adjusts video properties:", className="mt-3"),
                        html.Ul([
                            html.Li("Random saturation adjustment."),
                            html.Li("Random contrast adjustment."),
                            html.Li("Random highlight adjustment."),
                            html.Li("Random sharpness adjustment.")
                        ]),
                        html.Li("Applies a random rotation."),
                        html.Li("Adds an invisible watermark.")
                    ])
                ])
            ])
        ])
    ])
])

@app.callback(
    Output('upload-status', 'children'),
    [Input('submit-val', 'n_clicks')],
    [State('video-url', 'value'), State('upload-data', 'contents')]
)
def process_input(n_clicks, video_url, upload_data):
    if n_clicks > 0:
        if upload_data:
            content_type, content_string = upload_data.split(',')
            decoded = base64.b64decode(content_string)
            urls = decoded.decode('utf-8').splitlines()
        elif video_url:
            urls = [video_url]
        else:
            return "Please provide a URL or upload a file."

        output_path = "videos"
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        for video_url in urls:
            logging.info(f"Processing URL: {video_url}")
            try:
                download_video(video_url, output_path)
                downloaded_files = [f for f in os.listdir(output_path) if os.path.isfile(os.path.join(output_path, f)) and not f.startswith('cleaned_')]
                if downloaded_files:
                    for downloaded_file in downloaded_files:
                        input_video_path = os.path.join(output_path, downloaded_file)
                        unique_suffix = any.randint(1000, 9999)
                        output_video_path = os.path.join(output_path, f'cleaned_{unique_suffix}_{downloaded_file}')
                        
                        if clean_video(input_video_path, output_video_path):
                            logging.info(f'Video downloaded and edited successfully! Edited video saved as: {output_video_path}')
                            os.remove(input_video_path)
                        else:
                            logging.error(f'Failed to clean video: {input_video_path}')
                else:
                    logging.error('Error: No video found in the output directory.')
            except Exception as e:
                logging.error(f"Error processing URL {video_url}: {e}")
        
        return "Processing complete. Check the 'videos' directory for cleaned videos."

if __name__ == '__main__':
    # Example usage of mass automation functions:
    # init_accounts(['example_user1', 'example_user2'])
    # run_bot()
    # dump_screen()

    app.run_server(debug=True)
