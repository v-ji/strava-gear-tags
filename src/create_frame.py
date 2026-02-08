from PIL import Image, ImageDraw, ImageFont
import os # Added import

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
        "logo_path": "src/assets/brands/nike.png",
    },
}


for brand_name in brand_config.keys():
    logo = Image.open(brand_config[brand_name]["logo_path"])

    # Create a new RGBA image (work in full color with alpha)
    image = Image.new("RGBA", (296, 152), (255, 255, 255, 255))  # white background

    if brand_name == "Canyon":
        logo.thumbnail((image.height, image.height), resample=Image.NEAREST)
        logo = logo.rotate(-90, expand=True)
        image.paste(logo, (0, 0), logo)

    if brand_name == "Adidas" or brand_name == "Nike":
        logo.thumbnail((90, 90), resample=Image.NEAREST)
        pad_x, pad_y = 4, 4
        image.paste(
            logo,
            (image.width - logo.width - pad_x, image.height - logo.height - pad_y),
            logo,
        )

    image.save(f"src/assets/frames/{brand_name.lower()}.png")
