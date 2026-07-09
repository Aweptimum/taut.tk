from __future__ import annotations

from examples.layout_demo.styles import styles
from solid_tk import component
from solid_tk import style
from solid_tk.widgets import Button
from solid_tk.widgets import Frame
from solid_tk.widgets import HStack
from solid_tk.widgets import Item
from solid_tk.widgets import Label
from solid_tk.widgets import VStack

Page = style.component(VStack, styles["page"])
PanelStack = style.component(VStack, styles["panel"])
PanelTitle = style.component(Label, styles["panel_title"])
TitleLabel = style.component(Label, styles["title"])
SwatchLabel = style.component(Label, styles["swatch"])
GrowLabel = style.component(Label, styles["grow_label"])
GrowFrame = style.component(Frame, styles["grow_frame"])
CenteredItem = style.component(Item, styles["center_item"])
StartItem = style.component(Item, styles["start_item"])
GrowItem = style.component(Item, styles["grow_item"])
StartRow = style.component(HStack, styles["start_row"])
LooseRow = style.component(HStack, styles["loose_row"])
SampleRow = style.component(HStack, styles["sample_row"])
GrowRow = style.component(HStack, styles["grow_row"])
CenterFill = style.component(HStack, styles["center_fill"])
ButtonRow = style.component(HStack, styles["button_row"])


def swatch(text: str, color: str, *, swatch_style=None, width: int | None = None):
    swatch_props = style.merge(swatch_style, {"bg": color})
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
            VStack(
                Label(text="padding=8"),
                swatch("same x/y", "#c7d2fe"),
                **style.merge(styles["sample_box"], styles["soft_blue"]),
            ),
            VStack(
                Label(text="padding=(18, 6)"),
                swatch("wide x", "#fed7aa"),
                **style.merge(
                    styles["sample_box"],
                    styles["wide_sample_box"],
                    styles["soft_orange"],
                ),
            ),
            VStack(
                Label(text="padding=8, padx=24"),
                swatch("padx wins", "#a7f3d0"),
                **style.merge(
                    styles["sample_box"],
                    styles["wide_x_sample_box"],
                    styles["soft_green"],
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
        swatch("fixed", "#fde68a", swatch_style=styles["compact_swatch"]),
        GrowItem(grow_label()),
        swatch("fixed", "#fecaca", swatch_style=styles["compact_swatch"]),
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
        Button(text="OK"),
        Button(text="Cancel"),
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
