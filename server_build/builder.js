import PptxGenJS from "pptxgenjs";

// ── Slide dimensions (LAYOUT_16x9) ────────────────────────────────────────────
const W = 10;   // inches
const H = 5.625;

// ── Defaults ──────────────────────────────────────────────────────────────────
const DEFAULT_THEME = {
  primaryColor:   "1E2761",
  secondaryColor: "CADCFC",
  accentColor:    "F96167",
  backgroundColor:"FFFFFF",
  textColor:      "1A1A2E",
  fontFaceTitle:  "Georgia",
  fontFaceBody:   "Calibri",
};

/**
 * Build a .pptx from the AI-generated JSON.
 * @param {object} data - full slides JSON from ai.js
 * @returns {Buffer} pptx file buffer
 */
export async function buildPptx(data) {
  const pres = new PptxGenJS();
  pres.layout = "LAYOUT_16x9";
  pres.title = data.title || "Presentation";
  pres.defineSlideMaster({
  title: "MASTER_SLIDE",
  slideNumber: { x: 9.5, y: 5.3, color: "888888", fontSize: 10 }
});

  const theme = { ...DEFAULT_THEME, ...(data.theme || {}) };

  for (const slideData of data.slides || []) {
    const slide = pres.addSlide();
    await renderSlide(pres, slide, slideData, theme);
  }

  return await pres.write({ outputType: "nodebuffer" });
}

// ── Router ────────────────────────────────────────────────────────────────────
async function renderSlide(pres, slide, data, theme) {
  switch (data.type) {
    case "title":         return renderTitle(slide, data, theme);
    case "bullets":       return renderBullets(slide, data, theme);
    case "two_column":    return renderTwoColumn(slide, data, theme);
    case "comparison":    return renderComparison(slide, data, theme);
    case "stats":         return renderStats(slide, data, theme);
    case "timeline":      return renderTimeline(slide, data, theme);
    case "process":       return renderProcess(slide, data, theme);
    case "quote":         return renderQuote(slide, data, theme);
    case "agenda":        return renderAgenda(slide, data, theme);
    case "chart":         return renderChart(pres, slide, data, theme);
    case "table":         return renderTable(slide, data, theme);
    case "image_text":    return renderImageText(slide, data, theme);
    case "section_break": return renderSectionBreak(slide, data, theme);
    case "closing":       return renderClosing(slide, data, theme);
    default:
      // Fallback — treat as bullets
      return renderBullets(slide, { ...data, type: "bullets" }, theme);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function hex(color, fallback) {
  if (!color) return fallback || "000000";
  return String(color).replace(/^#/, "").slice(0, 6);
}

function slideTitle(slide, text, theme, opts = {}) {
  slide.addText(text, {
    x: opts.x ?? 0.5,
    y: opts.y ?? 0.3,
    w: opts.w ?? W - 1,
    h: opts.h ?? 0.65,
    fontSize: opts.fontSize ?? 28,
    bold: true,
    fontFace: theme.fontFaceTitle,
    color: opts.color ?? hex(theme.textColor),
    margin: 0,
    fit:'shrink',
    ...opts.extra,
  });
}

function makeShadow() {
  return { type: "outer", color: "000000", blur: 6, offset: 3, angle: 135, opacity: 0.12 };
}

// ── 1. Title slide ─────────────────────────────────────────────────────────────
function renderTitle(slide, data, theme) {
  const bg = hex(data.background || theme.primaryColor);
  slide.background = { color: bg };

  // Decorative shapes
  slide.addShape("rect", {
    x: 0, y: H - 1.2, w: W, h: 1.2,
    fill: { color: hex(theme.accentColor), transparency: 20 },
    line: { color: hex(theme.accentColor), transparency: 20 },
  });
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.18, h: H,
    fill: { color: hex(theme.accentColor) },
    line: { color: hex(theme.accentColor) },
  });

  slide.addText(data.heading || "Untitled", {
    x: 0.6, y: 1.4, w: W - 1.2, h: 1.8,
    fontSize: 44,
    bold: true,
    fontFace: theme.fontFaceTitle,
    color: "FFFFFF",
    align: "left",
    valign: "middle",
    fit:'shrink',
  });

  if (data.subheading) {
    slide.addText(data.subheading, {
      x: 0.6, y: 3.3, w: W - 1.2, h: 0.8,
      fontSize: 18,
      fontFace: theme.fontFaceBody,
      color: hex(theme.secondaryColor),
      align: "left",
      fit:'shrink',
    });
  }
}

// ── 2. Bullets slide ──────────────────────────────────────────────────────────
function renderBullets(slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };

  if (data.accent === "left") {
    slide.addShape("rect", {
      x: 0, y: 0, w: 0.12, h: H,
      fill: { color: hex(theme.primaryColor) },
      line: { color: hex(theme.primaryColor) },
    });
  }

  slideTitle(slide, data.heading || "", theme, { x: data.accent === "left" ? 0.35 : 0.5 });

  // Divider
  slide.addShape("rect", {
    x: data.accent === "left" ? 0.35 : 0.5,
    y: 1.05, w: W - 1.2, h: 0.035,
    fill: { color: hex(theme.accentColor) },
    line: { color: hex(theme.accentColor) },
  });

  const bullets = (data.bullets || []).map((b, i) => ({
    text: String(typeof b === "object" ? (b.text || "") : b),
    options: {
      bullet: true,
      bold: typeof b === "object" ? b.bold : false,
      indentLevel: typeof b === "object" && b.sub ? 1 : 0,
      fontSize: 15,
      fontFace: theme.fontFaceBody,
      color: hex(theme.textColor),
      breakLine: i < (data.bullets.length - 1),
    },
  }));

  slide.addText(bullets, {
    x: data.accent === "left" ? 0.35 : 0.5,
    y: 1.2, w: W - 1.2, h: H - 1.5,
    valign: "top",
    fit:'shrink',
  });
}

// ── 3. Two-column slide ────────────────────────────────────────────────────────
function renderTwoColumn(slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };
  slideTitle(slide, data.heading || "", theme);

  slide.addShape("rect", {
    x: 0.5, y: 1.05, w: W - 1, h: 0.035,
    fill: { color: hex(theme.accentColor) },
    line: { color: hex(theme.accentColor) },
  });

  const colW = (W - 1.3) / 2;
  const cols = [data.left, data.right];
  const xs = [0.5, 0.5 + colW + 0.3];

  cols.forEach((col, i) => {
    if (!col) return;
    // Column header bg
    slide.addShape("rect", {
      x: xs[i], y: 1.15, w: colW, h: 0.5,
      fill: { color: hex(theme.primaryColor) },
      line: { color: hex(theme.primaryColor) },
    });
    slide.addText(col.heading || "", {
      x: xs[i], y: 1.15, w: colW, h: 0.5,
      fontSize: 14, bold: true,
      fontFace: theme.fontFaceTitle,
      color: "FFFFFF", align: "center", valign: "middle", margin: 0,
      fit:'shrink',
    });

    const items = (col.bullets || []).map((b, j, arr) => ({
      text: String(b),
      options: {
        bullet: true, fontSize: 13,
        fontFace: theme.fontFaceBody,
        color: hex(theme.textColor),
        breakLine: j < arr.length - 1,
      },
    }));
    slide.addText(items, {
      x: xs[i] + 0.05, y: 1.75, w: colW - 0.1, h: H - 2.0,
      valign: "top",
      fit:'shrink',
    });
  });
}

// ── 4. Comparison slide ───────────────────────────────────────────────────────
function renderComparison(slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };
  slideTitle(slide, data.heading || "", theme);

  const colW = (W - 1.3) / 2;
  const xs = [0.5, 0.5 + colW + 0.3];
  const sides = [data.left, data.right];

  sides.forEach((side, i) => {
    if (!side) return;
    const color = hex(side.color || (i === 0 ? theme.primaryColor : theme.accentColor));
    // Header
    slide.addShape("rect", {
      x: xs[i], y: 1.0, w: colW, h: 0.65,
      fill: { color }, line: { color },
      shadow: makeShadow(),
    });
    slide.addText(side.label || "", {
      x: xs[i], y: 1.0, w: colW, h: 0.65,
      fontSize: 18, bold: true,
      fontFace: theme.fontFaceTitle,
      color: "FFFFFF", align: "center", valign: "middle", margin: 0,
      fit:'shrink',
    });
    // Card bg
    slide.addShape("rect", {
      x: xs[i], y: 1.7, w: colW, h: H - 2.0,
      fill: { color: "F8F9FA" }, line: { color: "E0E0E0", width: 1 },
    });
    const items = (side.points || []).map((p, j, arr) => ({
      text: String(p),
      options: {
        bullet: true, fontSize: 13,
        fontFace: theme.fontFaceBody,
        color: hex(theme.textColor),
        breakLine: j < arr.length - 1,
      },
    }));
    slide.addText(items, {
      x: xs[i] + 0.15, y: 1.8, w: colW - 0.3, h: H - 2.2,
      valign: "top",
      fit:'shrink',
    });
  });
}

// ── 5. Stats slide ────────────────────────────────────────────────────────────
function renderStats(slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };
  slideTitle(slide, data.heading || "", theme);

  slide.addShape("rect", {
    x: 0.5, y: 1.0, w: W - 1, h: 0.035,
    fill: { color: hex(theme.accentColor) },
    line: { color: hex(theme.accentColor) },
  });

  const stats = data.stats || [];
  const count = Math.min(stats.length, 4);
  const cardW = (W - 1 - (count - 1) * 0.2) / count;
  const startX = 0.5;

  stats.slice(0, count).forEach((stat, i) => {
    const x = startX + i * (cardW + 0.2);
    // Card
    slide.addShape("rect", {
      x, y: 1.2, w: cardW, h: H - 1.6,
      fill: { color: "F8F9FA" },
      line: { color: hex(theme.primaryColor), width: 1 },
      shadow: makeShadow(),
    });
    // Accent top bar
    slide.addShape("rect", {
      x, y: 1.2, w: cardW, h: 0.12,
      fill: { color: hex(theme.accentColor) },
      line: { color: hex(theme.accentColor) },
    });
    // Big number
    slide.addText(String(stat.value || ""), {
      x, y: 1.5, w: cardW, h: 1.4,
      fontSize: 48, bold: true,
      fontFace: theme.fontFaceTitle,
      color: hex(theme.primaryColor),
      align: "center", valign: "middle", margin: 0,
      fit:'shrink',
    });
    // Label
    slide.addText(stat.label || "", {
      x, y: 2.95, w: cardW, h: 0.55,
      fontSize: 14, bold: true,
      fontFace: theme.fontFaceBody,
      color: hex(theme.textColor),
      align: "center", margin: 0,
      fit:'shrink',
    });
    // Sublabel
    if (stat.sublabel) {
      slide.addText(stat.sublabel, {
        x, y: 3.5, w: cardW, h: 0.5,
        fontSize: 11, italic: true,
        fontFace: theme.fontFaceBody,
        color: "888888",
        align: "center", margin: 0,
        fit:'shrink',
      });
    }
  });
}

// ── 6. Timeline slide ─────────────────────────────────────────────────────────
function renderTimeline(slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };
  slideTitle(slide, data.heading || "", theme);

  const steps = (data.steps || []).slice(0, 5);
  const count = steps.length;
  if (!count) return;

  const lineY = 2.8;
  const stepW = (W - 1) / count;
  const startX = 0.5;

  // Horizontal line
  slide.addShape("rect", {
    x: startX, y: lineY - 0.02, w: W - 1, h: 0.04,
    fill: { color: hex(theme.primaryColor) },
    line: { color: hex(theme.primaryColor) },
  });

  steps.forEach((step, i) => {
    const cx = startX + i * stepW + stepW / 2;

    // Circle
    slide.addShape("ellipse", {
      x: cx - 0.28, y: lineY - 0.28, w: 0.56, h: 0.56,
      fill: { color: hex(theme.accentColor) },
      line: { color: "FFFFFF", width: 2 },
      shadow: makeShadow(),
    });
    // Number
    slide.addText(String(step.number ?? i + 1), {
      x: cx - 0.28, y: lineY - 0.28, w: 0.56, h: 0.56,
      fontSize: 14, bold: true,
      color: "FFFFFF", align: "center", valign: "middle", margin: 0,
      fit:'shrink',

    });
    // Title above line
    slide.addText(step.title || "", {
      x: cx - stepW / 2 + 0.05, y: lineY - 1.3, w: stepW - 0.1, h: 0.9,
      fontSize: 13, bold: true,
      fontFace: theme.fontFaceTitle,
      color: hex(theme.textColor),
      align: "center", valign: "bottom", margin: 0,
      fit:'shrink',
    });
    // Description below line
    if (step.description) {
      slide.addText(step.description, {
        x: cx - stepW / 2 + 0.05, y: lineY + 0.38, w: stepW - 0.1, h: 1.5,
        fontSize: 11,
        fontFace: theme.fontFaceBody,
        color: "555555",
        align: "center", valign: "top",
        fit:'shrink',
      });
    }
  });
}

// ── 7. Process slide ──────────────────────────────────────────────────────────
function renderProcess(slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };
  slideTitle(slide, data.heading || "", theme);

  const steps = (data.steps || []).slice(0, 5);
  const rowH = (H - 1.4) / steps.length;

  steps.forEach((step, i) => {
    const y = 1.1 + i * rowH;
    const color = i % 2 === 0
      ? hex(theme.primaryColor)
      : hex(theme.secondaryColor);
    const textColor = i % 2 === 0 ? "FFFFFF" : hex(theme.textColor);

    // Number badge
    slide.addShape("ellipse", {
      x: 0.4, y: y + rowH / 2 - 0.28, w: 0.56, h: 0.56,
      fill: { color: hex(theme.accentColor) },
      line: { color: hex(theme.accentColor) },
    });
    slide.addText(String(i + 1), {
      x: 0.4, y: y + rowH / 2 - 0.28, w: 0.56, h: 0.56,
      fontSize: 14, bold: true, color: "FFFFFF",
      align: "center", valign: "middle", margin: 0,
      fit:'shrink',
    });

    // Step bar
    slide.addShape("rect", {
      x: 1.1, y: y + 0.05, w: W - 1.7, h: rowH - 0.15,
      fill: { color },
      line: { color },
      shadow: makeShadow(),
    });

    slide.addText(step.title || "", {
      x: 1.25, y: y + 0.05, w: 2.5, h: rowH - 0.15,
      fontSize: 14, bold: true,
      fontFace: theme.fontFaceTitle,
      color: textColor, valign: "middle", margin: 0,
      fit:'shrink',
    });

    if (step.description) {
      slide.addText(step.description, {
        x: 3.9, y: y + 0.05, w: W - 5.1, h: rowH - 0.15,
        fontSize: 12,
        fontFace: theme.fontFaceBody,
        color: textColor, valign: "middle",
        fit:'shrink',
      });
    }

    // Connector arrow (skip last)
    if (i < steps.length - 1) {
      slide.addShape("rect", {
        x: 0.6, y: y + rowH - 0.08, w: 0.12, h: 0.16,
        fill: { color: hex(theme.accentColor) },
        line: { color: hex(theme.accentColor) },
      });
    }
  });
}

// ── 8. Quote slide ────────────────────────────────────────────────────────────
function renderQuote(slide, data, theme) {
  const bg = hex(data.background || theme.primaryColor);
  slide.background = { color: bg };

  // Large quote mark
  slide.addText("\u201C", {
    x: 0.4, y: 0.1, w: 2, h: 2,
    fontSize: 120, bold: true,
    color: hex(theme.accentColor),
    fontFace: theme.fontFaceTitle,
    transparency: 40,
    margin: 0,
    fit:'shrink',
  });

  slide.addText(data.quote || "", {
    x: 0.9, y: 1.0, w: W - 1.8, h: H - 2.4,
    fontSize: 22, italic: true,
    fontFace: theme.fontFaceTitle,
    color: "FFFFFF",
    align: "center", valign: "middle",
    fit:'shrink',
  });

  if (data.attribution) {
    slide.addShape("rect", {
      x: W / 2 - 1, y: H - 1.1, w: 2, h: 0.04,
      fill: { color: hex(theme.accentColor) },
      line: { color: hex(theme.accentColor) },
    });
    slide.addText(`— ${data.attribution}`, {
      x: 0, y: H - 1.0, w: W, h: 0.6,
      fontSize: 14, bold: true,
      fontFace: theme.fontFaceBody,
      color: hex(theme.secondaryColor),
      align: "center",
      fit:'shrink',
    });
  }
}

// ── 9. Agenda slide ───────────────────────────────────────────────────────────
function renderAgenda(slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };

  // Left panel
  slide.addShape("rect", {
    x: 0, y: 0, w: 3.2, h: H,
    fill: { color: hex(theme.primaryColor) },
    line: { color: hex(theme.primaryColor) },
  });
  slide.addText(data.heading || "Agenda", {
    x: 0.15, y: H / 2 - 0.5, w: 2.9, h: 1,
    fontSize: 28, bold: true,
    fontFace: theme.fontFaceTitle,
    color: "FFFFFF",
    align: "center", valign: "middle",
    fit:'shrink',
  });

  // Items
  const items = data.items || [];
  const itemH = Math.min(0.72, (H - 0.8) / items.length);
  items.forEach((item, i) => {
    const y = 0.4 + i * (itemH + 0.1);
    slide.addShape("ellipse", {
      x: 3.5, y: y + itemH / 2 - 0.24, w: 0.48, h: 0.48,
      fill: { color: hex(theme.accentColor) },
      line: { color: hex(theme.accentColor) },
    });
    slide.addText(String(i + 1), {
      x: 3.5, y: y + itemH / 2 - 0.24, w: 0.48, h: 0.48,
      fontSize: 13, bold: true, color: "FFFFFF",
      align: "center", valign: "middle", margin: 0,
      fit:'shrink',
    });
    slide.addText(item, {
      x: 4.15, y, w: W - 4.55, h: itemH,
      fontSize: 15,
      fontFace: theme.fontFaceBody,
      color: hex(theme.textColor),
      valign: "middle",
      fit:'shrink',
    });
    // Thin separator
    if (i < items.length - 1) {
      slide.addShape("rect", {
        x: 3.5, y: y + itemH + 0.04, w: W - 4, h: 0.015,
        fill: { color: "DDDDDD" }, line: { color: "DDDDDD" },
      });
    }
  });
}

// ── 10. Chart slide ───────────────────────────────────────────────────────────
function renderChart(pres, slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };
  slideTitle(slide, data.heading || "", theme);

  const typeMap = {
    bar: pres.charts.BAR,
    line: pres.charts.LINE,
    pie: pres.charts.PIE,
    doughnut: pres.charts.DOUGHNUT,
  };
  const chartType = typeMap[data.chartType] || pres.charts.BAR;
  const series = data.series || [];
  if (!series.length) return;

  const colors = [
    hex(theme.primaryColor),
    hex(theme.accentColor),
    hex(theme.secondaryColor),
    "4DB6AC", "FF8A65", "9575CD",
  ];

  slide.addChart(chartType, series, {
    x: 0.5, y: 1.1, w: W - 1, h: H - 1.5,
    barDir: "col",
    chartColors: colors,
    chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },
    catAxisLabelColor: "64748B",
    valAxisLabelColor: "64748B",
    valGridLine: { color: "E2E8F0", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelColor: hex(theme.textColor),
    showLegend: data.showLegend !== false,
    legendPos: "b",
    legendFontSize: 11,
  });
}

// ── 11. Table slide ───────────────────────────────────────────────────────────
function renderTable(slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };
  slideTitle(slide, data.heading || "", theme);

  const headers = (data.headers || []).map((h) => ({
    text: h,
    options: {
      bold: true,
      color: "FFFFFF",
      fill: { color: hex(theme.primaryColor) },
      align: "center",
    },
  }));

  const rows = [
    headers,
    ...(data.rows || []).map((row, ri) =>
      row.map((cell) => ({
        text: String(cell),
        options: {
          fill: { color: ri % 2 === 0 ? "F8F9FA" : "FFFFFF" },
          color: hex(theme.textColor),
          fontSize: 12,
        },
      }))
    ),
  ];

  const colCount = headers.length || 1;
  const colW = (W - 1) / colCount;

  slide.addTable(rows, {
    x: 0.5, y: 1.1, w: W - 1,
    colW: Array(colCount).fill(colW),
    border: { pt: 0.5, color: "D0D0D0" },
    fontSize: 13,
    fontFace: theme.fontFaceBody,
  });
}

// ── 12. Image + text slide ────────────────────────────────────────────────────
function renderImageText(slide, data, theme) {
  slide.background = { color: hex(theme.backgroundColor) };

  const imgLeft = data.imagePosition !== "right";
  const imgX = imgLeft ? 0 : W / 2;
  const textX = imgLeft ? W / 2 + 0.3 : 0.5;

  // Image placeholder (grey box with caption)
  slide.addShape("rect", {
    x: imgX, y: 0, w: W / 2, h: H,
    fill: { color: hex(theme.secondaryColor), transparency: 30 },
    line: { color: hex(theme.secondaryColor) },
  });
  slide.addText(data.imageCaption || "[ Image ]", {
    x: imgX, y: H / 2 - 0.3, w: W / 2, h: 0.6,
    fontSize: 13, italic: true,
    color: hex(theme.primaryColor),
    align: "center", valign: "middle",
    fit:'shrink',
  });

  // Text panel
  slideTitle(slide, data.heading || "", theme, {
    x: textX, y: 0.4, w: W / 2 - 0.6,
  });

  const items = (data.bullets || []).map((b, i, arr) => ({
    text: String(b),
    options: {
      bullet: true, fontSize: 13,
      fontFace: theme.fontFaceBody,
      color: hex(theme.textColor),
      breakLine: i < arr.length - 1,
    },
  }));
  slide.addText(items, {
    x: textX, y: 1.2, w: W / 2 - 0.6, h: H - 1.6,
    valign: "top",
    fit:'shrink',
  });
}

// ── 13. Section break slide ────────────────────────────────────────────────────
function renderSectionBreak(slide, data, theme) {
  slide.background = { color: hex(theme.primaryColor) };

  // Decorative accent line
  slide.addShape("rect", {
    x: W / 2 - 1.5, y: 1.8, w: 3, h: 0.06,
    fill: { color: hex(theme.accentColor) },
    line: { color: hex(theme.accentColor) },
  });

  if (data.sectionNumber) {
    slide.addText(`Section ${data.sectionNumber}`, {
      x: 0, y: 0.8, w: W, h: 0.6,
      fontSize: 14, bold: true,
      fontFace: theme.fontFaceBody,
      color: hex(theme.secondaryColor),
      align: "center",
      fit:'shrink',
    });
  }

  slide.addText(data.heading || "", {
    x: 0.5, y: 2.0, w: W - 1, h: 1.4,
    fontSize: 38, bold: true,
    fontFace: theme.fontFaceTitle,
    color: "FFFFFF",
    align: "center", valign: "middle",
    fit:'shrink',
  });

  if (data.subheading) {
    slide.addText(data.subheading, {
      x: 1, y: 3.5, w: W - 2, h: 0.7,
      fontSize: 15,
      fontFace: theme.fontFaceBody,
      color: hex(theme.secondaryColor),
      align: "center",
      fit:'shrink',
    });
  }
}

// ── 14. Closing slide ──────────────────────────────────────────────────────────
function renderClosing(slide, data, theme) {
  const bg = hex(data.background || theme.primaryColor);
  slide.background = { color: bg };

  slide.addShape("rect", {
    x: 0, y: 0, w: W, h: 0.18,
    fill: { color: hex(theme.accentColor) },
    line: { color: hex(theme.accentColor) },
  });
  slide.addShape("rect", {
    x: 0, y: H - 0.18, w: W, h: 0.18,
    fill: { color: hex(theme.accentColor) },
    line: { color: hex(theme.accentColor) },
  });

  slide.addText(data.heading || "Thank You", {
    x: 0.5, y: 1.1, w: W - 1, h: 1.4,
    fontSize: 42, bold: true,
    fontFace: theme.fontFaceTitle,
    color: "FFFFFF",
    align: "center", valign: "middle",
    fit:'shrink',
  });

  if (data.subheading) {
    slide.addText(data.subheading, {
      x: 1, y: 2.7, w: W - 2, h: 0.7,
      fontSize: 16,
      fontFace: theme.fontFaceBody,
      color: hex(theme.secondaryColor),
      align: "center",
      fit:'shrink',
    });
  }

  if (data.cta) {
    slide.addShape("rect", {
      x: W / 2 - 2, y: 3.6, w: 4, h: 0.75,
      fill: { color: hex(theme.accentColor) },
      line: { color: hex(theme.accentColor) },
      shadow: makeShadow(),
    });
    slide.addText(data.cta, {
      x: W / 2 - 2, y: 3.6, w: 4, h: 0.75,
      fontSize: 15, bold: true,
      fontFace: theme.fontFaceBody,
      color: "FFFFFF",
      align: "center", valign: "middle", margin: 0,
      fit:'shrink',
    });
  }
}
