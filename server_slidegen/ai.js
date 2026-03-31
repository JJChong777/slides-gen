import Anthropic from "@anthropic-ai/sdk";
import { jsonrepair } from "jsonrepair";

const client = new Anthropic();

// ── System prompt ─────────────────────────────────────────────────────────────
// This is the "IR" (intermediate representation) schema Claude must follow.
// It maps 1-to-1 to pptxgenjs capabilities so the builder can execute it directly.
const SYSTEM_PROMPT = `
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

5. "stats" — Big number callouts (3–4 metrics)
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
- Include 8–14 slides total for a full deck
- NEVER use "#" in hex colors — output them without the # prefix
- All hex colors must be exactly 6 characters
`;

/**
 * Call Claude, get back structured slide JSON.
 * @param {string} prompt - user's topic / instructions
 * @param {string} [themeHint] - optional theme override ("dark", "light", "colorful")
 * @returns {object} parsed slides JSON
 */
export async function generateSlidesJson(prompt, themeHint) {
  const userMsg = themeHint
    ? `${prompt}\n\nTheme preference: ${themeHint}`
    : prompt;

  const message = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 4096,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: userMsg }],
  });

  const raw = message.content
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("");

  // Strip any accidental markdown fences
  const stripped = raw
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/, "")
    .trim();

  // jsonrepair fixes common LLM JSON mistakes (trailing commas, single quotes, etc.)
  const repaired = jsonrepair(stripped);
  return JSON.parse(repaired);
}
