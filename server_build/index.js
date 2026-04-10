import express from "express";
import cors from "cors";
import multer from "multer";
import { buildPptx } from "./builder.js";
import libre from 'libreoffice-convert';
import { promisify } from 'util';
const convertAsync = promisify(libre.convert);
const PYTHON_SERVICE_URL = "http://server_gen_vertex:8002";

const app = express();
const upload = multer({ storage: multer.memoryStorage() });
app.use(cors());
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// ── Health ──────────────────────────────────────────────────────────────────
app.get("/", (_req, res) => res.json({ status: "ok", message: "server_build is running" }));

// ── POST /build ───────────────────────────────────────────────────────────────
// Takes raw JSON body (the slides schema) and builds the pptx directly
app.post("/build", async (req, res) => {
  try {
    const slidesJson = req.body;
    const buffer = await buildPptx(slidesJson);

    const title = String(slidesJson.title || "presentation")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .slice(0, 50);

    res.setHeader(
      "Content-Type",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    );
    res.setHeader("Content-Disposition", `attachment; filename="${title}.pptx"`);
    res.send(buffer);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.post("/build_full", upload.single("pdf_file"), async (req, res) => {
  try {
    const { prompt } = req.body;
    const pdfFile = req.file;
// 1. Send prompt and optional PDF to Python server
    const formData = new FormData();
    formData.append("prompt", prompt);

    if (pdfFile) {
      // Convert buffer to Blob for fetch API
      const blob = new Blob([pdfFile.buffer], { type: pdfFile.mimetype });
      formData.append("pdf_file", blob, pdfFile.originalname);
    }

    const receiveResponse = await fetch(`${PYTHON_SERVICE_URL}/receive_user_prompt`, {
      method: "POST",
      body: formData,
      // IMPORTANT: Do not set Content-Type header manually here.
      // fetch() will automatically set it to multipart/form-data with the correct boundary.
    });

    if (!receiveResponse.ok) {
      throw new Error(`Python service failed to receive text: ${await receiveResponse.text()}`);
    }

    // 2. Request the generated JSON from Python server
    const jsonResponse = await fetch(`${PYTHON_SERVICE_URL}/slides_json`);
    
    if (!jsonResponse.ok) {
      throw new Error(`Python service failed to generate JSON: ${await jsonResponse.text()}`);
    }

    const slidesJson = await jsonResponse.json();

    // 3. Build the .pptx buffer using your existing builder
    const pptxBuffer = await buildPptx(slidesJson);

    const pdfBuffer = await convertAsync(pptxBuffer, '.pdf', undefined);

    // 4. Prepare filename and send
    const title = String(slidesJson.title || "presentation")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .slice(0, 50);

    res.json({
      pptx: pptxBuffer.toString('base64'),
      pdf: pdfBuffer.toString('base64'),
      filename: title
    });

  } catch (err) {
    console.error("Orchestration Error:", err);
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`slidegen listening on :${PORT}`));
