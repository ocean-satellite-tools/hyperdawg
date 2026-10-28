"""MEOW marine ecosystem dashboard helpers."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.stats import linregress, percentileofscore


def configure(data, sst, chl, meow, alpha, TE, wet_weight):
    """Pass the notebook's prepared model data into this module."""
    global _data, _sst, _chl, _world, _alpha, _TE, _wet_weight, _effort_by_meow, _global_effort
    _data, _sst, _chl = data, sst, chl
    _world = meow.to_crs(epsg=4326).copy()
    _alpha, _TE, _wet_weight = alpha, TE, wet_weight
    _effort_by_meow = data[['MEOW', 'mean_monthly_fishing_hours']].drop_duplicates('MEOW').dropna()
    _global_effort = _effort_by_meow.mean_monthly_fishing_hours


def available_regions():
    return sorted(set(_world.ECOREGION) & set(_data.MEOW) & set(_sst.columns) & set(_chl.columns))


def indicator(values, years, scale=1, fmt=",.1f"):
    v, y = np.asarray(values, dtype=float), np.asarray(years, dtype=float)
    valid = np.isfinite(v) & np.isfinite(y)
    v, y = v[valid], y[valid]
    if len(v) == 0: return "No data"
    fit = linregress(y, v) if len(v) >= 3 and len(np.unique(y)) > 1 else None
    arrow = ("↑" if fit.slope > 0 else "↓") if fit and fit.pvalue < 0.05 else "↔"
    color = "#c65c50" if arrow == "↑" else "#377caa" if arrow == "↓" else "#888888"
    sd = v.std(ddof=1) if len(v) > 1 else 0
    return f'<span>{v.mean()/scale:{fmt}}</span><span class="p2f-sd">± {sd/scale:{fmt}}</span><span class="p2f-arrow" style="color:{color}">{arrow}</span>'


def trend_indicator(values, years, unit, fmt="+.3f"):
    v, y = np.asarray(values, dtype=float), np.asarray(years, dtype=float)
    valid = np.isfinite(v) & np.isfinite(y)
    v, y = v[valid], y[valid]
    if len(v) < 3 or len(np.unique(y)) < 2: return "No data", unit
    fit = linregress(y, v)
    arrow = ("↑" if fit.slope > 0 else "↓") if fit.pvalue < 0.05 else "↔"
    color = "#c65c50" if arrow == "↑" else "#377caa" if arrow == "↓" else "#888888"
    value = f'<span>{fit.slope*10:{fmt}}</span><span class="p2f-arrow" style="color:{color}">{arrow}</span>'
    return value, f'{unit}/decade'


def show_dashboard(region_name):
    region = _data[_data.MEOW == region_name].copy().sort_values('year')
    region['Baseline'] = _alpha * region.NPP * _wet_weight * _TE ** (region.TL - 1)
    region['Phyto2Fish'] = region.Predicted

    sst_trend, sst_unit = trend_indicator(_sst[region_name], _sst.year, "°C")
    chl_trend, chl_unit = trend_indicator(_chl[region_name], _chl.year, "mg/m³", fmt="+.4f")

    region_effort = _effort_by_meow.loc[_effort_by_meow.MEOW == region_name, 'mean_monthly_fishing_hours']
    effort = f'{region_effort.iloc[0]:,.0f}' if len(region_effort) else "No data"
    percentile = f"{percentileofscore(_global_effort, region_effort.iloc[0]):.0f}th percentile" if len(region_effort) else "No data"

    metrics = [
        ("SST TREND", sst_trend, sst_unit),
        ("CHLOROPHYLL-A TREND", chl_trend, chl_unit),
        ("NET PRIMARY PRODUCTION", indicator(region.NPP, region.year, scale=1e6, fmt=',.2f'), "million tonnes C/yr"),
        ("PHYTOPLANKTON SIZE FACTOR", indicator(region.Delta_L, region.year, fmt='.2f'), "ΔL = 0 (larger) – 2 (smaller)"),
        ("MEAN TROPHIC LEVEL", indicator(region.TL, region.year, fmt='.2f'), "Catch-weighted TL"),
        ("APPARENT FISHING EFFORT", effort, f"hours/mo | {percentile}"),
        ("OBSERVED CATCH", indicator(region.Catch, region.year, scale=1e3, fmt=',.1f'), "thousand tonnes/yr"),
        ("BASELINE PREDICTED CATCH", indicator(region.Baseline, region.year, scale=1e3, fmt=',.1f'), "thousand tonnes/yr"),
        ("PHYTO2FISH PREDICTED CATCH", indicator(region.Phyto2Fish, region.year, scale=1e3, fmt=',.1f'), "thousand tonnes/yr")
    ]

    cards = "".join(
        f'''
        <div class="p2f-card">
            <div class="p2f-label">{label}</div>
            <div class="p2f-value">{value}</div>
            <div class="p2f-unit">{unit}</div>
        </div>
        '''
        for label, value, unit in metrics
    )

    return f'''
    <style>
        .p2f-dashboard {{
            font-family: Arial, sans-serif;
            width: 100%;
            min-width: 0;
            box-sizing: border-box;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 12px;
            background: white;
            color: #222;
        }}
        .p2f-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr));
            gap: 12px;
        }}
        .p2f-card {{
            min-width: 0;
            padding: 14px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: #fafafa;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .p2f-label {{
            font-size: 12px;
            line-height: 1.4;
            font-weight: 600;
            letter-spacing: .3px;
            color: #777;
            min-height: 34px;
        }}
        .p2f-value {{
            display: flex;
            align-items: baseline;
            flex-wrap: wrap;
            column-gap: 5px;
            row-gap: 0;
            font-size: clamp(16px, 1.5vw, 21px);
            font-weight: 600;
            line-height: 1.3;
            font-variant-numeric: tabular-nums;
        }}
        .p2f-value span {{
            white-space: nowrap;
        }}
        .p2f-sd {{
            color: #888;
        }}
        .p2f-arrow {{
            font-size: 22px;
            font-weight: 500;
            line-height: 1;
        }}
        .p2f-unit {{
            font-size: 12px;
            color: #888;
            line-height: 1.4;
            overflow-wrap: break-word;
        }}
        .p2f-note {{
            font-size: 12px;
            color: #888;
            margin-top: 18px;
            line-height: 1.5;
        }}
        .p2f-footnote {{
            font-size: 11px;
            color: #999;
            margin-top: 6px;
            line-height: 1.5;
        }}
    </style>

    <div class="p2f-dashboard">
        <div style="font-size:12px;color:#888;letter-spacing:1px">MARINE ECOSYSTEM PROFILE</div>
        <div style="font-size:27px;font-weight:700;margin:5px 0 4px">{region_name}</div>
        <div style="font-size:13px;color:#888;margin-bottom:22px">{int(region.year.min())}–{int(region.year.max())} | Mean ± SD (model period)</div>

        <div class="p2f-grid">{cards}</div>

        <div class="p2f-note">↑ Significant increase &nbsp; ↓ Significant decrease &nbsp; ↔ No significant trend &nbsp; (p &lt; 0.05)</div>
        <div class="p2f-footnote">SST and chlorophyll trends: 1998–2025. Other annual indicators: {int(region.year.min())}–{int(region.year.max())}. Fishing effort: mean monthly apparent fishing hours, 2012–2024. Percentile among MEOWs with available data.</div>
    </div>
    '''


def show_region_map(region_name, map_variable='Catch', zoom=0.70):
    map_df = _data.copy()
    map_df['Baseline_predicted'] = _alpha * map_df.NPP * _wet_weight * _TE ** (map_df.TL - 1)
    map_df['Phyto2Fish_predicted'] = map_df['Predicted']

    if map_variable == 'SST' and 'SST' not in map_df.columns:
        map_df = map_df.merge(_sst.melt('year', var_name='MEOW', value_name='SST'), on=['year', 'MEOW'], how='left')

    regional_means = map_df.groupby('MEOW', as_index=False)[map_variable].mean()
    map_data = _world.merge(regional_means, left_on='ECOREGION', right_on='MEOW', how='left')
    selected = map_data[map_data.ECOREGION == region_name]

    xmin, ymin, xmax, ymax = selected.total_bounds
    dx, dy = xmax - xmin, ymax - ymin
    pad = max(dx, dy) * zoom
    extent = [xmin - pad, xmax + pad, ymin - pad, ymax + pad]

    log_scale = map_variable not in ['SST', 'Delta_L', 'Log_bias']
    cmap = 'RdBu_r' if map_variable == 'Log_bias' else 'viridis'
    kwargs = {'vmin': -2, 'vmax': 2} if map_variable == 'Log_bias' else {}

    norm = None
    if log_scale:
        vals = map_data[map_variable].dropna()
        vals = vals[vals > 0]
        if len(vals) > 0: norm = mcolors.LogNorm(vmin=vals.min(), vmax=vals.max())

    fig, ax = plt.subplots(figsize=(8.5, 6.2), subplot_kw={'projection': ccrs.PlateCarree()})
    map_data.plot(column=map_variable, ax=ax, cmap=cmap, norm=norm, legend=True, missing_kwds={'color': '#e5e5e5'}, legend_kwds={'label': map_variable, 'shrink': 0.7}, transform=ccrs.PlateCarree(), **kwargs)
    ax.add_feature(cfeature.LAND, facecolor='#e0e0e0', edgecolor='#888888', linewidth=0.4, zorder=3)
    selected.boundary.plot(ax=ax, color='black', linewidth=2.5, transform=ccrs.PlateCarree(), zorder=5)
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.set_title(f'{region_name} | {map_variable.replace("_", " ")}', fontsize=14, fontweight='bold', pad=12)
    ax.coastlines(resolution='50m', linewidth=0.5)
    ax.gridlines(draw_labels={'bottom': 'x', 'left': 'y'}, alpha=0.2, linestyle='--')
    fig.subplots_adjust(left=0.04, right=0.88, top=0.90, bottom=0.10)
    return fig
