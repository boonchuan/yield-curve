const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat
} = require('docx');

// Elsevier highlights: 3-5 bullets, each max 85 characters incl. spaces.
// Verify lengths:
const bullets = [
  "Six U.S. yield curve inversions, 1986–2024, display heterogeneous spread responses.",
  "Wald test rejects equality of episode inversion coefficients at p < 0.001.",
  "Pooled inversion effect is zero; pre-2022 is zero; Episode 6 effect is positive.",
  "Only the 2022–2024 episode shows predictive power for 6-month spread changes.",
  "Findings caution against pooled inference in the yield curve literature.",
];

// Verify character counts
bullets.forEach(b => {
  const len = b.length;
  const ok = len <= 85;
  console.log(`[${len}/${ok ? "OK " : "TOO LONG"}] ${b}`);
});

const children = [
  new Paragraph({
    children: [new TextRun({ text: "Highlights", bold: true, size: 28 })],
    spacing: { after: 240 },
  }),
];

bullets.forEach(b => {
  children.push(new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({ text: b })],
    spacing: { after: 120, line: 360 },
  }));
});

const doc = new Document({
  styles: { default: { document: { run: { font: "Times New Roman", size: 24 } } } },
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/home/claude/highlights.docx", buf);
  console.log("\nWrote highlights.docx");
});
