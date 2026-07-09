from __future__ import annotations

from solid_tk import style

page = style.define("page", padding=12, gap=10, bg="#e5e7eb")
title = style.define("title", font=("TkDefaultFont", 13, "bold"))
panel = style.define("panel", bg="#f8fafc", relief="ridge", bd=1, padding=10, gap=8)
panel_title = style.define("panel_title", font=("TkDefaultFont", 10, "bold"))

center_item = style.define("center_item", fill="none", align="center")
start_item = style.define("start_item", fill="none", align="start")
grow_item = style.define("grow_item", grow=True, fill="both")

swatch = style.define(
    "swatch",
    fg="#111827",
    padx=8,
    pady=4,
    width=14,
    relief="solid",
    bd=1,
)
compact_swatch = style.define("compact_swatch", width=10)

soft_blue = style.define("soft_blue", bg="#eef2ff")
soft_orange = style.define("soft_orange", bg="#fff7ed")
soft_green = style.define("soft_green", bg="#ecfdf5")

sample_box = style.define("sample_box", gap=6, padding=8)
wide_sample_box = style.define("wide_sample_box", padding=(18, 6))
wide_x_sample_box = style.define("wide_x_sample_box", padx=24)

sample_row = style.define("sample_row", gap=10, align="start", bg="#f8fafc")
loose_row = style.define("loose_row", gap=18, bg="#f8fafc")
start_row = style.define("start_row", gap=8, align="start", bg="#f8fafc")
grow_row = style.define("grow_row", gap=8, fill="both", bg="#f8fafc")
grow_frame = style.define(
    "grow_frame",
    bg="#0f766e",
    width=220,
    height=46,
    relief="sunken",
    bd=1,
)
grow_label = style.define("grow_label", bg="#d1fae5", padx=8, pady=8)
center_fill = style.define(
    "center_fill",
    align="center",
    fill="both",
    grow=True,
    bg="#0f766e",
)
button_row = style.define("button_row", gap=6, align="center")

image_grid = style.define(
    "image_grid",
    columns=2,
    gap=4,
    sticky="nsew",
    bg="#f8fafc",
)
image_tile = style.define(
    "image_tile",
    bg="#ffffff",
    relief="solid",
    bd=1,
    padx=8,
    pady=8,
)
image_title = style.define("image_title", bg="#ffffff", font=("TkDefaultFont", 9, "bold"))
image_meta = style.define("image_meta", bg="#ffffff", fg="#475569")
