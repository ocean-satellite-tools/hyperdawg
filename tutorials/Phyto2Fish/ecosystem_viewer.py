"""Interactive Jupyter viewer for ecosystem_dashboard.py.

Run after loading the model data in your notebook:
    import ecosystem_dashboard as dash
    import ecosystem_viewer as viewer
    dash.configure(data=data, sst=sst, chl=chl, meow=meow,
                   alpha=alpha, TE=TE, wet_weight=wet_weight)
    viewer.launch(region_name='Natal', map_variable='Catch', zoom=0.70)
"""

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
    """Show MEOW, variable, and zoom controls above a nine-card dashboard and map."""
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
        <div style="display:flex;align-items:flex-start;gap:20px;width:100%;max-width:1700px">
            <div style="flex:1.2;min-width:0">{dashboard}</div>
            <div style="flex:1.05;min-width:0">
                <img src="data:image/png;base64,{map_image}" style="width:100%;height:auto">
            </div>
        </div>
        '''
        with output:
            clear_output(wait=True)
            display(HTML(html))

    region_select.observe(update_view, names='value')
    variable_select.observe(update_view, names='value')
    zoom_select.observe(update_view, names='value')

    display(widgets.HBox([region_select, variable_select, zoom_select]))
    display(output)
    update_view()
    return region_select, variable_select, zoom_select
