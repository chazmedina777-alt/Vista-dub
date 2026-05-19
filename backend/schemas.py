from pydantic import BaseModel
from typing import List, Optional

class ElementTransform(BaseModel):
    x_in: float
    y_in: float
    rotation_deg: float

class TextProperties(BaseModel):
    text: str
    font_family: str
    font_size_pt: float
    color_hex: str
    align: str

class ImageProperties(BaseModel):
    source_url: str
    width_in: float
    height_in: float
    scale_x: float
    scale_y: float

class SurfaceElement(BaseModel):
    element_id: str
    type: str
    z_index: int
    transform: ElementTransform
    text_props: Optional[TextProperties] = None
    image_props: Optional[ImageProperties] = None

class SurfaceBlueprint(BaseModel):
    surface_name: str
    elements: List[SurfaceElement]

class PrintDimensions(BaseModel):
    width_in: float
    height_in: float
    bleed_in: float

class PrintBlueprint(BaseModel):
    design_id: str
    product_id: str
    status: str
    dimensions: PrintDimensions
    surfaces: List[SurfaceBlueprint]
