import random

def random_image_url(width=300, height=200):
    img_id = random.randint(1, 1000)
    return f"https://picsum.photos/seed/{img_id}/{width}/{height}"
