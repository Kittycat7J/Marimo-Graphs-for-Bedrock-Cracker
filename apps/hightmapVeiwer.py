# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.19.9",
#     "matplotlib==3.10.8",
#     "numpy==2.3.5",
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
    import json
    import sys
    import plotly.graph_objects as go
    import plotly.express as px
    import plotly.colors as pc
    import numpy as np
    import marimo as mo
    from pathlib import Path

    return go, json, mo, np, pc


@app.cell(hide_code=True)
def _():
    CHUNK_RADIUS = 7  # 15x15 chunks
    CHUNK_SIZE = 16
    return CHUNK_RADIUS, CHUNK_SIZE


@app.cell(hide_code=True)
def _(CHUNK_RADIUS, CHUNK_SIZE, file_select, json, np):
    def load_grid(file):

        json_text = file_select.contents(0)
        data = json.loads(json_text)

        size = (CHUNK_RADIUS * 2 + 1) * CHUNK_SIZE

        height_grid = np.full((size, size), np.nan)
        id_grid = np.full((size, size), np.nan)
        data_grid = np.full((size, size), np.nan)
        section_grid = np.full((size, size), np.nan)

        for chunk_key, chunk in data.get("chunks", {}).items():
            try:
                cx, cz = map(int, chunk_key.split(","))
            except ValueError:
                continue

            if not (-CHUNK_RADIUS <= cx <= CHUNK_RADIUS and -CHUNK_RADIUS <= cz <= CHUNK_RADIUS):
                continue

            base_x = (cx + CHUNK_RADIUS) * CHUNK_SIZE
            base_z = (cz + CHUNK_RADIUS) * CHUNK_SIZE

            # sectionBase can be int or { value: int }
            section_raw = chunk.get("sectionBase", 0)
            section_val = section_raw.get("value", section_raw) if isinstance(section_raw, dict) else section_raw

            for pos, block in chunk.get("heightmap", {}).items():
                try:
                    lx, lz = map(int, pos.split(","))
                except ValueError:
                    continue

                gx = base_x + lx
                gz = base_z + lz

                if isinstance(block, dict):
                    y_val = block.get("y", 0)
                    block_id = block.get("id", 0)
                    data_val = block.get("data", 0)
                else:
                    y_val = block
                    block_id = 0
                    data_val = 0

                height_grid[gz, gx] = y_val
                id_grid[gz, gx] = block_id
                data_grid[gz, gx] = data_val
                section_grid[gz, gx] = section_val

        return height_grid, id_grid, data_grid, section_grid

    return (load_grid,)


@app.cell(hide_code=True)
def _(go, np, pc):
    def draw(height_grid, id_grid, data_grid, section_grid, center_chunk=None):
        size = height_grid.shape[0]

        # Optional subchunk Y offset
        subchunk_y_offset = 16 * (center_chunk[1] if center_chunk else 0)

        # Determine offsets for world coordinates
        offset_x = (center_chunk[0] if center_chunk else 0) * 16
        offset_z = (center_chunk[2] if center_chunk else 0) * 16

        xs_world, zs_world, heights, hover_texts = [], [], [], []

        # ----------------------------
        # Collect block data
        # ----------------------------
        for y_idx in range(size):
            for x_idx in range(size):
                h = height_grid[y_idx, x_idx]
                if np.isnan(h):
                    continue

                bid = id_grid[y_idx, x_idx]
                d = data_grid[y_idx, x_idx]
                s = section_grid[y_idx, x_idx]

                chunk_x = (x_idx // 16) - 7
                chunk_z = (y_idx // 16) - 7
                local_x = x_idx % 16
                local_z = y_idx % 16
            
                # Apply center_chunk offset
                center_x = center_chunk[0] if center_chunk else 0
                center_z = center_chunk[2] if center_chunk else 0
            
                world_x = (chunk_x - center_x) * 16 + local_x
                world_z = (chunk_z - center_z) * 16 + local_z
                display_height = h + subchunk_y_offset


                xs_world.append(world_x)
                zs_world.append(-world_z)
                heights.append(display_height)

                world_chunk_x = chunk_x - center_x
                world_chunk_z = chunk_z - center_z
            
                hover_texts.append(
                    f"X={world_x} Z={world_z}<br>"
                    f"Height(Y)={int(display_height)}<br>"
                    f"ID={int(bid)} DV={int(d)}<br>"
                    f"Chunk=({world_chunk_x},{world_chunk_z}) LC={int(s)+subchunk_y_offset}"
                )


        # ----------------------------
        # Collect sectionBase per chunk
        # ----------------------------
        chunk_vals = {}
        for y_idx in range(size):
            for x_idx in range(size):
                sec = section_grid[y_idx, x_idx]
                if np.isnan(sec):
                    continue

                cx = (x_idx // 16) - 7
                cz = (y_idx // 16) - 7

                if (cx, cz) not in chunk_vals:
                    chunk_vals[(cx, cz)] = sec

        sec_min = min(chunk_vals.values()) if chunk_vals else 0
        sec_max = max(chunk_vals.values()) if chunk_vals else 1

        def sec_to_color(v, min_t=0.3):
            if sec_max == sec_min:
                t = 1.0
            else:
                t = (v - sec_min) / (sec_max - sec_min)
            t = min_t + (1 - min_t) * t
            return pc.sample_colorscale("Greys_r", [t])[0]

        # ----------------------------
        # Build figure
        # ----------------------------
        fig = go.Figure()

        # --- draw coloured chunk rectangles ---
        for (cx, cz), sec_val in chunk_vals.items():
            fig.add_shape(
                type="rect",
                x0=(cx - center_x) * 16,
                x1=(cx + 1 - center_x) * 16,
                y0=-(cz - center_z) * 16,
                y1=-(cz + 1 - center_z) * 16,
                fillcolor=sec_to_color(sec_val),
                opacity=0.2,
                line=dict(width=0),
                layer="below"
            )


        # --- height scatter ---
        fig.add_trace(go.Scatter(
            x=xs_world,
            y=zs_world,
            mode='markers',
            marker=dict(
                size=4,
                color=heights,
                colorscale='Agsunset',
                showscale=True,
                colorbar=dict(title="Height", thickness=15, len=0.7)
            ),
            hoverinfo='text',
            hovertext=hover_texts
        ))

        # --- chunk grid lines ---
        for i in range(-7, 8):
            fig.add_shape(type="line", x0=i*16 - offset_x, y0=-7*16 + offset_z,
                          x1=i*16 - offset_x, y1=7*16 + offset_z,
                          line=dict(color="gray", width=0.5))
            fig.add_shape(type="line", x0=-7*16 - offset_x, y0=-i*16 + offset_z,
                          x1=7*16 - offset_x, y1=-i*16 + offset_z,
                          line=dict(color="gray", width=0.5))

        fig.update_layout(
            title=dict(text="Heightmap Viewer", x=0.5),
            xaxis_title="West (-x)",
            yaxis_title="North (-z)",
            hovermode='closest',
            plot_bgcolor='black',
            dragmode='pan',
            yaxis=dict(scaleanchor="x", scaleratio=1),
            xaxis=dict(constrain="domain")
        )

        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)

        return fig


    return (draw,)


@app.cell(hide_code=True)
def _(mo):


    # Create UI elements
    file_select = mo.ui.file(
        filetypes=[".json"],
        label="Select JSON file",
        kind="button"
    )

    x_input = mo.ui.number(
        label="X coordinate",
        start=-100,
        stop=100,
        value=0,
        step=1
    )

    y_input = mo.ui.number(
        label="Y coordinate",
        value=0,
        step=1
    )

    z_input = mo.ui.number(
        label="Z coordinate",
        start=-100,
        stop=100,
        value=0,
        step=1
    )

    # Display the input controls
    mo.vstack([
        mo.md("## Heightmap Viewer"),
        mo.hstack([file_select, mo.md("Select a JSON file to visualize")]),
        mo.md("### Subchunk Coordinates"),
        mo.hstack([x_input, y_input, z_input]),
    ], align="start")
    return file_select, x_input, y_input, z_input


@app.cell(hide_code=True)
def _(draw, file_select, load_grid, mo, x_input, y_input, z_input):
    center_chunk = -x_input.value, y_input.value, -z_input.value
    graph = 'Please select a JSON'
    if file_select.name(0) is not None:
        height_grid, id_grid, data_grid, section_grid = load_grid(file_select)
        fig0 = draw(height_grid, id_grid, data_grid, section_grid, center_chunk=center_chunk)
        graph = mo.ui.plotly(fig0)
    graph

    return


if __name__ == "__main__":
    app.run()
