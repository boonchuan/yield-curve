const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel
} = require('docx');

function p(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, ...opts })],
    spacing: { after: 240, line: 360 },
    alignment: opts.alignment || AlignmentType.LEFT,
  });
}

function p_runs(runs) {
  return new Paragraph({
    children: runs,
    spacing: { after: 240, line: 360 },
    alignment: AlignmentType.LEFT,
  });
}

const children = [
  p("LIM Boon Chuan", { bold: true }),
  p("Independent Researcher"),
  p("Singapore"),
  p("boonchuan@singapore.to"),
  p(""),
  p("April 19, 2026"),
  p(""),
  p("The Editors"),
  p("Finance Research Open"),
  p("Elsevier"),
  p(""),
  p("Dear Editors,"),
  p(""),
  p_runs([
    new TextRun({ text: "I am pleased to submit for your consideration the attached manuscript, \"" }),
    new TextRun({ text: "Episode Heterogeneity in the Yield Curve Inversion–Credit Spread Relationship: Evidence from Six U.S. Inversion Episodes, 1986–2024", italics: true }),
    new TextRun({ text: ",\" for publication in " }),
    new TextRun({ text: "Finance Research Open", italics: true }),
    new TextRun({ text: "." }),
  ]),
  p("The paper documents an empirical feature of U.S. yield curve inversions that, to my knowledge, has not been cleanly established in the prior literature: the relationship between yield curve inversion and investment-grade credit spreads is strongly heterogeneous across historical inversion episodes. Using monthly data from 1986 through 2024 and six identifiable inversion episodes, I show that pooled regressions yield a null effect, but this null reflects cancellation across episodes with heterogeneous coefficient signs rather than a stable zero relationship. A Wald test decisively rejects the null of coefficient homogeneity across episodes (χ²(5) = 436.7, p < 0.001). In separate predictive regressions, only the 2022–2024 episode shows a statistically significant relationship between inversion depth and six-month-ahead spread changes (β = +0.22, t = 3.11, R² = 0.74), meaning the widely discussed \"inversion predicts widening credit spreads\" pattern visible in recent data is driven entirely by this single episode."),
  p("The paper makes two contributions. First, methodologically, it demonstrates that pooled inversion coefficients in the yield curve literature mask substantial episode-level instability and should be accompanied by tests of parameter homogeneity. Second, economically, it identifies the 2022–2024 episode as a structural outlier—the longest, deepest, and only episode in which inversion depth predicts subsequent credit spread widening—raising questions about the joint role of supply-driven inflation, the pace of monetary tightening, and the real policy rate in shaping the inversion–spread relationship."),
  p("The paper fits the scope of Finance Research Open in that it applies standard time-series econometric methods (OLS with Newey–West HAC standard errors) to publicly available FRED data to produce an empirical finding of direct interest to the yield curve and credit spread literatures. All data and code are reproducible."),
  p("The manuscript has not been published previously and is not under consideration at any other journal. The author declares no conflict of interest. The paper is single-authored."),
  p("Thank you for considering this submission. I look forward to your response."),
  p(""),
  p("Sincerely,"),
  p(""),
  p(""),
  p("LIM Boon Chuan"),
];

const doc = new Document({
  styles: { default: { document: { run: { font: "Times New Roman", size: 24 } } } },
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
  fs.writeFileSync("/home/claude/cover_letter.docx", buf);
  console.log("Wrote cover_letter.docx");
});
