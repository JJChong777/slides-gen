import express from "express";
import cors from "cors";

import { buildPptx } from "./builder.js";

const PYTHON_SERVICE_URL = "http://server_gen_vertex:8002";

const app = express();
app.use(cors());
app.use(express.json({ limit: "10mb" }));

// ── Health ──────────────────────────────────────────────────────────────────
app.get("/", (_req, res) => res.json({ status: "ok", message: "server_build is running" }));

// ── POST /build ───────────────────────────────────────────────────────────────
// Takes raw JSON body (the slides schema) and builds the pptx directly
app.post("/build", async (req, res) => {
  try {
    const slidesJson = req.body;
    const buffer = await buildPptx(slidesJson);

    const title = (slidesJson.title || "presentation")
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

app.post("/build-full", async (req, res) => {
  try {
    const { prompt } = req.body;

    if (!prompt) {
      return res.status(400).json({ error: "Prompt is required" });
    }

    // 1. Send prompt to Python server (server_gen_vertex)
    // We use URLSearchParams because the Python endpoint expects Form(...) data
    const formData = new URLSearchParams();
    formData.append("user_input", prompt);

    const receiveResponse = await fetch(`${PYTHON_SERVICE_URL}/receive_user_text`, {
      method: "POST",
      body: formData,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
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
    const buffer = await buildPptx(slidesJson);

    // 4. Prepare filename and send
    const title = (slidesJson.title || "presentation")
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
    console.error("Orchestration Error:", err);
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`slidegen listening on :${PORT}`));
