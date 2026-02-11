import logging
import os

from PIL import Image, ImageDraw, ImageFont

from .config import DINISH_FONT_PATH

# Define a base path for assets relative to the current script
ASSETS_BASE_PATH = os.path.join(os.path.dirname(__file__), "assets")

brand_config = {
    "Canyon": {
        "frame_path": os.path.join(ASSETS_BASE_PATH, "frames", "canyon.png"),
        "padding-left": 28,
    },
    "Adidas": {
        "frame_path": os.path.join(ASSETS_BASE_PATH, "frames", "adidas.png"),
        "padding-left": 4,
    },
    "Nike": {
        "frame_path": os.path.join(ASSETS_BASE_PATH, "frames", "nike.png"),
        "padding-left": 4,
    },
}


def create_gear_image(gear_stats: dict):
    """Generate an image for a specific piece of gear"""

    brand_name = gear_stats["brand_name"]
    specs = brand_config.get(brand_name)

    if not specs:
        logging.warning(f"Configuration not found for brand: {brand_name}")
        raise ValueError(f"Brand not configured: {brand_name}")

    # Create a new RGBA image (work in full color with alpha)
    image = Image.new("RGBA", (296, 152), (255, 255, 255, 255))  # white background

    # Load frame file
    frame = Image.open(specs["frame_path"])

    # Convert frame to RGBA and ensure it matches image size
    if frame.mode != "RGBA":
        frame = frame.convert("RGBA")
    if frame.size != image.size:
        frame = frame.resize(image.size, Image.LANCZOS)

    # Composite frame onto canvas
    image.alpha_composite(frame, (0, 0))

    # Initialise the drawing context
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"  # disable anti-aliasing

    FONT_SIZE = 34

    font_regular = ImageFont.truetype(
        os.path.join(DINISH_FONT_PATH, "DINish-Medium.ttf"),
        size=FONT_SIZE,
    )
    font_bold = ImageFont.truetype(
        os.path.join(DINISH_FONT_PATH, "DINish-Bold.ttf"), size=FONT_SIZE
    )

    padding_left = specs["padding-left"]

    BLACK = (0, 0, 0, 255)

    start_y = -4
    line_spacing = 5
    text_positions = [
        (padding_left, y)
        for y in range(start_y, image.height, FONT_SIZE + line_spacing)
    ]

    def format_km(km: float) -> str:
        """Format a distance in km. One decimal place below 100 km, integer with thousands separator above."""
        return f"{km:.1f}" if km < 100 else f"{km:,.0f}"

    # Define the text lines from gear_stats
    gear_name = gear_stats["name"].replace(brand_name, "").strip()
    gear_distance = f"{format_km(gear_stats['distance_km'])} km"

    # If this week’s distance is zero, show 30d distance instead. Else, show “Off duty”
    def featured_distance(stats):
        if stats["this_week"]["distance_km"] > 0:
            return f"{format_km(stats['this_week']['distance_km'])} km (wk)"
        if stats["last_30_days"]["distance_km"] > 0:
            return f"{format_km(stats['last_30_days']['distance_km'])} km (30d)"
        return "Off duty"

    # Write the text on the image
    draw.text(text_positions[0], gear_name, fill=BLACK, font=font_bold)
    draw.text(text_positions[1], gear_distance, fill=BLACK, font=font_regular)
    draw.text(
        text_positions[3], featured_distance(gear_stats), fill=BLACK, font=font_regular
    )

    # Return image as RGB
    return image.convert("RGB")
