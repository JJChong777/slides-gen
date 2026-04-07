import json

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from json_repair import repair_json

@asynccontextmanager
async def server_gen_lifespan(app: FastAPI):
    app.state.max_tokens = 300
    app.state.last_input = None
    app.state.messages = []
    app.state.slides_template = None
    
    try:
        print("Initializing Vertex AI...")
        vertexai.init(project="slide-gen-492602", location="us-central1")
        
        app.state.model = GenerativeModel("gemini-2.5-flash-lite")
        
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

@app.post("/receive_user_text")
def receive_user_text(user_input: str = Form(...)):
    try:
        user_message = {
            "role": "user",
            ### to add the text from PDF into the content
            "content": [{"type": "text", "text": user_input}]
        }
        app.state.messages.append(user_message)
        app.state.last_input = user_input
        print(f"Received slides prompt: {user_input}")
        return {"message": f"Slide Gen Prompt received: {user_input}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting slides generation prompt")

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
        try:
            json_output = json.loads(raw_json_output)
            print("Successfully parsed JSON on first try.")
            
        except json.JSONDecodeError as e:
            # 2. Fallback: If it's invalid (e.g., markdown wrappers), repair it
            print(f"Standard JSON parsing failed: {e}. Attempting repair...")
            # Remember to keep return_objects=True to prevent the double-serialization bug!
            json_output = repair_json(raw_json_output, return_objects=True)
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

