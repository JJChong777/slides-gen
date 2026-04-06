import express from "express";
import cors from "cors";

import { buildPptx } from "./builder.js";

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

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`slidegen listening on :${PORT}`));
