import os

from PIL import Image

# Define a base path for assets relative to the current script
ASSETS_BASE_PATH = os.path.join(os.path.dirname(__file__), "assets")

brand_config = {
    "Canyon": {
        "logo_path": os.path.join(ASSETS_BASE_PATH, "brands", "canyon.png"),
    },
    "Adidas": {
        "logo_path": os.path.join(ASSETS_BASE_PATH, "brands", "adidas.png"),
    },
    "Nike": {
        "logo_path": os.path.join(ASSETS_BASE_PATH, "brands", "nike.png"),
    },
    "PUMA": {
        "logo_path": os.path.join(ASSETS_BASE_PATH, "brands", "puma.png"),
    },
}


for brand_name in brand_config.keys():
    print(f"Processing brand: {brand_name}")
    logo = Image.open(brand_config[brand_name]["logo_path"])

    # Create a new RGBA image (work in full color with alpha)
    image = Image.new("RGBA", (296, 152), (255, 255, 255, 255))  # white background

    if brand_name == "Canyon":
        logo.thumbnail((image.height, image.height), resample=Image.NEAREST)
        logo = logo.rotate(-90, expand=True)
        image.paste(logo, (0, 0), logo)

    else:
        logo.thumbnail((90, 90), resample=Image.NEAREST)
        pad_x, pad_y = 4, 4

        is_transparent = logo.mode in ("RGBA", "LA") or (
            logo.mode == "P" and "transparency" in logo.info
        )
        image.paste(
            logo,
            (image.width - logo.width - pad_x, image.height - logo.height - pad_y),
            logo if is_transparent else None,
        )

    image.save(f"src/assets/frames/{brand_name.lower()}.png")
