# /// script
# dependencies = [
#     "altair==6.0.0",
#     "marimo",
#     "numpy==2.3.5",
#     "pandas==3.0.0",
#     "plotly==6.5.2",
# ]
# ///

import marimo

__generated_with = "0.19.8"
app = marimo.App(
    width="medium",
    css_file="/usr/local/_marimo/custom.css",
    auto_download=["html"],
)


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import altair as alt
    import itertools

    return alt, mo, np, pd


@app.cell(hide_code=True)
def _(mo):
    fileInput = mo.ui.file(label="input data")
    fileInput
    return (fileInput,)


@app.cell(hide_code=True)
def _(fileInput, np, pd):
    # Example CSV loading (replace with your file upload or URL)
    # For demonstration, we'll generate a sample DataFrame with the described columns and ranges
    np.random.seed(42)

    switch_options = ["", "Hostile,", "Passive,", "Ambient,", "Water,",
                      "Hostile, Passive", "Hostile, Ambient", "Hostile, Water",
                      "Passive, Ambient", "Passive, Water", "Ambient, Water",
                      "Hostile, Passive, Ambient", "Hostile, Passive, Water",
                      "Hostile, Ambient, Water", "Passive, Ambient, Water",
                      "Hostile, Passive, Ambient, Water"]

    n_rows = 500
    if fileInput.name(0) is not None:
        pd.read_csv(fileInput.contents(0))
    data = pd.DataFrame({
        'limit': np.random.randint(1, 1001, n_rows,),
        'delay': np.random.randint(0, 6001, n_rows),
        'advances': np.random.randint(1, 100, n_rows),
        'RD': np.random.randint(2, 33, n_rows),
        'width': np.random.choice([0, 1], n_rows),
        'switches': np.random.choice(switch_options, n_rows)
    })
    VALID = ["Hostile", "Passive", "Ambient", "Water"]

    def fix_switches(s):
        if not s:
            return ""
        parts = [p.strip() for p in s.split(",") if p.strip()]
        parts = [p for p in parts if p in VALID]
        parts.sort()
        return ", ".join(parts)

    data["switches"] = data["switches"].astype(str).apply(fix_switches)

    # data
    # For real use, replace above with:
    # file = mo.ui.file(label="Upload CSV")
    # if file.value is not None:
    #     data = pd.read_csv(file.value)
    return (data,)


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    # UI for selecting base switches (Hostile, Passive, Ambient, Water)
    base_switches = ['Hostile', 'Passive', 'Ambient', 'Water']
    switch_hostile, switch_passive, switch_ambient, switch_water = [mo.ui.checkbox(label=s, value=False) for s in base_switches]

    # UI for width toggle
    width_toggle = mo.ui.checkbox(value = False, label="Width")
    # UI for selecting x, y, color, z axes (excluding width and switches for axes)
    axis_options = ['limit', 'delay', 'advances', 'RD','switches']


    switch_filter = mo.ui.checkbox(value=False,label="Filter switch")
    x_axis = mo.ui.dropdown(axis_options, value='limit', label='X Axis')
    y_axis = mo.ui.dropdown(axis_options, value='delay', label='Y Axis')
    z_axis = mo.ui.dropdown(axis_options, value='RD', label='Z Axis (3D)')

    color_check = mo.ui.checkbox(value=True)
    color_axis = mo.ui.dropdown(axis_options, value='advances', label='Color')
    average_check = mo.ui.checkbox()
    average_axis = mo.ui.dropdown(axis_options, value='advances',label='Average')
    # Layout for UI
    highDelayThreshold = mo.ui.slider(start=0,stop=6000,value=5500,label="High Delay Threshold")
    mo.vstack([
        mo.md("**Select base switches:**"),
        switch_filter,
        mo.hstack([switch_hostile, switch_passive, switch_ambient, switch_water]),
        mo.center(item=width_toggle),
        mo.hstack([average_check,average_axis, color_check,color_axis],justify="center"),
        mo.hstack([x_axis, y_axis, z_axis],justify="center",gap=5),
        highDelayThreshold
    ])
    return (
        average_axis,
        average_check,
        base_switches,
        color_axis,
        color_check,
        highDelayThreshold,
        switch_ambient,
        switch_filter,
        switch_hostile,
        switch_passive,
        switch_water,
        width_toggle,
        x_axis,
        y_axis,
        z_axis,
    )


@app.cell(hide_code=True)
def _(
    alt,
    average_axis,
    average_check,
    base_switches,
    color_axis,
    color_check,
    data,
    switch_ambient,
    switch_filter,
    switch_hostile,
    switch_passive,
    switch_water,
    width_toggle,
    x_axis,
    y_axis,
    z_axis,
):
    selected_switches = {
        s for s, cb in zip(
            base_switches,
            [switch_hostile, switch_passive, switch_ambient, switch_water]
        )
        if cb.value
    }


    def switches_to_string(selected_switches):
        if not selected_switches:
            return ""

        ordered = [s for s in base_switches if s in selected_switches]
        return ", ".join(ordered)

    def filter_data(df, selected_switches, width_value):
        # Width always filters
        df = df[df["width"] == width_value]

        # Ignore switch filtering entirely
        if not switch_filter.value:
            return df

        switch_string = switches_to_string(selected_switches)

        # ALL switches selected → empty string NOT allowed → return empty
        if switch_string == "Hostile, Passive, Ambient, Water":
            return df.iloc[0:0]

        # Otherwise filter by the canonical string
        return df[df["switches"] == switch_string]


    filtered_data = filter_data(data, selected_switches, width_toggle.value)

    if average_check.value:
        group_col = average_axis.value  # e.g., "RD" or another selected axis

        # Only numeric plotting axes to average
        axes_to_average = [x_axis.value, y_axis.value, z_axis.value]

        # Make a copy to preserve original columns
        averaged_data = filtered_data.copy()

        # Group by the selected axis and average only the plotting axes
        averaged_data[axes_to_average] = (
            filtered_data
            .groupby(group_col, as_index=False)[axes_to_average]
            .transform("mean")[axes_to_average]
        )
    else:
        averaged_data = filtered_data
    # After filtering and averaging
    averaged_data = averaged_data.copy()  # safety

    # Replace empty switch strings with "None"
    averaged_data["switches"] = averaged_data["switches"].replace("", "None")



    if not color_check.value:
        color_value = alt.value("steelblue")
        color_scale = None 
        colorAxis_value = None
    else:
        colorAxis_value = color_axis.value
        color_scale = [
                "#E70000", "#FF8C00", "#FFEF00",
                "#00811F", "#0044FF", "#760089"
            ]
        if color_axis.value == "switches":
            # DISCRETE / NOMINAL
            color_value = alt.Color(
                "switches:N",
                scale=alt.Scale(),
                legend=alt.Legend(title="Switches"),
            )

        else:

            # CONTINUOUS / NUMERIC
            color_value = alt.Color(
                color_axis.value,
                type="quantitative",
                scale=alt.Scale(
                    range=[
                        "#E70000",
                        "#FF8C00",
                        "#FFEF00",
                        "#00811F",
                        "#0044FF",
                        "#760089",
                    ]
                ),
                legend=alt.Legend(
                    title=color_axis.value,
                    type="gradient",
                ),
            )

    # averaged_data


    # filtered_data
    return averaged_data, colorAxis_value, color_scale, color_value


@app.cell(hide_code=True)
def _(alt, averaged_data, color_axis, color_value, mo, x_axis, y_axis):
    # Create the interactive chart
    chart_2d = mo.ui.altair_chart(
        alt.Chart(averaged_data)
        .mark_point()
        .encode(
            x=x_axis.value,
            y=y_axis.value,
            color=color_value,
            tooltip=[x_axis.value, y_axis.value, color_axis.value]
        )
        .interactive()
    )

    chart_2d  # <-- display it in this cell
    return


@app.cell(hide_code=True)
def interactive_3d_chart(
    averaged_data,
    colorAxis_value,
    color_scale,
    mo,
    x_axis,
    y_axis,
    z_axis,
):
    import plotly.express as px

    chart_3d = mo.ui.plotly(
        px.scatter_3d(
            averaged_data,
            x=x_axis.value,
            y=y_axis.value,
            z=z_axis.value,
            color=colorAxis_value,
            color_continuous_scale= color_scale,
            hover_data=["width"],
        )
    )

    chart_3d
    return (px,)


@app.cell(hide_code=True)
def _(data, highDelayThreshold, mo, px):


    summary_data = (
        data
        .groupby(["limit", "width"])
        .agg(
            averageDelay=("delay", "mean"),
            highDelays=("delay", lambda x: (x >= highDelayThreshold.value).sum())
        )
        .reset_index()
    )

    summary_plots = []

    for width_value1 in [0, 1]:
        subset11 = summary_data[summary_data["width"] == width_value1]
        if subset11.empty:
            continue

        plot = mo.ui.plotly(
            px.scatter(
                subset11,
                x="limit",
                y="averageDelay",
                color="highDelays",
                color_continuous_scale="Viridis",
                labels={
                    "limit": "Limit",
                    "averageDelay": "Average Delay",
                    'highDelays': f'High Delays (>={highDelayThreshold.value})',
                },
                title=f"Summary (width={width_value1})",
            )
        )

        summary_plots.append(plot)

    mo.vstack(summary_plots)
    return


@app.cell(hide_code=True)
def _(data, highDelayThreshold, mo, np, pd, px):
    polyOrder = 3

    rd_data = (
        data
        .groupby(["RD", "width"])
        .agg(
            avgDelay=("delay", "mean"),
            highDelayCount=("delay", lambda x: (x >= highDelayThreshold.value).sum())
        )
        .reset_index()
        .sort_values("RD")
    )

    rd_plots = []

    for width_value3 in [0, 1]:
        subset1 = rd_data[rd_data["width"] == width_value3]
        if len(subset1) < 2:
            continue

        xFit = np.linspace(subset1["RD"].min(), subset1["RD"].max(), 300)
        fitOrder = min(polyOrder, len(subset1) - 1)

        fit_avg = np.polyval(
            np.polyfit(subset1["RD"], subset1["avgDelay"], fitOrder),
            xFit,
        )
        fit_high = np.polyval(
            np.polyfit(subset1["RD"], subset1["highDelayCount"], fitOrder),
            xFit,
        )

        fit_df = pd.DataFrame({
            "RD": xFit,
            "avgFit": fit_avg,
            "highFit": fit_high,
        })

        scatter_avg = px.scatter(
            subset1,
            x="RD",
            y="avgDelay",
            labels={"RD": "Render Distance", "avgDelay": "Average Delay"},
        )

        scatter_avg.add_scatter(
            x=fit_df["RD"],
            y=fit_df["avgFit"],
            mode="lines",
            name="Avg Delay Fit",
        )

        scatter_avg.add_scatter(
            x=subset1["RD"],
            y=subset1["highDelayCount"],
            mode="markers",
            name="High Delays",
            yaxis="y2",
        )

        scatter_avg.add_scatter(
            x=fit_df["RD"],
            y=fit_df["highFit"],
            mode="lines",
            name="High Delays Fit",
            yaxis="y2",
        )

        scatter_avg.update_layout(
            title=f"Render Distance vs Delay (width={width_value3})",
            yaxis=dict(title="Average Delay"),
            yaxis2=dict(
                title=f'High Delays (>={highDelayThreshold.value})',
                overlaying="y",
                side="right",
            ),
        )

        rd_plots.append(mo.ui.plotly(scatter_avg))

    mo.vstack(rd_plots)
    return


@app.cell(hide_code=True)
def _(data, mo, px):
    scatter_data = data.copy()
    scatter_data["delay"] = scatter_data["delay"].clip(upper=6000)

    plots_3d = []

    for width_value in [0, 1]:
        subset = scatter_data[scatter_data["width"] == width_value]
        if subset.empty:
            continue

        chart_3 = mo.ui.plotly(
            px.scatter_3d(
                subset,
                x="limit",
                y="RD",
                z="delay",
                color="delay",
                color_continuous_scale="Viridis",
                range_x=[1, 1000],
                range_y=[2, 32],
                range_z=[0, 6000],
                hover_data=["width", "advances", "switches"],
                title=f"3D Delay Scatter (width={width_value})",
            )
        )

        plots_3d.append(chart_3)

    mo.vstack(plots_3d)
    return


if __name__ == "__main__":
    app.run()
