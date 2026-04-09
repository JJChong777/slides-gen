import json

from google import genai
from google.genai.types import HttpOptions, Part
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from json_repair import repair_json

@asynccontextmanager
async def server_gen_lifespan(app: FastAPI):
    app.state.contents = None
    
    try:
        print("Initializing Vertex AI Client...")
        app.state.client = genai.Client(vertexai=True,project="slide-gen-492602", location="us-central1")
        app.state.config = genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=4096,
            temperature=0.3,
            response_logprobs=True,
            logprobs=3,
            response_mime_type="application/json",
          )
        print("Vertex AI initialized successfully.")
    except Exception as e:
        app.state.model = None
        print(f"Vertex AI initialization failed: {e}")
    print("Server Gen Vertex is ready to receive requests.")
    yield
    print("Server Gen Vertex shutting down.")


# app = FastAPI(lifespan=lifespan)
app = FastAPI(lifespan=server_gen_lifespan)

@app.get("/")
def root():
    return {"message": "server_gen_vertex is running"}

@app.post("/receive_user_prompt")
async def receive_user_text(prompt: str = Form(...), 
    pdf_file: UploadFile | None = None):
    try:
        if pdf_file:
            file_bytes = await pdf_file.read()
            pdf_part = Part.from_bytes(data=file_bytes, mime_type="application/pdf")
            app.state.contents = [pdf_part, prompt]
            print(f"Received slides prompt with PDF: {pdf_file.filename}")
        else:
            app.state.contents = prompt
            print(f"Received slides prompt (Text Only): {prompt}")
        return {"message": "Slide Gen Prompt (and optional PDF) received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting slides generation prompt")

@app.get("/slides_json")
def get_slides_json():
    if not app.state.contents:
        raise HTTPException(status_code=400, detail="No prompt provided yet. Call /input_slides first.")
    if not app.state.client or not app.state.config:
        raise HTTPException(status_code=500, detail="Vertex AI client or config not loaded.")
    
    # Construct the full prompt

    
    try:
        # Enforce strict JSON output using GenerationConfig
        response = app.state.client.models.generate_content(
          model=MODEL_ID,
          contents=app.state.contents,
          config=app.state.config,
        )
        
        raw_json_output = response.text
        try:
            json_output = json.loads(raw_json_output)
            print("Successfully parsed JSON on first try.")
            
        except json.JSONDecodeError as e:
            # 2. Fallback: If it's invalid (e.g., markdown wrappers), repair it
            print(f"Standard JSON parsing failed: {e}. Attempting repair...")
            # Remember to keep return_objects=True to prevent the double-serialization bug!
            json_output = repair_json(raw_json_output, return_objects=True)
        
        app.state.contents = None  
        return JSONResponse(content=json_output)
        
    except Exception as e:
        print(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate slides: {str(e)}")

MODEL_ID = "gemini-2.5-flash-lite"

SYSTEM_PROMPT = '''
You are an expert presentation designer. Given a topic, generate a complete, visually engaging slide deck.

Return ONLY valid JSON — no markdown, no code fences, no explanation. Match this schema exactly.

LENGTH CONSTRAINTS (CRITICAL - DO NOT FAIL):
- Bullets: MAXIMUM 15 words per bullet.
- Paragraphs/Descriptions: MAXIMUM 25 words.
- Agenda/Lists: MAXIMUM 8 items per slide. If there are more, create a second "agenda" slide.
- Headings: MAXIMUM 8 words.

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

