"""Main Dash application."""
import dash
import dash_bootstrap_components as dbc
from app.components.layout import create_main_layout

# Initialize the Dash app
# CSS files in app/assets/ folder will be automatically loaded by Dash
# No external CDN dependencies - all assets are local
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True
)

# Set the layout
app.layout = create_main_layout()

# Import callbacks to register them
from app.components import callbacks, modal_callbacks

# Expose the Flask server for uvicorn
server = app.server

if __name__ == '__main__':
    # For development - run with Dash's built-in server
    app.run_server(debug=True, host='0.0.0.0', port=8000)
