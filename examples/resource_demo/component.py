from __future__ import annotations

import time
import urllib.request
from io import BytesIO

from PIL import Image
from PIL import ImageTk

from solid_tk import component
from solid_tk.reactive import create_memo
from solid_tk.reactive import create_signal
from solid_tk.resource import SourceInfo
from solid_tk.resource import create_resource
from solid_tk.runtime import to_ui
from solid_tk.widgets import Button
from solid_tk.widgets import HStack
from solid_tk.widgets import Label
from solid_tk.widgets import VStack

DATASET_IMAGE_URL = (
    "https://raw.githubusercontent.com/scikit-image/scikit-image/"
    "v0.22.0/skimage/data/astronaut.png"
)

PREVIEW_SIZE = (300, 300)


def progress_bar(value: int) -> str:
    filled = max(0, min(20, value // 5))
    return f"[{'#' * filled}{'.' * (20 - filled)}] {value:>3}%"


@component
def resource_demo(props):
    progress, set_progress = create_signal(0)
    dispatch = to_ui()

    def fetch_image(source: str, info: SourceInfo[bytes, str]) -> bytes:
        dispatch(lambda: set_progress(4))
        for step in (12, 20, 28):
            time.sleep(0.25)
            dispatch(lambda step=step: set_progress(step))

        with urllib.request.urlopen(source, timeout=15) as response:
            total = int(response.headers.get("Content-Length") or "0")
            loaded = 0
            chunks: list[bytes] = []
            while chunk := response.read(16_384):
                chunks.append(chunk)
                loaded += len(chunk)
                if total:
                    next_progress = min(92, 30 + int((loaded / total) * 62))
                    dispatch(lambda next_progress=next_progress: set_progress(next_progress))

        time.sleep(0.35)
        dispatch(lambda: set_progress(100))
        return b"".join(chunks)

    image, actions = create_resource(fetch_image, None, DATASET_IMAGE_URL)
    mutate, refetch = actions

    photo = create_memo(
        lambda: (
            resized_photo(image.latest())
            if image.latest() is not None
            else None
        )
    )

    def retry() -> None:
        set_progress(0)
        refetch("button")

    def clear() -> None:
        set_progress(0)
        mutate(None)

    return VStack(
        Label(text="Resource demo"),
        Label(
            text=lambda: (
                "Loading image..."
                if image.loading()
                else "Fetch failed"
                if image.error()
                else "Ready"
            )
        ),
        Label(
            text=lambda: (
                progress_bar(progress())
                if image.loading() or image.latest() is not None
                else ""
            ),
            font=("Courier", 12),
        ),
        Label(
            image=lambda: photo() or "",
            text=lambda: "" if image.latest() is not None else "image pending",
            width=lambda: PREVIEW_SIZE[0] if image.latest() is not None else 24,
            height=lambda: PREVIEW_SIZE[1] if image.latest() is not None else 2,
            relief="sunken",
            bd=1,
        ),
        HStack(
            Button(text="Refetch", on_click=retry),
            Button(text="Clear", on_click=clear),
        ),
        Label(text=lambda: f"state={image.state()} loading={image.loading()}"),
        Label(text=lambda: f"error={image.error()}" if image.error() else ""),
        padx=8,
        pady=8,
    )


def resized_photo(data: bytes) -> ImageTk.PhotoImage:
    image = Image.open(BytesIO(data))
    image.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)
