from __future__ import annotations

from solid_tk import style

styles = dict(
    page=style.define(padding=12, gap=10, bg="#e5e7eb"),
    title=style.define(font=("TkDefaultFont", 13, "bold")),
    panel=style.define(bg="#f8fafc", relief="ridge", bd=1, padding=10, gap=8),
    panel_title=style.define(font=("TkDefaultFont", 10, "bold")),
    center_item=style.define(fill="none", align="center"),
    start_item=style.define(fill="none", align="start"),
    grow_item=style.define(grow=True, fill="both"),
    swatch=style.define(fg="#111827", padx=8, pady=4, width=14, relief="solid", bd=1),
    compact_swatch=style.define(width=10),
    soft_blue=style.define(bg="#eef2ff"),
    soft_orange=style.define(bg="#fff7ed"),
    soft_green=style.define(bg="#ecfdf5"),
    sample_box=style.define(gap=6, padding=8),
    wide_sample_box=style.define(padding=(18, 6)),
    wide_x_sample_box=style.define(padx=24),
    sample_row=style.define(gap=10, align="start", bg="#f8fafc"),
    loose_row=style.define(gap=18, bg="#f8fafc"),
    start_row=style.define(gap=8, align="start", bg="#f8fafc"),
    grow_row=style.define(gap=8, fill="both", bg="#f8fafc"),
    grow_frame=style.define(
        bg="#0f766e",
        width=220,
        height=46,
        relief="sunken",
        bd=1,
    ),
    grow_label=style.define(bg="#d1fae5", padx=8, pady=8),
    center_fill=style.define(
        align="center",
        fill="both",
        grow=True,
        bg="#0f766e",
        pack={"fill": "both", "expand": True},
    ),
    button_row=style.define(gap=6, align="center"),
)