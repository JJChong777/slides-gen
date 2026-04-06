from client import app
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from json_repair import repair_json

@asynccontextmanager
async def slidedeckai_lifespan(app: FastAPI):
    app.state.max_tokens = 300
    app.state.last_input = None
    app.state.messages = None
    app.state.slides_template = None
    
    try:
        print("Initializing Vertex AI...")
        # Replace with your actual Google Cloud Project ID
        vertexai.init(project="YOUR_GOOGLE_CLOUD_PROJECT_ID", location="us-central1")
        
        # Initialize Gemini 1.5 Flash (Fast, cheap, and excellent at JSON)
        app.state.model = GenerativeModel("gemini-1.5-flash-002")
        
        print("Vertex AI initialized successfully.")
    except Exception as e:
        app.state.model = None
        print(f"Vertex AI initialization failed: {e}")


# app = FastAPI(lifespan=lifespan)
app = FastAPI(lifespan=slidedeckai_lifespan)

@app.get("/")
def root():
    return {"message": "server_gen_vertex is running"}

@app.get("/slides_json")
def get_slides_json():
    if not app.state.last_input:
        raise HTTPException(status_code=400, detail="No prompt provided yet. Call /input_slides first.")
    if not app.state.model:
        raise HTTPException(status_code=500, detail="Vertex AI model not loaded.")
    
    # Construct the full prompt
    full_prompt = f"System Instructions:\n{SYSTEM_PROMPT}\n\nUser Input:\n{app.state.last_input}"
    
    try:
        # Enforce strict JSON output using GenerationConfig
        response = app.state.model.generate_content(
            full_prompt,
            generation_config=GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
            )
        )
        
        raw_json_output = response.text
        json_output = repair_json(raw_json_output)
        return JSONResponse(content=json_output)
        
    except Exception as e:
        print(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate slides: {str(e)}")


SYSTEM_PROMPT = '''
You are an expert presentation designer. Given a topic, generate a complete, visually engaging slide deck.

Return ONLY valid JSON — no markdown, no code fences, no explanation. Match this schema exactly.

SCHEMA:
{
  "title": "string",
  "theme": {
    "primaryColor": "hex without #",
    "secondaryColor": "hex without #",
    "accentColor": "hex without #",
    "backgroundColor": "hex without #",
    "textColor": "hex without #",
    "fontFaceTitle": "string (e.g. Georgia)",
    "fontFaceBody": "string (e.g. Calibri)"
  },
  "slides": [ /* array of slide objects — see types below */ ]
}

SLIDE TYPES — use "type" field to select:

1. "title" — Opening title slide (dark bg, big text)
{
  "type": "title",
  "heading": "string",
  "subheading": "string",
  "background": "hex without #"  // optional override
}

2. "bullets" — Classic title + bullet points
{
  "type": "bullets",
  "heading": "string",
  "bullets": [
    { "text": "string", "bold": false, "sub": false }
  ],
  "accent": "left" | "none"  // left = colored bar on left edge
}

3. "two_column" — Side-by-side content (text vs text, or text vs stats)
{
  "type": "two_column",
  "heading": "string",
  "left": { "heading": "string", "bullets": ["string"] },
  "right": { "heading": "string", "bullets": ["string"] }
}

4. "comparison" — Before/after or A vs B with colored headers
{
  "type": "comparison",
  "heading": "string",
  "left": { "label": "string", "color": "hex", "points": ["string"] },
  "right": { "label": "string", "color": "hex", "points": ["string"] }
}

5. "stats" — Big number callouts (3-4 metrics)
{
  "type": "stats",
  "heading": "string",
  "stats": [
    { "value": "string", "label": "string", "sublabel": "string" }
  ]
}

6. "timeline" — Horizontal numbered steps
{
  "type": "timeline",
  "heading": "string",
  "steps": [
    { "number": 1, "title": "string", "description": "string" }
  ]
}

7. "process" — Vertical step-by-step flow with connectors
{
  "type": "process",
  "heading": "string",
  "steps": [
    { "title": "string", "description": "string" }
  ]
}

8. "quote" — Full-bleed pull quote slide
{
  "type": "quote",
  "quote": "string",
  "attribution": "string",
  "background": "hex without #"
}

9. "agenda" — Numbered agenda / table of contents
{
  "type": "agenda",
  "heading": "string",
  "items": ["string"]
}

10. "chart" — Bar, line, or pie chart with data
{
  "type": "chart",
  "heading": "string",
  "chartType": "bar" | "line" | "pie" | "doughnut",
  "series": [
    { "name": "string", "labels": ["string"], "values": [number] }
  ],
  "showLegend": true
}

11. "table" — Data table
{
  "type": "table",
  "heading": "string",
  "headers": ["string"],
  "rows": [["string"]]
}

12. "image_text" — Half image (placeholder) + text panel
{
  "type": "image_text",
  "heading": "string",
  "imagePosition": "left" | "right",
  "imageCaption": "string",
  "bullets": ["string"]
}

13. "section_break" — Visual divider between sections (dark bg, centered)
{
  "type": "section_break",
  "sectionNumber": "string",
  "heading": "string",
  "subheading": "string"
}

14. "closing" — Final CTA / thank you slide
{
  "type": "closing",
  "heading": "string",
  "subheading": "string",
  "cta": "string",
  "background": "hex without #"
}

DESIGN RULES:
- Always start with a "title" slide
- Always end with a "closing" slide
- Use "section_break" slides to divide major sections
- Pick a cohesive color palette (don't default to blue/white)
- Include at least one "stats", "chart", or "comparison" slide when relevant
- Include 8-14 slides total for a full deck
- NEVER use "#" in hex colors — output them without the # prefix
- All hex colors must be exactly 6 characters
'''

