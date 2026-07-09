from __future__ import annotations

from examples.layout_demo import styles
from solid_tk import component
from solid_tk import layout
from solid_tk import style
from solid_tk import tk
from solid_tk import ttk
from solid_tk.control import For

Page = style.component(layout.VStack, styles.page)
PanelStack = style.component(layout.VStack, styles.panel)
PanelTitle = style.component(tk.Label, styles.panel_title)
TitleLabel = style.component(tk.Label, styles.title)
SwatchLabel = style.component(tk.Label, styles.swatch)
GrowLabel = style.component(tk.Label, styles.grow_label)
GrowFrame = style.component(tk.Frame, styles.grow_frame)
CenteredItem = style.component(layout.Item, styles.center_item)
StartItem = style.component(layout.Item, styles.start_item)
GrowItem = style.component(layout.Item, styles.grow_item)
StartRow = style.component(layout.HStack, styles.start_row)
LooseRow = style.component(layout.HStack, styles.loose_row)
SampleRow = style.component(layout.HStack, styles.sample_row)
GrowRow = style.component(layout.HStack, styles.grow_row)
CenterFill = style.component(layout.HStack, styles.center_fill)
ButtonRow = style.component(layout.HStack, styles.button_row)

IMAGE_TILES = (
    {"id": "north", "title": "North ridge", "tone": "#bfdbfe"},
    {"id": "east", "title": "East window", "tone": "#bbf7d0"},
    {"id": "south", "title": "South field", "tone": "#fed7aa"},
    {"id": "west", "title": "West desk", "tone": "#ddd6fe"},
)


def swatch(text: str, color: str, *, swatch_style=None, width: int | None = None):
    swatch_props = style.merge(swatch_style, {"bg": color}).props()
    if width is not None:
        swatch_props["width"] = width
    return SwatchLabel(text=text, **swatch_props)


def panel(title: str, *children, **props):
    panel_children = [
        child if hasattr(child, "_stack_layout") else StartItem(child)
        for child in children
    ]
    return PanelStack(
        CenteredItem(PanelTitle(text=title)),
        *panel_children,
        **props,
    )


def title():
    return CenteredItem(TitleLabel(text="Layout demo"))


def gap_align_example():
    return panel(
        "gap + align",
        StartRow(
            swatch("start", "#bfdbfe"),
            swatch("center", "#bbf7d0"),
            swatch("end", "#fde68a"),
        ),
        LooseRow(
            swatch("loose", "#fecaca"),
            swatch("row", "#ddd6fe"),
            swatch("spacing", "#bae6fd"),
        ),
    )


def padding_example():
    return panel(
        "padding is frame padx/pady sugar",
        SampleRow(
            layout.VStack(
                tk.Label(text="padding=8"),
                swatch("same x/y", "#c7d2fe"),
                **style.merge(styles.sample_box, styles.soft_blue),
            ),
            layout.VStack(
                tk.Label(text="padding=(18, 6)"),
                swatch("wide x", "#fed7aa"),
                **style.merge(
                    styles.sample_box,
                    styles.wide_sample_box,
                    styles.soft_orange,
                ),
            ),
            layout.VStack(
                tk.Label(text="padding=8, padx=24"),
                swatch("padx wins", "#a7f3d0"),
                **style.merge(
                    styles.sample_box,
                    styles.wide_x_sample_box,
                    styles.soft_green,
                ),
            ),
        ),
    )


def grow_label():
    return GrowFrame(
        CenterFill(
            GrowLabel(text="grow=True, fill='both'"),
            pack={"fill": "both", "expand": True},
        ),
    )


def grow_example_row():
    return GrowRow(
        swatch("fixed", "#fde68a", swatch_style=styles.compact_swatch),
        GrowItem(grow_label()),
        swatch("fixed", "#fecaca", swatch_style=styles.compact_swatch),
    )


def grow_example():
    return GrowItem(
        panel(
            "Item overrides one child",
            GrowItem(grow_example_row()),
            fill="both",
        ),
    )


def grid_tile(tile):
    return layout.VStack(
        swatch("", tile["tone"], width=18),
        tk.Label(text=tile["title"], style=styles.image_title),
        tk.Label(text="placed by layout.Grid", style=styles.image_meta),
        style=styles.image_tile,
    )


def grid_style_example():
    return panel(
        "For children with grid styles",
        layout.Grid(
            For(IMAGE_TILES, grid_tile, key=lambda tile: tile["id"]),
            layout.GridItem(
                tk.Label(text="weighted columns + GridItem span", style=styles.image_meta),
                style=styles.wide_image_tile,
            ),
            style=styles.image_grid,
            pack={"fill": "x"},
        ),
    )


def actions():
    return ButtonRow(
        ttk.Button(text="OK"),
        ttk.Button(text="Cancel"),
    )


@component
def layout_demo(props):
    return Page(
        title(),
        gap_align_example(),
        padding_example(),
        grow_example(),
        grid_style_example(),
        actions(),
    )
