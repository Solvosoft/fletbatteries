import random

from fletbatteries.utils import (  # noqa: F401
    close_dialog,
    is_mounted,
    safe_update,
    show_snackbar,
    text_with_truncate,
    truncate_str,
)


def random_image_url(width=300, height=200):
    img_id = random.randint(1, 1000)
    return f"https://picsum.photos/seed/{img_id}/{width}/{height}"

