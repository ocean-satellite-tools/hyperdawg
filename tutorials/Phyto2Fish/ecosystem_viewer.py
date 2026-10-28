"""Interactive Jupyter viewer for ecosystem_dashboard.py."""

import io
import base64
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

import ecosystem_dashboard as dash

MAP_VARIABLES = [
    ('Prediction bias', 'Log_bias'),
    ('Phytoplankton size factor', 'Delta_L'),
    ('Sea surface temperature', 'SST'),
    ('Chlorophyll-a', 'CHL'),
    ('Net primary production', 'NPP'),
    ('Observed catch', 'Catch'),
    ('Baseline predicted catch', 'Baseline_predicted'),
    ('Phyto2Fish predicted catch', 'Phyto2Fish_predicted'),
    ('Apparent fishing hours', 'mean_monthly_fishing_hours')
]


def launch(region_name='Natal', map_variable='Catch', zoom=0.70):
    """Show MEOW, map variable, and zoom controls above the dashboard and map."""
    regions = dash.available_regions()
    region_select = widgets.Dropdown(options=regions, value=region_name, description='MEOW:')
    variable_select = widgets.Dropdown(options=MAP_VARIABLES, value=map_variable, description='Map:')
    zoom_select = widgets.FloatSlider(value=zoom, min=0.1, max=2.0, step=0.1, description='Zoom:', continuous_update=False)
    output = widgets.Output()

    def update_view(change=None):
        dashboard = dash.show_dashboard(region_select.value)

        with plt.ioff():
            fig = dash.show_region_map(region_select.value, variable_select.value, zoom_select.value)
            image = io.BytesIO()
            try:
                fig.savefig(image, format='png', dpi=130, bbox_inches='tight')
            finally:
                plt.close(fig)

        map_image = base64.b64encode(image.getvalue()).decode('ascii')

        html = f'''
        <style>
            .p2f-viewer {{
                width: 100%;
                max-width: 1700px;
                min-width: 0;
                container-type: inline-size;
            }}
            .p2f-layout {{
                display: grid;
                grid-template-columns: minmax(0, 1.2fr) minmax(0, 1.05fr);
                gap: 20px;
                align-items: start;
            }}
            .p2f-panel {{
                min-width: 0;
            }}
            .p2f-map {{
                display: block;
                width: 100%;
                height: auto;
            }}
            @container (max-width: 1100px) {{
                .p2f-layout {{
                    grid-template-columns: minmax(0, 1fr);
                }}
            }}
        </style>

        <div class="p2f-viewer">
            <div class="p2f-layout">
                <div class="p2f-panel">{dashboard}</div>
                <div class="p2f-panel">
                    <img class="p2f-map" src="data:image/png;base64,{map_image}">
                </div>
            </div>
        </div>
        '''

        with output:
            clear_output(wait=True)
            display(HTML(html))

    region_select.observe(update_view, names='value')
    variable_select.observe(update_view, names='value')
    zoom_select.observe(update_view, names='value')

    # Original dropdown controls
    display(widgets.HBox([region_select, variable_select, zoom_select]))
    display(output)
    update_view()

    return region_select, variable_select, zoom_select
