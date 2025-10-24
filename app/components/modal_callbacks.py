"""Callbacks for event creation modal."""
import base64
from dash import callback, Input, Output, State, no_update, html
from dash.exceptions import PreventUpdate
from datetime import datetime

from app.services.event_creation_service import EventCreationService


@callback(
    Output('create-event-modal', 'is_open'),
    [Input('create-event-btn', 'n_clicks'),
     Input('modal-cancel-btn', 'n_clicks')],
    State('create-event-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_modal(create_clicks, cancel_clicks, is_open):
    """Toggle the create event modal."""
    return not is_open


@callback(
    [Output('csv-upload-store', 'data'),
     Output('csv-validation-message', 'children')],
    Input('csv-upload', 'contents'),
    State('csv-upload', 'filename'),
    prevent_initial_call=True
)
def validate_csv_upload(contents, filename):
    """Validate uploaded CSV file."""
    if not contents:
        raise PreventUpdate
    
    try:
        # Decode the file content
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        file_content = decoded.decode('utf-8')
        
        # Validate CSV
        valid, account_numbers, error_message = EventCreationService.validate_csv_file(file_content)
        
        if valid:
            success_msg = html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                html.Span(f"Successfully validated {len(account_numbers):,} account numbers", 
                         className="text-success")
            ], className="mt-2")
            return account_numbers, success_msg
        else:
            error_msg = html.Div([
                html.I(className="fas fa-exclamation-circle text-danger me-2"),
                html.Span(error_message, className="text-danger")
            ], className="mt-2")
            return None, error_msg
            
    except Exception as e:
        error_msg = html.Div([
            html.I(className="fas fa-exclamation-circle text-danger me-2"),
            html.Span(f"Error processing file: {str(e)}", className="text-danger")
        ], className="mt-2")
        return None, error_msg


@callback(
    Output('modal-submit-btn', 'disabled'),
    [Input('modal-event-name', 'value'),
     Input('modal-subgroup', 'value'),
     Input('modal-event-date', 'date'),
     Input('modal-monitor-start', 'date'),
     Input('modal-monitor-end', 'date'),
     Input('modal-description', 'value'),
     Input('csv-upload-store', 'data')],
    prevent_initial_call=False
)
def update_submit_button(event_name, subgroup, event_date, monitor_start, monitor_end, description, csv_data):
    """Enable submit button when all fields are filled."""
    # Check if all required fields are filled
    if (event_name and subgroup and event_date and monitor_start and 
        monitor_end and description and csv_data):
        return False
    return True


@callback(
    [Output('choice-modal', 'is_open'),
     Output('choice-modal-body', 'children'),
     Output('event-choice-store', 'data')],
    [Input('modal-submit-btn', 'n_clicks'),
     Input('choice-cancel-btn', 'n_clicks'),
     Input('choice-append-btn', 'n_clicks'),
     Input('choice-overwrite-btn', 'n_clicks')],
    [State('modal-event-name', 'value'),
     State('modal-subgroup', 'value'),
     State('modal-event-date', 'date'),
     State('modal-monitor-start', 'date'),
     State('modal-monitor-end', 'date'),
     State('modal-description', 'value'),
     State('csv-upload-store', 'data'),
     State('choice-modal', 'is_open'),
     State('event-choice-store', 'data')],
    prevent_initial_call=True
)
def handle_event_submission(submit_clicks, cancel_clicks, append_clicks, overwrite_clicks,
                           event_name, subgroup, event_date, monitor_start, monitor_end,
                           description, account_numbers, choice_modal_open, choice_data):
    """Handle event submission and user choice for existing events."""
    from dash import ctx
    
    if not ctx.triggered_id:
        raise PreventUpdate
    
    # Handle choice modal buttons
    if ctx.triggered_id == 'choice-cancel-btn':
        return False, '', None
    
    if ctx.triggered_id == 'choice-append-btn':
        # User chose to append
        return False, '', {'choice': 'append', 'proceed': True}
    
    if ctx.triggered_id == 'choice-overwrite-btn':
        # User chose to overwrite
        return False, '', {'choice': 'overwrite', 'proceed': True}
    
    # Handle initial submission
    if ctx.triggered_id == 'modal-submit-btn':
        if not all([event_name, subgroup, event_date, monitor_start, monitor_end, description, account_numbers]):
            raise PreventUpdate
        
        try:
            # Initial check if event exists (without creating)
            result, message, _ = EventCreationService.create_event(
                event_name, subgroup, event_date, monitor_start, monitor_end,
                description, account_numbers, overwrite_choice=None
            )
            
            if result == 'needs_choice':
                # Show choice modal
                choice_body = html.Div([
                    html.P(message['message']),
                    html.P("What would you like to do?")
                ])
                return True, choice_body, {'event_data': {
                    'event_name': event_name,
                    'subgroup': subgroup,
                    'event_date': event_date,
                    'monitor_start': monitor_start,
                    'monitor_end': monitor_end,
                    'description': description,
                    'account_numbers': account_numbers
                }}
            
            # If no choice needed, proceed with creation
            return False, '', {'choice': None, 'proceed': True}
            
        except Exception as e:
            return False, '', None
    
    return no_update, no_update, no_update


@callback(
    [Output('create-event-modal', 'is_open', allow_duplicate=True),
     Output('modal-loading-indicator', 'style'),
     Output('modal-loading-text', 'children'),
     Output('event-name-dropdown', 'value', allow_duplicate=True),
     Output('event-subgroup-dropdown', 'value', allow_duplicate=True),
     Output('raw-call-data-store', 'data', allow_duplicate=True),
     Output('event-details-store', 'data', allow_duplicate=True)],
    Input('event-choice-store', 'data'),
    [State('modal-event-name', 'value'),
     State('modal-subgroup', 'value'),
     State('modal-event-date', 'date'),
     State('modal-monitor-start', 'date'),
     State('modal-monitor-end', 'date'),
     State('modal-description', 'value'),
     State('csv-upload-store', 'data')],
    prevent_initial_call=True
)
def process_event_creation(choice_data, event_name, subgroup, event_date, 
                          monitor_start, monitor_end, description, account_numbers):
    """Process the actual event creation after user choice."""
    if not choice_data or not choice_data.get('proceed'):
        raise PreventUpdate
    
    # Get event data (might be from choice_data if it was stored)
    if 'event_data' in choice_data:
        ed = choice_data['event_data']
        event_name = ed['event_name']
        subgroup = ed['subgroup']
        event_date = ed['event_date']
        monitor_start = ed['monitor_start']
        monitor_end = ed['monitor_end']
        description = ed['description']
        account_numbers = ed['account_numbers']
    
    overwrite_choice = choice_data.get('choice')
    
    try:
        # Show loading indicator
        loading_style = {'display': 'block'}
        loading_text = "Starting event creation..."
        
        # Progress callback to update UI
        progress_messages = []
        
        def progress_callback(message):
            progress_messages.append(message)
        
        # Create the event
        success, message, call_data = EventCreationService.create_event(
            event_name, subgroup, event_date, monitor_start, monitor_end,
            description, account_numbers, progress_callback, overwrite_choice
        )
        
        if success:
            # Get event details
            from app.services.event_service import EventService
            event_details = EventService.get_event_details(event_name, subgroup)
            
            # Close modal and load data
            return (False, {'display': 'none'}, '', 
                   event_name, subgroup, call_data, event_details)
        else:
            # Show error but keep modal open
            return (True, {'display': 'none'}, f"Error: {message}",
                   no_update, no_update, no_update, no_update)
            
    except Exception as e:
        return (True, {'display': 'none'}, f"Error: {str(e)}",
               no_update, no_update, no_update, no_update)
