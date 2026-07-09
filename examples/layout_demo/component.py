from __future__ import annotations

from examples.layout_demo import styles
from solid_tk import component
from solid_tk import style
from solid_tk import tk
from solid_tk import ttk

Page = style.component(tk.VStack, styles.page)
PanelStack = style.component(tk.VStack, styles.panel)
PanelTitle = style.component(tk.Label, styles.panel_title)
TitleLabel = style.component(tk.Label, styles.title)
SwatchLabel = style.component(tk.Label, styles.swatch)
GrowLabel = style.component(tk.Label, styles.grow_label)
GrowFrame = style.component(tk.Frame, styles.grow_frame)
CenteredItem = style.component(tk.Item, styles.center_item)
StartItem = style.component(tk.Item, styles.start_item)
GrowItem = style.component(tk.Item, styles.grow_item)
StartRow = style.component(tk.HStack, styles.start_row)
LooseRow = style.component(tk.HStack, styles.loose_row)
SampleRow = style.component(tk.HStack, styles.sample_row)
GrowRow = style.component(tk.HStack, styles.grow_row)
CenterFill = style.component(tk.HStack, styles.center_fill)
ButtonRow = style.component(tk.HStack, styles.button_row)


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
            tk.VStack(
                tk.Label(text="padding=8"),
                swatch("same x/y", "#c7d2fe"),
                **style.merge(styles.sample_box, styles.soft_blue),
            ),
            tk.VStack(
                tk.Label(text="padding=(18, 6)"),
                swatch("wide x", "#fed7aa"),
                **style.merge(
                    styles.sample_box,
                    styles.wide_sample_box,
                    styles.soft_orange,
                ),
            ),
            tk.VStack(
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
        actions(),
    )
