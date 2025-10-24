"""Callbacks for main page functionality."""
from dash import callback, Input, Output, State, no_update, ctx, html
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime

from app.services.event_service import EventService


@callback(
    [Output('event-name-dropdown', 'options'),
     Output('event-name-dropdown', 'value')],
    [Input('refresh-events-btn', 'n_clicks'),
     Input('create-event-modal', 'is_open')],
    prevent_initial_call=False
)
def update_event_dropdown(refresh_clicks, modal_is_open):
    """Update event name dropdown options."""
    try:
        events_dict = EventService.get_events_and_subgroups()
        options = [{'label': name, 'value': name} for name in sorted(events_dict.keys())]
        return options, None
    except Exception as e:
        print(f"Error loading events: {e}")
        return [], None


@callback(
    [Output('event-subgroup-dropdown', 'options'),
     Output('event-subgroup-dropdown', 'value')],
    Input('event-name-dropdown', 'value'),
    prevent_initial_call=True
)
def update_subgroup_dropdown(event_name):
    """Update subgroup dropdown based on selected event."""
    if not event_name:
        return [], None
    
    try:
        events_dict = EventService.get_events_and_subgroups()
        subgroups = events_dict.get(event_name, [])
        
        options = [{'label': sg['subGroup'], 'value': sg['subGroup']} for sg in subgroups]
        
        # Auto-select if only one subgroup
        selected_value = options[0]['value'] if len(options) == 1 else None
        
        return options, selected_value
    except Exception as e:
        print(f"Error loading subgroups: {e}")
        return [], None


@callback(
    Output('load-data-btn', 'disabled'),
    [Input('event-name-dropdown', 'value'),
     Input('event-subgroup-dropdown', 'value'),
     Input('raw-call-data-store', 'data')],
    prevent_initial_call=False
)
def update_load_button_state(event_name, subgroup, raw_data):
    """Enable/disable load data button based on selections."""
    # Disable if no event/subgroup selected
    if not event_name or not subgroup:
        return True
    
    # Disable if data is already loaded for this event/subgroup
    if raw_data is not None:
        return True
    
    return False


@callback(
    Output('clear-data-btn', 'disabled'),
    [Input('event-name-dropdown', 'value'),
     Input('event-subgroup-dropdown', 'value'),
     Input('raw-call-data-store', 'data')],
    prevent_initial_call=False
)
def update_clear_button_state(event_name, subgroup, raw_data):
    """Enable/disable clear data button."""
    # Enable if any dropdown has selection or data is loaded
    if event_name or subgroup or raw_data is not None:
        return False
    return True


@callback(
    [Output('raw-call-data-store', 'data'),
     Output('event-details-store', 'data'),
     Output('loading-indicator', 'style'),
     Output('loading-text', 'children'),
     Output('load-data-btn', 'children')],
    [Input('load-data-btn', 'n_clicks'),
     Input('load-cancelled-store', 'data')],
    [State('event-name-dropdown', 'value'),
     State('event-subgroup-dropdown', 'value'),
     State('raw-call-data-store', 'data')],
    prevent_initial_call=True
)
def load_call_data(n_clicks, cancelled, event_name, subgroup, current_data):
    """Load call data for selected event and subgroup."""
    if not n_clicks or not event_name or not subgroup:
        raise PreventUpdate
    
    # Check if cancelled
    if cancelled:
        return current_data, no_update, {'display': 'none'}, '', 'Load Data'
    
    try:
        # Show loading indicator
        loading_style = {'display': 'block', 'text-align': 'center'}
        
        # Step 1: Get event details
        event_details = EventService.get_event_details(event_name, subgroup)
        if not event_details:
            return None, None, {'display': 'none'}, '', 'Load Data'
        
        # Step 2: Load account numbers
        account_numbers = EventService.load_account_numbers(event_name, subgroup)
        account_count = len(account_numbers)
        
        # Step 3: Load call data
        call_data = EventService.load_call_data(
            event_name,
            subgroup,
            account_numbers,
            event_details['monitorStart'],
            event_details['monitorEnd']
        )
        
        call_count = len(call_data)
        
        return call_data, event_details, {'display': 'none'}, '', 'Load Data'
        
    except Exception as e:
        print(f"Error loading call data: {e}")
        return None, None, {'display': 'none'}, f'Error: {str(e)}', 'Load Data'


@callback(
    [Output('queue-filter-dropdown', 'options'),
     Output('queue-filter-dropdown', 'value'),
     Output('queue-filter-dropdown', 'style'),
     Output('queue-filter-label', 'style')],
    Input('raw-call-data-store', 'data'),
    prevent_initial_call=False
)
def update_queue_filter(raw_data):
    """Update queue filter dropdown when data is loaded."""
    if not raw_data:
        return [], None, {'display': 'none'}, {'display': 'none'}
    
    try:
        queues = EventService.get_unique_queues(raw_data)
        options = [{'label': 'All', 'value': 'All'}]
        options.extend([{'label': q, 'value': q} for q in queues])
        
        return options, 'All', {'display': 'block'}, {'display': 'block'}
    except Exception as e:
        print(f"Error updating queue filter: {e}")
        return [], None, {'display': 'none'}, {'display': 'none'}


@callback(
    [Output('description-card', 'style'),
     Output('description-card-body', 'children')],
    [Input('raw-call-data-store', 'data'),
     Input('event-details-store', 'data')],
    prevent_initial_call=False
)
def update_description_card(raw_data, event_details):
    """Update description card when data is loaded."""
    if not raw_data or not event_details:
        return {'display': 'none'}, ''
    
    try:
        description_content = [
            html.P([html.Strong("Event: "), event_details.get('eventName', '')]),
            html.P([html.Strong("Subgroup: "), event_details.get('subGroup', '')]),
            html.P([html.Strong("Event Date: "), str(event_details.get('eventDate', ''))]),
            html.P([html.Strong("Monitor Period: "), 
                   f"{event_details.get('monitorStart', '')} to {event_details.get('monitorEnd', '')}"]),
            html.P([html.Strong("Description: "), event_details.get('Description', '')])
        ]
        
        return {'display': 'block'}, description_content
    except Exception as e:
        print(f"Error updating description card: {e}")
        return {'display': 'none'}, ''


@callback(
    [Output('top-queues-card', 'style'),
     Output('top-queues-card-body', 'children')],
    Input('raw-call-data-store', 'data'),
    prevent_initial_call=False
)
def update_top_queues_card(raw_data):
    """Update top 3 queues card when data is loaded."""
    if not raw_data:
        return {'display': 'none'}, ''
    
    try:
        from dash import html
        
        top_queues = EventService.get_top_queues(raw_data, top_n=3)
        
        if not top_queues:
            return {'display': 'block'}, html.P("No queue data available")
        
        queue_content = []
        for idx, queue in enumerate(top_queues, 1):
            queue_content.append(
                html.Div([
                    html.H5(f"{idx}. {queue['queueName']}"),
                    html.P(f"Calls: {queue['callCount']:,} ({queue['percentage']:.2f}%)")
                ], className="mb-3")
            )
        
        return {'display': 'block'}, queue_content
    except Exception as e:
        print(f"Error updating top queues card: {e}")
        return {'display': 'none'}, ''


@callback(
    [Output('line-chart', 'figure'),
     Output('line-chart', 'style'),
     Output('bar-chart', 'figure'),
     Output('bar-chart', 'style')],
    [Input('raw-call-data-store', 'data'),
     Input('queue-filter-dropdown', 'value')],
    prevent_initial_call=False
)
def update_charts(raw_data, selected_queue):
    """Update charts when data is loaded or queue filter changes."""
    if not raw_data:
        empty_fig = go.Figure()
        return empty_fig, {'display': 'none'}, empty_fig, {'display': 'none'}
    
    try:
        # Filter data by queue if needed
        filtered_data = EventService.filter_call_data_by_queue(raw_data, selected_queue)
        
        if not filtered_data:
            empty_fig = go.Figure()
            return empty_fig, {'display': 'block'}, empty_fig, {'display': 'block'}
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(filtered_data)
        
        # Aggregate by date for charts
        daily_counts = df.groupby('CallDate').size().reset_index(name='CallCount')
        daily_counts = daily_counts.sort_values('CallDate')
        
        # Line chart: Call counts over time
        line_fig = go.Figure()
        line_fig.add_trace(go.Scatter(
            x=daily_counts['CallDate'],
            y=daily_counts['CallCount'],
            mode='lines+markers',
            name='Call Count',
            line=dict(color='blue', width=2)
        ))
        line_fig.update_layout(
            title='Call Volume Over Time',
            xaxis_title='Date',
            yaxis_title='Number of Calls',
            hovermode='x unified'
        )
        
        # Bar chart: Call counts by date
        bar_fig = go.Figure()
        bar_fig.add_trace(go.Bar(
            x=daily_counts['CallDate'],
            y=daily_counts['CallCount'],
            name='Call Count',
            marker_color='steelblue'
        ))
        bar_fig.update_layout(
            title='Call Volume by Date',
            xaxis_title='Date',
            yaxis_title='Number of Calls',
            hovermode='x unified'
        )
        
        return line_fig, {'display': 'block'}, bar_fig, {'display': 'block'}
        
    except Exception as e:
        print(f"Error updating charts: {e}")
        empty_fig = go.Figure()
        return empty_fig, {'display': 'none'}, empty_fig, {'display': 'none'}


@callback(
    [Output('event-name-dropdown', 'value', allow_duplicate=True),
     Output('event-subgroup-dropdown', 'value', allow_duplicate=True),
     Output('raw-call-data-store', 'data', allow_duplicate=True),
     Output('event-details-store', 'data', allow_duplicate=True)],
    Input('clear-data-btn', 'n_clicks'),
    prevent_initial_call=True
)
def clear_data(n_clicks):
    """Clear all data and selections."""
    if not n_clicks:
        raise PreventUpdate
    
    return None, None, None, None
