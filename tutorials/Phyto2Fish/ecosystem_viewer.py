"""Interactive Jupyter viewer for ecosystem_dashboard.py."""

import io
import base64
import traceback

import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, HTML

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


def launch(region_dropdown, map_variable='Catch', zoom=2.0):
    """
    Display dashboard and map using an external MEOW dropdown.

    Creates the viewer once and updates it when the selected
    MEOW, map variable, or zoom changes.
    """

    # Map controls only (no second MEOW dropdown)
    variable_select = widgets.Dropdown(
        options=MAP_VARIABLES,
        value=map_variable,
        description='Map:'
    )

    zoom_select = widgets.FloatSlider(
        value=zoom,
        min=0.1,
        max=2.0,
        step=0.1,
        description='Zoom:',
        continuous_update=False
    )

    output = widgets.Output()

    # ------------------------------------------
    # Render selected ecosystem
    # ------------------------------------------
    def update_view(change=None):

        region_name = region_dropdown.value

        with output:
            output.clear_output(wait=True)

            try:
                dashboard = dash.show_dashboard(region_name)

                with plt.ioff():
                    fig = dash.show_region_map(
                        region_name,
                        variable_select.value,
                        zoom_select.value
                    )

                    image = io.BytesIO()

                    try:
                        fig.savefig(
                            image,
                            format='png',
                            dpi=130,
                            bbox_inches='tight'
                        )
                    finally:
                        plt.close(fig)

                map_image = base64.b64encode(
                    image.getvalue()
                ).decode('ascii')

                html = f'''
                <div style="
                    display:flex;
                    align-items:flex-start;
                    gap:16px;
                    width:100%;
                    max-width:1700px;
                ">
                    <div style="flex:1.2; min-width:0">
                        {dashboard}
                    </div>
                    <div style="flex:1.05; min-width:0">
                        <img
                            src="data:image/png;base64,{map_image}"
                            style="width:100%; height:auto"
                        >
                    </div>
                </div>
                '''

                display(HTML(html))

            except Exception:
                traceback.print_exc()

    # ------------------------------------------
    # Observe changes
    # ------------------------------------------
    region_dropdown.observe(update_view, names='value')
    variable_select.observe(update_view, names='value')
    zoom_select.observe(update_view, names='value')

    # ------------------------------------------
    # Display controls and output
    # ------------------------------------------
    controls = widgets.HBox([
        variable_select,
        zoom_select
    ])

    viewer = widgets.VBox([
        controls,
        output
    ])

    # Initial render
    update_view()

    return viewer