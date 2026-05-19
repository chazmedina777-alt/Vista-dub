from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from io import BytesIO
import os
import shutil
import sqlite3
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from backend.schemas import PrintBlueprint
from backend.renderer import generate_surface_render

app = FastAPI(title="PrintFlow Order Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_FILE = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_FILE))
FRONTEND_FILE = os.path.join(PROJECT_ROOT, "frontend", "index.html")
STORAGE_DIR = os.path.join(PROJECT_ROOT, "backend", "storage")
DB_PATH = os.path.join(STORAGE_DIR, "printflow.sqlite")

SENDER_EMAIL = "ChazMedina777@gmail.com"
SENDER_PASSWORD = "vved orhh lbuu syaa" 

os.makedirs(STORAGE_DIR, exist_ok=True)
with sqlite3.connect(DB_PATH) as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS blueprints (design_id TEXT PRIMARY KEY, payload TEXT)")

app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*60)
    print("  PRINTFLOW ENGINE GATEWAY ACTIVE - TEMPLATE MATRIX ARMED")
    print("="*60 + "\n")

# EXPANDED TEMPLATE LIBRARY (6 Layouts Total)
@app.get("/api/v1/templates")
async def get_built_in_templates():
    return {
        "corporate_modern": [
            {"type": "text", "text": "ALEX MERCER", "left": 45, "top": 50, "color": "#1a1a22", "size": 34, "font": "Montserrat"},
            {"type": "text", "text": "Chief Executive Officer", "left": 45, "top": 90, "color": "#00a2ff", "size": 14, "font": "Roboto"},
            {"type": "text", "text": "📞 +1 (555) 234-5678", "left": 45, "top": 170, "color": "#5a6268", "size": 13, "font": "Helvetica"},
            {"type": "text", "text": "✉️ alex@enterprise.com", "left": 45, "top": 195, "color": "#5a6268", "size": 13, "font": "Helvetica"},
            {"type": "text", "text": "🌐 www.enterprise.com", "left": 45, "top": 220, "color": "#5a6268", "size": 13, "font": "Helvetica"}
        ],
        "luxury_editorial": [
            {"type": "text", "text": "V A L E N T I N A", "left": 130, "top": 60, "color": "#c5a880", "size": 36, "font": "Cinzel"},
            {"type": "text", "text": "B O U T I Q U E  D E S I G N E R", "left": 132, "top": 115, "color": "#a0a0ab", "size": 11, "font": "Montserrat"},
            {"type": "text", "text": "studio@valentina.luxury", "left": 150, "top": 210, "color": "#1e1e24", "size": 13, "font": "Playfair Display"}
        ],
        "retro_creative": [
            {"type": "text", "text": "MOOMOO HQ", "left": 50, "top": 45, "color": "#ff0055", "size": 42, "font": "Bebas Neue"},
            {"type": "text", "text": "Est. 2026 / Creative Lab", "left": 52, "top": 95, "color": "#1e1e24", "size": 14, "font": "Special Elite"},
            {"type": "text", "text": "hello@moomoographics.com", "left": 52, "top": 180, "color": "#ff0055", "size": 13, "font": "Pacifico"}
        ],
        "tech_startup": [
            {"type": "text", "text": "< DATA . SYNC >", "left": 40, "top": 50, "color": "#00ffcc", "size": 24, "font": "IBM Plex Mono"},
            {"type": "text", "text": "ELLIOT ALDERSON", "left": 40, "top": 100, "color": "#1e1e24", "size": 28, "font": "Archivo Black"},
            {"type": "text", "text": "Lead Cybersecurity Engineer", "left": 40, "top": 135, "color": "#a0a0ab", "size": 12, "font": "Inter"},
            {"type": "text", "text": "E: elliot@datasync.io", "left": 40, "top": 210, "color": "#5a6268", "size": 12, "font": "IBM Plex Mono"}
        ],
        "real_estate": [
            {"type": "text", "text": "SARAH JENKINS", "left": 150, "top": 50, "color": "#2c3e50", "size": 32, "font": "Cinzel"},
            {"type": "text", "text": "LUXURY REAL ESTATE BROKER", "left": 155, "top": 90, "color": "#b8860b", "size": 12, "font": "Montserrat"},
            {"type": "text", "text": "M: (555) 867-5309", "left": 200, "top": 170, "color": "#34495e", "size": 14, "font": "Lato"},
            {"type": "text", "text": "sarah@prime-estates.com", "left": 175, "top": 200, "color": "#34495e", "size": 14, "font": "Lato"}
        ],
        "minimal_boutique": [
            {"type": "text", "text": "aura", "left": 230, "top": 70, "color": "#1a1a22", "size": 55, "font": "Sacramento"},
            {"type": "text", "text": "botanical skincare", "left": 205, "top": 140, "color": "#8b9dc3", "size": 16, "font": "Quicksand"},
            {"type": "text", "text": "@aura.botanicals", "left": 220, "top": 220, "color": "#a0a0ab", "size": 12, "font": "Inter"}
        ]
    }

@app.post("/api/v1/assets/upload", status_code=status.HTTP_201_CREATED)
async def upload_asset(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid asset type.")
    safe_filename = "".join([c for c in file.filename if c.isalnum() or c in "._-"]).strip()
    target_path = os.path.join(STORAGE_DIR, safe_filename)
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"asset_url": f"/storage/{safe_filename}", "filename": safe_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File system error: {str(e)}")

@app.post("/api/v1/designs", status_code=status.HTTP_201_CREATED)
async def save_or_update_design(payload: PrintBlueprint):
    design_id = payload.design_id
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO blueprints (design_id, payload) VALUES (?, ?)",
            (design_id, json.dumps(payload.model_dump()))
        )
    return {"message": "Blueprint verified and saved to SQLite", "design_id": design_id}

@app.get("/api/v1/designs/{design_id}/render/{surface_name}")
async def render_design_surface(design_id: str, surface_name: str, dpi: int = 150):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT payload FROM blueprints WHERE design_id = ?", (design_id,))
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Design not found.")
    blueprint = PrintBlueprint(**json.loads(row[0]))
    try:
        pil_image = generate_surface_render(blueprint, surface_name, target_dpi=dpi)
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        return Response(content=buffer.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering error: {str(e)}")

class OrderSubmissionRequest(BaseModel):
    target_email: str
    order_number: str
    material_type: str
    quantity: str

@app.post("/api/v1/designs/{design_id}/submit-order")
async def process_and_mail_order(design_id: str, payload: OrderSubmissionRequest):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT payload FROM blueprints WHERE design_id = ?", (design_id,))
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Design blueprint target dataset missing.")
    
    blueprint = PrintBlueprint(**json.loads(row[0]))
    try:
        front_img = generate_surface_render(blueprint, "front", target_dpi=300)
        rgb_image = front_img.convert("RGB")
        
        pdf_filename = f"Order_{payload.order_number}_production_master.pdf"
        pdf_path = os.path.join(STORAGE_DIR, pdf_filename)
        rgb_image.save(pdf_path, "PDF", resolution=300.0)

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = payload.target_email
        msg['Subject'] = f"📦 NEW PRINT ORDER: #{payload.order_number} [{payload.quantity} QTY]"

        body = (
            f"====================================================\n"
            f"          MOOMOO GRAPHIC PRODUCTION INBOUND JOB     \n"
            f"====================================================\n\n"
            f"  📌 Order Tracking ID: #{payload.order_number}\n"
            f"  🔢 Run Quantity:     {payload.quantity} units\n"
            f"  🌿 Specified Stock:  {payload.material_type}\n"
            f"  📧 Customer Receipt: {payload.target_email}\n\n"
            f"----------------------------------------------------\n"
            f"Production Master document generated successfully.\n"
            f"The press-ready 300 DPI layout file is attached below."
        )
        msg.attach(MIMEText(body, 'plain'))

        with open(pdf_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {pdf_filename}")
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, payload.target_email, msg.as_string())
        server.quit()

        return {
            "message": "Order verified",
            "order_number": payload.order_number,
            "quantity": payload.quantity,
            "pdf_url": f"/storage/{pdf_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order routing crash: {str(e)}")

@app.get("/")
async def serve_frontend_index():
    return FileResponse(FRONTEND_FILE)
