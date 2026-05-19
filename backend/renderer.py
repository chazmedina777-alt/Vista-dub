from PIL import Image, ImageDraw, ImageFont
import os
from backend.schemas import PrintBlueprint

def generate_surface_render(blueprint: PrintBlueprint, surface_name: str, target_dpi: int = 300) -> Image.Image:
    """
    Renders a pixel-perfect, commercial-ready image file directly from physical 
    inch coordinates, supporting text compositing and dynamic uploaded image scaling.
    """
    target_surface = next((s for s in blueprint.surfaces if s.surface_name == surface_name), None)
    if not target_surface:
        raise ValueError(f"Surface target '{surface_name}' footprint not found in data blueprint.")

    w_in = blueprint.dimensions.width_in
    h_in = blueprint.dimensions.height_in
    bleed = blueprint.dimensions.bleed_in

    canvas_width_px = int((w_in + (bleed * 2)) * target_dpi)
    canvas_height_px = int((h_in + (bleed * 2)) * target_dpi)
    bleed_offset_px = int(bleed * target_dpi)

    image = Image.new("RGBA", (canvas_width_px, canvas_height_px), "#FFFFFF")
    draw = ImageDraw.Draw(image)

    if target_dpi < 300:
        draw.rectangle(
            [bleed_offset_px, bleed_offset_px, canvas_width_px - bleed_offset_px, canvas_height_px - bleed_offset_px],
            outline="#E0E0E0", width=1
        )

    sorted_elements = sorted(target_surface.elements, key=lambda e: e.z_index)

    CURRENT_FILE = os.path.abspath(__file__)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_FILE))

    for element in sorted_elements:
        x_px = int(element.transform.x_in * target_dpi) + bleed_offset_px
        y_px = int(element.transform.y_in * target_dpi) + bleed_offset_px

        if element.type == "text" and element.text_props:
            props = element.text_props
            pixel_font_size = int((props.font_size_pt * target_dpi) / 72.0)
            try:
                font = ImageFont.truetype("LiberationSans-Regular.ttf", pixel_font_size)
            except IOError:
                font = ImageFont.load_default()
            draw.text((x_px, y_px), props.text, fill=props.color_hex, font=font)

        elif element.type == "image" and element.image_props:
            props = element.image_props
            if not props.source_url:
                continue

            # CRITICAL FIX: Extract just the filename and force map it to the true backend/storage/ directory
            filename = props.source_url.split("/")[-1]
            local_asset_path = os.path.join(PROJECT_ROOT, "backend", "storage", filename)

            if os.path.exists(local_asset_path):
                try:
                    with Image.open(local_asset_path) as asset_img:
                        if asset_img.mode != "RGBA":
                            asset_img = asset_img.convert("RGBA")

                        target_w_px = int(props.width_in * props.scale_x * target_dpi)
                        target_h_px = int(props.height_in * props.scale_y * target_dpi)

                        if target_w_px > 0 and target_h_px > 0:
                            resized_asset = asset_img.resize((target_w_px, target_h_px), Image.Resampling.LANCZOS)
                            image.alpha_composite(resized_asset, (x_px, y_px))
                except Exception as e:
                    print(f"Skipping asset element processing error on file {local_asset_path}: {e}")
            else:
                print(f"WARNING: Image file not found at strict server path: {local_asset_path}")

    return image
