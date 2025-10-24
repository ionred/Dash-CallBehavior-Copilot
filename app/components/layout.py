"""Main layout for the Dash application."""
import dash_bootstrap_components as dbc
from dash import html, dcc


def create_main_layout():
    """Create the main page layout."""
    
    layout = dbc.Container([
        # Store components for maintaining state
        dcc.Store(id='raw-call-data-store'),
        dcc.Store(id='event-details-store'),
        dcc.Store(id='load-cancelled-store', data=False),
        dcc.Store(id='csv-upload-store'),
        dcc.Store(id='event-choice-store'),
        
        # Interval component for progress updates (disabled by default)
        dcc.Interval(id='progress-interval', interval=1000, disabled=True),
        
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("Call Behavior Analysis", className="text-center mb-4 mt-3")
            ])
        ]),
        
        # Control row with dropdowns and buttons
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    html.I(className="fas fa-sync-alt"),
                    id='refresh-events-btn',
                    color="secondary",
                    className="me-2"
                )
            ], width="auto"),
            dbc.Col([
                dcc.Dropdown(
                    id='event-name-dropdown',
                    placeholder='Select Event Name',
                    className="mb-2"
                )
            ], width=3),
            dbc.Col([
                dcc.Dropdown(
                    id='event-subgroup-dropdown',
                    placeholder='Select Subgroup',
                    className="mb-2"
                )
            ], width=3),
            dbc.Col([
                dbc.Button(
                    "Load Data",
                    id='load-data-btn',
                    color="primary",
                    className="me-2",
                    disabled=True
                ),
                dbc.Button(
                    "Clear Data",
                    id='clear-data-btn',
                    color="warning",
                    disabled=True
                )
            ], width="auto"),
        ], className="mb-4 align-items-center"),
        
        # Create Event button
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Create New Event",
                    id='create-event-btn',
                    color="success",
                    className="mb-3"
                )
            ])
        ]),
        
        # Loading indicator area
        dbc.Row([
            dbc.Col([
                html.Div(id='loading-indicator', style={'display': 'none'}, children=[
                    dbc.Spinner(color="primary", size="lg"),
                    html.H4(id='loading-text', className="mt-3 text-center")
                ])
            ])
        ], className="mb-4"),
        
        # Queue filter dropdown (hidden by default)
        dbc.Row([
            dbc.Col([
                html.Label("Filter by Queue:", id='queue-filter-label', style={'display': 'none'}),
                dcc.Dropdown(
                    id='queue-filter-dropdown',
                    placeholder='Select Queue',
                    style={'display': 'none'}
                )
            ], width=4)
        ], className="mb-3"),
        
        # Cards row (hidden by default)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Event Description"),
                    dbc.CardBody(id='description-card-body')
                ], id='description-card', style={'display': 'none'})
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Top 3 Queues"),
                    dbc.CardBody(id='top-queues-card-body')
                ], id='top-queues-card', style={'display': 'none'})
            ], width=6)
        ], className="mb-4"),
        
        # Graphs row (hidden by default)
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='line-chart', style={'display': 'none'})
            ], width=6),
            dbc.Col([
                dcc.Graph(id='bar-chart', style={'display': 'none'})
            ], width=6)
        ], className="mb-4"),
        
        # Create Event Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Create New Event")),
            dbc.ModalBody([
                # Event details form
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Event Name"),
                        dbc.Input(id='modal-event-name', type='text', placeholder='Enter event name')
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Subgroup"),
                        dbc.Input(id='modal-subgroup', type='text', placeholder='Enter subgroup')
                    ], width=6)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Event Date"),
                        dcc.DatePickerSingle(id='modal-event-date', placeholder='Select date')
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Monitor Start"),
                        dcc.DatePickerSingle(id='modal-monitor-start', placeholder='Select start date')
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Monitor End"),
                        dcc.DatePickerSingle(id='modal-monitor-end', placeholder='Select end date')
                    ], width=4)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Description"),
                        dbc.Textarea(id='modal-description', placeholder='Enter description', rows=3)
                    ])
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Upload Account Numbers CSV"),
                        dcc.Upload(
                            id='csv-upload',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select CSV File')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'cursor': 'pointer'
                            }
                        )
                    ])
                ], className="mb-3"),
                
                # CSV validation message
                html.Div(id='csv-validation-message'),
                
                # Progress indicator for event creation
                html.Div(id='modal-loading-indicator', style={'display': 'none'}, children=[
                    dbc.Spinner(color="primary", size="sm"),
                    html.Div(id='modal-loading-text', className="mt-2")
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id='modal-cancel-btn', color="secondary", className="me-2"),
                dbc.Button("Submit", id='modal-submit-btn', color="primary", disabled=True)
            ])
        ], id='create-event-modal', size="lg", is_open=False),
        
        # Confirmation modal for overwrite/append choice
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Event Already Exists")),
            dbc.ModalBody(id='choice-modal-body'),
            dbc.ModalFooter([
                dbc.Button("Cancel", id='choice-cancel-btn', color="secondary"),
                dbc.Button("Append Accounts Only", id='choice-append-btn', color="info", className="ms-2"),
                dbc.Button("Overwrite", id='choice-overwrite-btn', color="warning", className="ms-2")
            ])
        ], id='choice-modal', is_open=False),
        
    ], fluid=True)
    
    return layout
