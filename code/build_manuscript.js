/**
 * Episode Heterogeneity in Yield Curve Inversions and Credit Spreads
 * Full manuscript for Finance Research Open (Elsevier)
 *
 * Author: LIM Boon Chuan (Yong Joo Seng Pte Ltd, Singapore)
 */

const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageBreak, TabStopType, TabStopPosition, ImageRun
} = require('docx');

// ============================================================================
// STYLE HELPERS
// ============================================================================

const border = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const topBorder = { top: border };
const bottomBorder = { bottom: border };
const topBottom = { top: border, bottom: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function p(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, ...opts })];
  return new Paragraph({
    children: runs,
    spacing: { after: opts.after || 120, line: opts.line || 360 },
    alignment: opts.alignment || AlignmentType.JUSTIFIED,
  });
}

function body(text) {
  // body paragraph: justified, double-spaced
  return new Paragraph({
    children: [new TextRun({ text })],
    spacing: { after: 120, line: 480 },
    alignment: AlignmentType.JUSTIFIED,
  });
}

function bodyRuns(runs) {
  return new Paragraph({
    children: runs,
    spacing: { after: 120, line: 480 },
    alignment: AlignmentType.JUSTIFIED,
  });
}

function h1(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, size: 28 })],
    spacing: { before: 360, after: 180 },
  });
}

function h2(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, size: 24 })],
    spacing: { before: 240, after: 120 },
  });
}

function title(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, size: 32 })],
    spacing: { after: 240 },
    alignment: AlignmentType.CENTER,
  });
}

function center(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, ...opts })],
    spacing: { after: 120 },
    alignment: AlignmentType.CENTER,
  });
}

function tableCaption(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, size: 22 })],
    spacing: { before: 240, after: 120 },
  });
}

function tableNote(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 20 })],
    spacing: { before: 80, after: 240 },
    alignment: AlignmentType.JUSTIFIED,
  });
}

function figureCaption(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, size: 22 })],
    spacing: { before: 240, after: 120 },
  });
}

function figureNote(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 20 })],
    spacing: { before: 80, after: 240 },
    alignment: AlignmentType.JUSTIFIED,
  });
}

function figure(path, width, height) {
  return new Paragraph({
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(path),
      transformation: { width, height },
      altText: { title: "Figure", description: path, name: "figure" },
    })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 },
  });
}

function cell(text, opts = {}) {
  const {
    width,
    bold = false,
    align = AlignmentType.LEFT,
    italics = false,
    top = false,
    bottom = false,
    fontSize = 20,
  } = opts;
  const borders = {
    top: top ? border : noBorder,
    bottom: bottom ? border : noBorder,
    left: noBorder,
    right: noBorder,
  };
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children: [new Paragraph({
      children: [new TextRun({ text, bold, italics, size: fontSize })],
      alignment: align,
      spacing: { after: 0 },
    })],
  });
}

// ============================================================================
// TABLES
// ============================================================================

// Table 1: Summary statistics
function table1() {
  const widths = [2340, 1404, 1404, 1404, 1404, 1404]; // sums to 9360
  const L = AlignmentType.LEFT;
  const C = AlignmentType.CENTER;
  const makeRow = (cells, opts = {}) => new TableRow({
    children: cells.map((c, i) =>
      cell(c.text, { width: widths[i], align: c.align || C, bold: c.bold || false,
                     top: opts.top, bottom: opts.bottom, fontSize: 20 })
    ),
  });
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      makeRow([{text:"Variable", align:L, bold:true}, {text:"Mean",bold:true},
               {text:"SD",bold:true}, {text:"Min",bold:true},
               {text:"Median",bold:true}, {text:"Max",bold:true}],
              {top:true, bottom:true}),
      makeRow([{text:"Credit spread (BAA–AAA, %)", align:L}, {text:"0.968"},
               {text:"0.358"}, {text:"0.550"}, {text:"0.900"}, {text:"3.380"}]),
      makeRow([{text:"T10Y2Y (%)", align:L}, {text:"0.982"}, {text:"0.895"},
               {text:"−0.929"}, {text:"0.859"}, {text:"2.834"}]),
      makeRow([{text:"DFF (%)", align:L}, {text:"3.325"}, {text:"2.686"},
               {text:"0.049"}, {text:"3.072"}, {text:"9.849"}]),
      makeRow([{text:"CPI YoY (%)", align:L}, {text:"2.794"}, {text:"1.606"},
               {text:"−1.959"}, {text:"2.670"}, {text:"8.979"}]),
      makeRow([{text:"Inversion indicator (0/1)", align:L}, {text:"0.128"},
               {text:"0.335"}, {text:"0"}, {text:"0"}, {text:"1"}],
              {bottom:true}),
    ],
  });
}

// Table 2: Episode identification and descriptive statistics
function table2() {
  const widths = [780, 1404, 1404, 1248, 1248, 1248, 1248, 780]; // sum 9360
  const L = AlignmentType.LEFT;
  const C = AlignmentType.CENTER;
  const mkRow = (cells, opts = {}) => new TableRow({
    children: cells.map((c, i) =>
      cell(c.text, { width: widths[i], align: c.align || C, bold: c.bold || false,
                     top: opts.top, bottom: opts.bottom, fontSize: 18 })
    ),
  });
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      mkRow([{text:"#",bold:true}, {text:"Start",bold:true}, {text:"End",bold:true},
             {text:"Months",bold:true}, {text:"Max inv.",bold:true},
             {text:"Avg CPI",bold:true}, {text:"Avg DFF",bold:true},
             {text:"ΔSpd",bold:true}], {top:true, bottom:true}),
      mkRow([{text:"1"}, {text:"1989-01"}, {text:"1989-09"}, {text:"9"},
             {text:"−0.322"}, {text:"4.85"}, {text:"9.42"}, {text:"−0.201"}]),
      mkRow([{text:"2"}, {text:"1990-03"}, {text:"1990-03"}, {text:"1"},
             {text:"−0.038"}, {text:"5.24"}, {text:"8.28"}, {text:"−0.069"}]),
      mkRow([{text:"3"}, {text:"1998-06"}, {text:"1998-06"}, {text:"1"},
             {text:"−0.024"}, {text:"1.62"}, {text:"5.56"}, {text:"+0.012"}]),
      mkRow([{text:"4"}, {text:"2000-02"}, {text:"2000-12"}, {text:"11"},
             {text:"−0.413"}, {text:"3.42"}, {text:"6.31"}, {text:"−0.028"}]),
      mkRow([{text:"5"}, {text:"2006-02"}, {text:"2007-05"}, {text:"16"},
             {text:"−0.145"}, {text:"2.96"}, {text:"5.10"}, {text:"+0.046"}]),
      mkRow([{text:"6"}, {text:"2022-07"}, {text:"2024-08"}, {text:"26"},
             {text:"−0.929"}, {text:"4.65"}, {text:"4.63"}, {text:"+0.206"}],
            {bottom:true}),
    ],
  });
}

// Table 3: Pooled vs episode 6 comparison
function table3() {
  const widths = [2808, 1638, 1638, 1638, 1638]; // 9360
  const L = AlignmentType.LEFT;
  const C = AlignmentType.CENTER;
  const mkRow = (cells, opts = {}) => new TableRow({
    children: cells.map((c, i) =>
      cell(c.text, { width: widths[i], align: c.align || C, bold: c.bold || false,
                     italics: c.italics || false,
                     top: opts.top, bottom: opts.bottom, fontSize: 20 })
    ),
  });
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      mkRow([{text:"Sample", align:L, bold:true},
             {text:"β(Inv)",bold:true}, {text:"t",bold:true},
             {text:"p",bold:true}, {text:"n",bold:true}],
            {top:true, bottom:true}),
      mkRow([{text:"Full sample 1986–2024", align:L},
             {text:"+0.021"}, {text:"+0.29"}, {text:"0.773"}, {text:"468"}]),
      mkRow([{text:"Pre-2022 (1986–2022:M6)", align:L},
             {text:"−0.047"}, {text:"−0.71"}, {text:"0.478"}, {text:"438"}]),
      mkRow([{text:"Episode 6 window only", align:L},
             {text:"+0.146"}, {text:"+1.98"}, {text:"0.048"}, {text:"42"}],
            {bottom:true}),
    ],
  });
}

// Table 4: Episode-interacted regression (BAA-AAA)
function table4() {
  const widths = [3120, 1560, 1560, 1560, 1560]; // 9360
  const L = AlignmentType.LEFT;
  const C = AlignmentType.CENTER;
  const mkRow = (cells, opts = {}) => new TableRow({
    children: cells.map((c, i) =>
      cell(c.text, { width: widths[i], align: c.align || C, bold: c.bold || false,
                     top: opts.top, bottom: opts.bottom, fontSize: 20 })
    ),
  });
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      mkRow([{text:"Variable", align:L, bold:true},
             {text:"Coef.",bold:true}, {text:"SE",bold:true},
             {text:"t-stat",bold:true}, {text:"p-value",bold:true}],
            {top:true, bottom:true}),
      mkRow([{text:"Constant", align:L},
             {text:"1.125"}, {text:"0.126"}, {text:"8.93"}, {text:"<0.001"}]),
      mkRow([{text:"Inv × E1 (1989)", align:L},
             {text:"+0.128"}, {text:"0.116"}, {text:"+1.11"}, {text:"0.269"}]),
      mkRow([{text:"Inv × E2 (1990)", align:L},
             {text:"+0.049"}, {text:"0.109"}, {text:"+0.45"}, {text:"0.654"}]),
      mkRow([{text:"Inv × E3 (1998)", align:L},
             {text:"−0.374"}, {text:"0.070"}, {text:"−5.36"}, {text:"<0.001"}]),
      mkRow([{text:"Inv × E4 (2000)", align:L},
             {text:"−0.134"}, {text:"0.061"}, {text:"−2.18"}, {text:"0.029"}]),
      mkRow([{text:"Inv × E5 (2006–07)", align:L},
             {text:"−0.023"}, {text:"0.048"}, {text:"−0.48"}, {text:"0.629"}]),
      mkRow([{text:"Inv × E6 (2022–24)", align:L},
             {text:"+0.099"}, {text:"0.112"}, {text:"+0.89"}, {text:"0.376"}]),
      mkRow([{text:"DFF", align:L},
             {text:"−0.016"}, {text:"0.016"}, {text:"−1.04"}, {text:"0.297"}]),
      mkRow([{text:"CPI YoY", align:L},
             {text:"−0.038"}, {text:"0.032"}, {text:"−1.21"}, {text:"0.226"}]),
      mkRow([{text:"n = 468    R² = 0.186    Wald χ²(5) = 436.69, p < 0.001",
              align:L, italics:true}, {text:""}, {text:""}, {text:""}, {text:""}],
            {top:true, bottom:true}),
    ],
  });
}

// Table 5: Per-episode predictive regressions
function table5() {
  const widths = [780, 1560, 1560, 1560, 1560, 1300, 1040]; // 9360
  const L = AlignmentType.LEFT;
  const C = AlignmentType.CENTER;
  const mkRow = (cells, opts = {}) => new TableRow({
    children: cells.map((c, i) =>
      cell(c.text, { width: widths[i], align: c.align || C, bold: c.bold || false,
                     top: opts.top, bottom: opts.bottom, fontSize: 20 })
    ),
  });
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      mkRow([{text:"Ep.",bold:true}, {text:"Window",bold:true},
             {text:"β(T10Y2Y)",bold:true}, {text:"t",bold:true},
             {text:"p",bold:true}, {text:"R²",bold:true}, {text:"n",bold:true}],
            {top:true, bottom:true}),
      mkRow([{text:"1"}, {text:"1988-07 to 1990-03"},
             {text:"+0.071"}, {text:"+0.51"}, {text:"0.613"},
             {text:"0.796"}, {text:"15"}]),
      mkRow([{text:"4"}, {text:"1999-08 to 2001-06"},
             {text:"+0.061"}, {text:"+0.54"}, {text:"0.591"},
             {text:"0.072"}, {text:"17"}]),
      mkRow([{text:"5"}, {text:"2005-08 to 2007-11"},
             {text:"+0.018"}, {text:"+0.09"}, {text:"0.928"},
             {text:"0.076"}, {text:"22"}]),
      mkRow([{text:"6"}, {text:"2022-01 to 2024-12"},
             {text:"+0.219"}, {text:"+3.11"}, {text:"0.002"},
             {text:"0.740"}, {text:"30"}],
            {bottom:true}),
    ],
  });
}

// ============================================================================
// DOCUMENT CONTENT
// ============================================================================

const children = [];

// ---- TITLE PAGE ----
children.push(title("Episode Heterogeneity in the Yield Curve Inversion–Credit Spread Relationship: Evidence from Six U.S. Inversion Episodes, 1986–2024"));

children.push(new Paragraph({ children: [new TextRun("")], spacing: {after: 240} }));
children.push(center("LIM Boon Chuan", { bold: true }));
children.push(center("Independent Researcher, Singapore"));
children.push(center("boonchuan@singapore.to"));
children.push(new Paragraph({ children: [new TextRun("")], spacing: {after: 360} }));

children.push(center("April 2026", { italics: true }));
children.push(new Paragraph({ children: [new TextRun("")], spacing: {after: 480} }));

// ---- ABSTRACT ----
children.push(h2("Abstract"));
children.push(body("Yield curve inversions are commonly treated as a homogeneous signal of credit stress. Using monthly U.S. data from 1986 to 2024 and six identifiable inversion episodes defined by the 10-year minus 2-year Treasury spread, I show that the relationship between yield curve inversion and investment-grade credit spreads is strongly heterogeneous across episodes. An episode-interacted regression decisively rejects the null of coefficient homogeneity (Wald χ²(5) = 436.7, p < 0.001); episode-specific inversion coefficients range from −0.37 to +0.13 percentage points with differing signs. Pooled regressions yield no significant effect, but this null reflects cancellation rather than a stable zero relationship. In per-episode predictive regressions at a six-month horizon, only the 2022–2024 episode shows a statistically significant relationship between inversion depth and subsequent spread changes (β = +0.22, t = 3.11, p = 0.002, R² = 0.74). Results are robust to an alternative inversion measure (T10Y3M), an alternative credit spread (BAA minus 10-year Treasury), a continuous inversion-depth measure, and both full-sample and rolling standardization of the spread. The apparent pooled relationship between inversion and spreads in recent data is driven almost entirely by the 2022–2024 episode, suggesting the post-COVID inversion is structurally distinct from prior episodes rather than a repetition of a common pattern."));

children.push(bodyRuns([
  new TextRun({ text: "Keywords: ", bold: true }),
  new TextRun({ text: "yield curve inversion; credit spreads; episode heterogeneity; recession prediction; term structure." }),
]));

children.push(bodyRuns([
  new TextRun({ text: "JEL classification: ", bold: true }),
  new TextRun({ text: "E43, E44, G12, G17." }),
]));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ---- SECTION 1: INTRODUCTION ----
children.push(h1("1. Introduction"));

children.push(body("The inversion of the U.S. Treasury yield curve—typically measured as the spread between the 10-year and 2-year (or 3-month) Treasury yields turning negative—is one of the most studied leading indicators in macroeconomics and finance. Since Estrella and Hardouvelis (1991) and Estrella and Mishkin (1998) established the predictive power of the term spread for U.S. recessions, a large literature has documented this relationship across business cycles (Rudebusch and Williams, 2009; Bauer and Mertens, 2018), alternative term-structure measures (Engstrom and Sharpe, 2019), and international samples."));

children.push(body("A parallel line of research examines credit spreads as indicators of financial stress and leading indicators of real activity. Gilchrist and Zakrajšek (2012) construct a micro-founded credit spread index that predicts economic activity beyond standard default-risk measures; their decomposition into a default-risk component and an excess bond premium has become a workhorse in the macro-finance literature. Gertler and Lown (1999) and Mueller (2009) document similar predictive content in high-yield spreads."));

children.push(body("Popular commentary frequently links these two indicators, suggesting that yield curve inversion itself causes or presages widening credit spreads. This view was reinforced by the 2022–2024 inversion episode, during which U.S. investment-grade credit spreads widened materially. Yet the pooled empirical evidence on the inversion–spread relationship is surprisingly thin. Most of the recession-prediction literature treats the term spread as a direct predictor of real activity, bypassing the credit spread channel; most of the credit spread literature takes the credit spread itself as a predictor rather than as an outcome."));

children.push(body("This paper addresses that gap by documenting a specific empirical feature of the data that has not been highlighted in prior work: the relationship between yield curve inversion and contemporaneous investment-grade credit spreads is strongly heterogeneous across historical inversion episodes, and pooled regressions mask this heterogeneity to the point of generating misleading inferences."));

children.push(body("Using monthly data from January 1986 through December 2024, I identify six distinct U.S. yield curve inversion episodes based on the 10-year minus 2-year Treasury spread (T10Y2Y). I then run an episode-interacted regression of the BAA–AAA credit spread on inversion indicators specific to each episode, controlling for the federal funds rate and year-over-year inflation, with Newey–West HAC standard errors. Three findings emerge."));

children.push(body("First, in pooled specifications the inversion indicator is statistically indistinguishable from zero (β = +0.021, t = 0.29, p = 0.77). Across 1986–2024, yield curve inversion is not on average associated with higher IG credit spreads once macroeconomic controls are included."));

children.push(body("Second, the episode-interacted specification strongly rejects the null that the six episode coefficients are equal (Wald χ²(5) = 436.7, p < 0.001). The estimated coefficients range from −0.37 (1998 episode, t = −5.4) to +0.13 (1989 episode). Spreads actually narrow during the 1998, 2000, and 1989 episodes (relative to the pre-inversion baseline), while the 2022–2024 episode shows widening. There is no stable pooled effect; the sign and magnitude of the inversion–spread relationship depends on which episode one examines."));

children.push(body("Third, in predictive (six-month-ahead) regressions run separately within each episode window, only the 2022–2024 episode produces a statistically significant coefficient on the yield curve slope (β = +0.22, t = 3.11, p = 0.002, R² = 0.74). In every prior episode, yield curve depth has no predictive power for six-month-ahead spread changes. The apparent \"inversion predicts spreads\" result in recent samples comes entirely from this single episode."));

children.push(body("These findings have two implications. Methodologically, they caution against pooled inference on inversion effects across historical episodes, given the evidence of coefficient instability. Economically, they suggest that the 2022–2024 inversion is structurally distinct from prior episodes rather than a repetition of a common pattern. The episode coincided with the fastest Federal Reserve tightening cycle since the early 1980s, supply-driven inflation following the COVID-19 pandemic, and the deepest T10Y2Y inversion in the sample—features that are not shared by prior episodes."));

children.push(body("The remainder of the paper is organized as follows. Section 2 briefly situates the paper in the literature and describes the data. Section 3 documents the pooled and episode-interacted results on the contemporaneous relationship. Section 4 presents the predictive regressions. Section 5 reports robustness checks. Section 6 concludes."));

// ---- SECTION 2: DATA ----
children.push(h1("2. Data and related literature"));

children.push(h2("2.1. Related literature"));

children.push(body("The yield curve's predictive content for recessions is well established. Estrella and Hardouvelis (1991) and Estrella and Mishkin (1998) show that the term spread forecasts U.S. recessions at horizons up to four quarters. Rudebusch and Williams (2009) confirm this robustness in real time. Engstrom and Sharpe (2019) argue that a near-term forward spread (the six-quarter-ahead forward rate minus the three-month bill) statistically dominates long-term spreads as a recession predictor."));

children.push(body("The credit spread literature has focused primarily on the predictive content of corporate bond spreads for real activity. Gilchrist and Zakrajšek (2012) construct the \"GZ spread\" from micro-level corporate bond data and decompose it into expected-default and excess-bond-premium components, showing the latter contains most of the predictive content. Bleaney et al. (2016) extend the analysis to international samples."));

children.push(body("Few papers directly examine how yield curve inversions relate to contemporaneous or near-term credit spreads. Harvey (1988) and Ang et al. (2006) consider joint dynamics of the term structure and credit conditions but within unified affine frameworks rather than through the inversion-as-event lens used here. The gap this paper addresses is the episode-by-episode heterogeneity of that relationship, which to my knowledge has not been documented in the prior literature."));

children.push(h2("2.2. Data"));

children.push(body("All data are from the Federal Reserve Economic Data (FRED) database at the Federal Reserve Bank of St. Louis. The credit spread measure is the difference between Moody's Seasoned BAA Corporate Bond Yield and Moody's Seasoned AAA Corporate Bond Yield (both monthly, series IDs BAA and AAA). This within-investment-grade spread captures the compensation for default and illiquidity risk on the lower rung of the IG universe, and has the longest continuous history among standard credit spread measures. Robustness checks using the BAA minus 10-year Treasury spread are reported in Section 5."));

children.push(body("The yield curve measure is the 10-year minus 2-year Treasury constant-maturity spread (series ID T10Y2Y), observed daily and aggregated to monthly mean. I define an inversion indicator as equal to one when the monthly-averaged T10Y2Y is negative, and zero otherwise. A robustness check uses the 10-year minus 3-month spread (T10Y3M)."));

children.push(body("Macroeconomic controls are the effective federal funds rate (DFF, daily, aggregated to monthly mean) and the year-over-year percent change in the headline Consumer Price Index for all urban consumers (CPIAUCSL, monthly). The sample period runs from January 1986 through December 2024, yielding 468 monthly observations—the longest continuous daily T10Y2Y series available aligned with monthly BAA/AAA data. Table 1 reports summary statistics."));

children.push(tableCaption("Table 1. Summary statistics, 1986:M1–2024:M12 (n = 468)"));
children.push(table1());
children.push(tableNote("Note: BAA–AAA credit spread in percentage points. T10Y2Y is the 10-year minus 2-year Treasury constant-maturity yield. DFF is the effective federal funds rate. CPI YoY is the year-over-year percent change in CPIAUCSL. Inversion indicator equals one when monthly-averaged T10Y2Y is negative."));

children.push(h2("2.3. Episode identification"));

children.push(body("I identify an inversion episode as a contiguous run of months with Inversion = 1, allowing up to two consecutive non-inversion months within an episode to accommodate brief technical un-inversions. This algorithm yields six episodes over 1986–2024. Table 2 summarizes them."));

children.push(tableCaption("Table 2. Inversion episodes, 1986–2024"));
children.push(table2());
children.push(tableNote("Note: \"Max inv.\" is the minimum (most negative) monthly-averaged T10Y2Y observed during the episode. \"Avg CPI\" and \"Avg DFF\" are episode-average percent levels. \"ΔSpd\" is the difference between the mean BAA–AAA spread during the episode and the mean spread over the 12 months immediately preceding it."));

children.push(body("Three features of Table 2 are notable. First, the 2022–2024 episode (Episode 6) is the longest (26 months) and deepest (maximum inversion of −93 basis points) in the sample; the next deepest episode (2000, Episode 4) reached −41 basis points. Second, the change in credit spread from the pre-inversion baseline (ΔSpd) is negative or near zero in every episode prior to 2022 and positive and large (+21 basis points) in Episode 6. Third, the macroeconomic context differs markedly: Episodes 1 and 6 both occurred during periods of elevated inflation (4.9% and 4.7% respectively), but the federal funds rate was 9.4% in 1989 versus 4.6% in 2022–2024, meaning the real policy rate was strongly positive in 1989 and approximately zero in 2022–2024."));

children.push(body("Figure 1 shows the 10Y–2Y Treasury spread (top panel) and the BAA–AAA credit spread (bottom panel) over the sample period, with inversion episodes shaded in red and NBER recessions in gray. The visual pattern reinforces the descriptive evidence: Episode 6 stands out both for the depth of inversion (breaking below −90 basis points) and for the contemporaneous credit-spread widening visible as a bump in the bottom panel. Earlier inversion episodes show either flat or declining credit spreads within the shaded region."));

children.push(figureCaption("Figure 1. Yield curve and credit spread, 1986–2024"));
children.push(figure("/home/claude/figs/figure1_timeseries.png", 576, 456));
children.push(figureNote("Note: Top panel plots the monthly-averaged 10-year minus 2-year Treasury constant-maturity spread (T10Y2Y). Bottom panel plots the BAA–AAA corporate bond spread. Red shaded bands denote inversion episodes identified in Table 2. Gray bands denote NBER-dated recessions. Episode labels E1–E2 overlap in the 1989–1990 period because these episodes are consecutive."));

// ---- SECTION 3: CONTEMPORANEOUS RESULTS ----
children.push(h1("3. Contemporaneous results"));

children.push(h2("3.1. Pooled specification"));

children.push(body("I begin with the standard pooled specification:"));

children.push(new Paragraph({
  children: [new TextRun({
    text: "Spread_t = α + β₁·Inversion_t + β₂·DFF_t + β₃·CPI_YoY_t + ε_t,   (1)",
    italics: true
  })],
  alignment: AlignmentType.CENTER,
  spacing: { before: 120, after: 120, line: 360 },
}));

children.push(body("estimated by OLS with Newey–West (1987) HAC standard errors, using a lag length of 6 months. The lag length follows the data-driven rule of thumb L = ⌊4·(T/100)^(2/9)⌋ of Newey and West (1994), which for T = 468 yields L ≈ 6. The coefficient on the inversion indicator is +0.021 (t = 0.29, p = 0.77), not statistically distinguishable from zero. The coefficients on DFF (−0.016, t = −1.04) and CPI YoY (−0.038, t = −1.21) are likewise insignificant."));

children.push(body("This pooled result—that yield curve inversion has no systematic contemporaneous relationship with IG credit spreads once macro conditions are controlled for—stands in contrast to informal discussion that treats inversion as a harbinger of credit stress. One might conclude from this result alone that inversion is uninformative about contemporaneous credit conditions. That conclusion, as the next subsection shows, would be incorrect."));

children.push(h2("3.2. Episode-interacted specification"));

children.push(body("To examine whether the pooled null effect masks cross-episode heterogeneity, I estimate:"));

children.push(new Paragraph({
  children: [new TextRun({
    text: "Spread_t = α + Σₖ βₖ·(Inversion_t × 1{episode = k}) + γ₁·DFF_t + γ₂·CPI_YoY_t + ε_t,   (2)",
    italics: true
  })],
  alignment: AlignmentType.CENTER,
  spacing: { before: 120, after: 120, line: 360 },
}));

children.push(body("where the episode indicator equals one during the episode window and for the twelve months immediately following it (to capture the post-inversion adjustment period), and zero otherwise. The inversion-episode interactions thus identify episode-specific inversion effects relative to normal (non-inverted) periods. Results appear in Table 4."));

children.push(tableCaption("Table 4. Episode-interacted contemporaneous regression"));
children.push(table4());
children.push(tableNote("Note: Dependent variable is the BAA–AAA credit spread. Standard errors are Newey–West HAC with 6 monthly lags. Wald test reports the chi-squared statistic for the null that all six episode coefficients (Inv × E1 through Inv × E6) are equal."));

children.push(body("Two results stand out. First, the coefficient estimates are economically and statistically heterogeneous across episodes. In Episodes 3 (1998) and 4 (2000), the inversion coefficient is significantly negative, indicating that IG credit spreads were meaningfully narrower during these inversions than in comparable non-inverted periods. In Episode 1 (1989) and Episode 6 (2022–2024), the point estimates are positive (though not significant at conventional levels in this specification), while Episodes 2 and 5 are near zero. Second, and more decisively, the Wald test of coefficient equality across the six episodes yields χ²(5) = 436.7, with p-value less than 0.001. The hypothesis that a single inversion coefficient applies to all episodes is overwhelmingly rejected."));

children.push(figureCaption("Figure 2. Episode-specific inversion coefficients with 95% confidence intervals"));
children.push(figure("/home/claude/figs/figure2_episode_coefs.png", 528, 324));
children.push(figureNote("Note: Point estimates and 95% confidence intervals for each episode's inversion coefficient from the interacted regression reported in Table 4. Filled markers indicate significance at the 5% level; open markers indicate non-significance. Standard errors are Newey–West HAC with 6 monthly lags. The Wald test statistic for the null that all six episode coefficients are equal is shown in the lower-right corner."));

children.push(body("The policy rate and inflation controls remain insignificant in this specification. This indicates that the pooled null effect of the inversion indicator in equation (1) is not driven by colinearity between inversion and macro levels, but by cancellation across episodes with opposing signs."));

children.push(h2("3.3. Pooled versus episode-6-only comparison"));

children.push(body("To make the heterogeneity concrete, Table 3 reports the pooled inversion coefficient across three samples: the full 1986–2024 sample, a pre-2022 subsample (through 2022:M6), and a window around Episode 6 only."));

children.push(tableCaption("Table 3. Pooled inversion coefficient across samples"));
children.push(table3());
children.push(tableNote("Note: Each row reports the coefficient on the inversion indicator in a pooled OLS regression of the BAA–AAA spread on the inversion indicator, DFF, and CPI YoY, with Newey–West HAC standard errors (6 monthly lags). The Episode 6 window includes the inversion months and 12 months before and after."));

children.push(body("The pattern is striking. The full-sample coefficient is essentially zero, and the pre-2022 subsample coefficient is slightly negative (though insignificant). Only in the Episode 6 window does a positive, marginally significant coefficient emerge. The widely-discussed \"inversion predicts widening spreads\" pattern visible in recent data is a feature of the 2022–2024 episode, not a generalizable relationship that shows up across U.S. history."));

// ---- SECTION 4: PREDICTIVE RESULTS ----
children.push(h1("4. Predictive results"));

children.push(body("The preceding results concern the contemporaneous relationship. I now turn to whether yield curve depth has predictive content for future credit spread changes, running the per-episode specification:"));

children.push(new Paragraph({
  children: [new TextRun({
    text: "ΔSpread_{t+6} = α + β·T10Y2Y_t + γ₁·DFF_t + γ₂·CPI_YoY_t + ε_t,   (3)",
    italics: true
  })],
  alignment: AlignmentType.CENTER,
  spacing: { before: 120, after: 120, line: 360 },
}));

children.push(body("where ΔSpread_{t+6} = Spread_{t+6} − Spread_t, and the regression is run within each episode window (episode months plus six months before and six months after). The six-month horizon matches the time frame at which the recession-prediction literature typically finds yield-curve predictive content (Estrella and Mishkin, 1998; Rudebusch and Williams, 2009). Credit-risk studies sometimes consider longer horizons of 12 to 18 months; for tractability and comparability with the recession literature, I focus on the six-month result here and note that qualitative conclusions are unchanged at 12-month horizons (results available on request). Standard errors are Newey–West HAC with 6 monthly lags. Table 5 reports the coefficient on T10Y2Y (more negative values indicate deeper inversion; a positive β means that deeper inversion predicts a spread decline six months later)."));

children.push(tableCaption("Table 5. Per-episode predictive regressions: six-month-ahead spread change on contemporaneous T10Y2Y"));
children.push(table5());
children.push(tableNote("Note: Dependent variable is the six-month change in the BAA–AAA spread, Spread_{t+6} − Spread_t. Standard errors are Newey–West HAC with 6 monthly lags. Each regression is estimated on the episode-specific window described in the text. Episodes 2 and 3 are excluded because they consist of a single month and do not permit within-episode regression estimation. Controls for DFF and CPI YoY included in each regression but coefficients suppressed for brevity."));

children.push(body("Only Episode 6 (2022–2024) shows a statistically significant predictive coefficient on the yield curve measure (β = +0.22, t = 3.11, p = 0.002, R² = 0.74). The sign indicates that less-negative T10Y2Y values (shallower inversion or normalization) predict spread narrowing, while deeper inversion predicts spread widening. This is consistent with the informal narrative linking inversion to credit stress. The R² of 0.74 is notably high and reflects in part the strong trending behavior of spreads during this episode."));

children.push(body("For every prior episode (1, 4, and 5), the T10Y2Y coefficient is economically small and statistically insignificant. In Episode 1 (1989), R² = 0.80 but this is driven by DFF and CPI YoY rather than by the yield curve measure itself. In Episodes 4 (2000) and 5 (2006–2007), R² values are below 0.10, indicating the full regression has weak explanatory power in those episode windows."));

children.push(body("Figure 3 visualizes the per-episode relationship via added-variable plots. Each panel shows T10Y2Y and the six-month-ahead spread change after both have been residualized against DFF and CPI YoY, so the slope of the fitted line exactly equals the multivariate β reported in Table 5. The contrast is visually striking: Episodes 1, 4, and 5 show essentially flat residualized relationships, while Episode 6 shows a clear positive slope."));

children.push(figureCaption("Figure 3. Per-episode added-variable plots: six-month-ahead spread change against T10Y2Y, conditional on DFF and CPI YoY"));
children.push(figure("/home/claude/figs/figure3_per_episode_scatter.png", 624, 167));
children.push(figureNote("Note: Each panel plots the residual of ΔSpread_{t+6} against the residual of T10Y2Y, after both are regressed on a constant, DFF, and CPI YoY within the episode window. Dashed lines are OLS fits whose slopes equal the multivariate coefficients reported in Table 5. Episodes 2 and 3 are excluded because they consist of a single month. Asterisk on E6 title indicates statistical significance at the 5% level."));

children.push(body("Taken together, the predictive evidence reinforces the heterogeneity finding: yield curve inversion only predicted subsequent spread widening during Episode 6. In the other three episodes large enough to admit within-episode regression, neither inversion depth nor its normalization predicted six-month-ahead spread changes."));

// ---- SECTION 5: ROBUSTNESS ----
children.push(h1("5. Robustness"));

children.push(h2("5.1. Alternative inversion measure (T10Y3M)"));

children.push(body("Replacing T10Y2Y with the 10-year minus 3-month Treasury spread (T10Y3M) as the inversion measure yields a qualitatively similar picture. T10Y3M inverts in a subset of the episodes identified from T10Y2Y (53 months of T10Y3M inversion versus 60 months of T10Y2Y inversion over 1986–2024, with 39 months of overlap). The episode-interacted specification still rejects equality of episode coefficients (Wald χ²(5) = 70.5, p < 0.001), and the sign pattern across episodes is preserved. Details available on request."));

children.push(h2("5.2. Alternative credit spread (BAA–10Y)"));

children.push(body("Using the BAA minus 10-year Treasury spread as the dependent variable—a broader default-risk measure than BAA–AAA—the Wald test of episode-coefficient homogeneity is again decisively rejected (χ²(5) = 56.4, p < 0.001). However, the sign pattern differs: Episode 4 (2000) shows a significantly positive coefficient rather than negative, and Episodes 3 and 5 show strongly negative coefficients. This indicates that the specific sign pattern of heterogeneity is measure-dependent. The core finding—that a single pooled inversion coefficient cannot be imposed across episodes—is robust to the spread measure chosen. Results available on request."));

children.push(h2("5.3. Inversion depth (continuous)"));

children.push(body("Replacing the binary inversion indicator with a continuous depth measure (min(T10Y2Y, 0)) in the episode-interacted specification yields economically similar conclusions. Episode coefficients remain statistically heterogeneous. The depth measure does not improve fit over the binary indicator, suggesting that the contemporaneous relationship between inversion and IG credit spreads is better captured by the regime dummy than by a continuous gradient. Results available on request."));

children.push(h2("5.4. Standardized credit spreads"));

children.push(body("A potential concern is that credit spread levels are not stationary across four decades: both mean and volatility of the BAA–AAA spread shift across sub-periods (tighter and less volatile in 1993–1998 and 2014–2019; wider and more volatile around the 2008 financial crisis). If Episode 6's raw ΔSpread of +21 basis points is unremarkable when rescaled by the local volatility of spreads, the \"2022–2024 is distinctively wide\" framing would need revision. To check this, I re-express the dependent variable in two standardized forms: (i) a full-sample z-score, subtracting the 1986–2024 mean and dividing by the 1986–2024 standard deviation; and (ii) a rolling 10-year z-score using a 120-month trailing window. Table 6 reports the resulting episode-level ΔSpread values."));

// Table 6: Standardized episode deltas
const widths6 = [780, 1404, 1248, 1404, 1755, 1872, 897]; // sum 9360
const tbl6 = new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: widths6,
  rows: [
    new TableRow({ children: [
      cell("#",                    { width: widths6[0], align: AlignmentType.CENTER, bold:true, top:true, bottom:true, fontSize:20 }),
      cell("Start",                { width: widths6[1], align: AlignmentType.CENTER, bold:true, top:true, bottom:true, fontSize:20 }),
      cell("Months",               { width: widths6[2], align: AlignmentType.CENTER, bold:true, top:true, bottom:true, fontSize:20 }),
      cell("Raw ΔSpread",          { width: widths6[3], align: AlignmentType.CENTER, bold:true, top:true, bottom:true, fontSize:20 }),
      cell("Full-sample ΔZ",       { width: widths6[4], align: AlignmentType.CENTER, bold:true, top:true, bottom:true, fontSize:20 }),
      cell("Rolling 10-yr ΔZ",     { width: widths6[5], align: AlignmentType.CENTER, bold:true, top:true, bottom:true, fontSize:20 }),
      cell("Rank",                 { width: widths6[6], align: AlignmentType.CENTER, bold:true, top:true, bottom:true, fontSize:20 }),
    ]}),
    new TableRow({ children: [
      cell("1", { width: widths6[0], align: AlignmentType.CENTER, fontSize:20 }),
      cell("1989-01", { width: widths6[1], align: AlignmentType.CENTER, fontSize:20 }),
      cell("9", { width: widths6[2], align: AlignmentType.CENTER, fontSize:20 }),
      cell("−0.201", { width: widths6[3], align: AlignmentType.CENTER, fontSize:20 }),
      cell("−0.561", { width: widths6[4], align: AlignmentType.CENTER, fontSize:20 }),
      cell("n/a", { width: widths6[5], align: AlignmentType.CENTER, fontSize:20 }),
      cell("—", { width: widths6[6], align: AlignmentType.CENTER, fontSize:20 }),
    ]}),
    new TableRow({ children: [
      cell("2", { width: widths6[0], align: AlignmentType.CENTER, fontSize:20 }),
      cell("1990-03", { width: widths6[1], align: AlignmentType.CENTER, fontSize:20 }),
      cell("1", { width: widths6[2], align: AlignmentType.CENTER, fontSize:20 }),
      cell("−0.069", { width: widths6[3], align: AlignmentType.CENTER, fontSize:20 }),
      cell("−0.193", { width: widths6[4], align: AlignmentType.CENTER, fontSize:20 }),
      cell("n/a", { width: widths6[5], align: AlignmentType.CENTER, fontSize:20 }),
      cell("—", { width: widths6[6], align: AlignmentType.CENTER, fontSize:20 }),
    ]}),
    new TableRow({ children: [
      cell("3", { width: widths6[0], align: AlignmentType.CENTER, fontSize:20 }),
      cell("1998-06", { width: widths6[1], align: AlignmentType.CENTER, fontSize:20 }),
      cell("1", { width: widths6[2], align: AlignmentType.CENTER, fontSize:20 }),
      cell("+0.012", { width: widths6[3], align: AlignmentType.CENTER, fontSize:20 }),
      cell("+0.033", { width: widths6[4], align: AlignmentType.CENTER, fontSize:20 }),
      cell("+0.152", { width: widths6[5], align: AlignmentType.CENTER, fontSize:20 }),
      cell("3rd", { width: widths6[6], align: AlignmentType.CENTER, fontSize:20 }),
    ]}),
    new TableRow({ children: [
      cell("4", { width: widths6[0], align: AlignmentType.CENTER, fontSize:20 }),
      cell("2000-02", { width: widths6[1], align: AlignmentType.CENTER, fontSize:20 }),
      cell("11", { width: widths6[2], align: AlignmentType.CENTER, fontSize:20 }),
      cell("−0.028", { width: widths6[3], align: AlignmentType.CENTER, fontSize:20 }),
      cell("−0.079", { width: widths6[4], align: AlignmentType.CENTER, fontSize:20 }),
      cell("−0.033", { width: widths6[5], align: AlignmentType.CENTER, fontSize:20 }),
      cell("4th", { width: widths6[6], align: AlignmentType.CENTER, fontSize:20 }),
    ]}),
    new TableRow({ children: [
      cell("5", { width: widths6[0], align: AlignmentType.CENTER, fontSize:20 }),
      cell("2006-02", { width: widths6[1], align: AlignmentType.CENTER, fontSize:20 }),
      cell("16", { width: widths6[2], align: AlignmentType.CENTER, fontSize:20 }),
      cell("+0.046", { width: widths6[3], align: AlignmentType.CENTER, fontSize:20 }),
      cell("+0.128", { width: widths6[4], align: AlignmentType.CENTER, fontSize:20 }),
      cell("+0.083", { width: widths6[5], align: AlignmentType.CENTER, fontSize:20 }),
      cell("2nd", { width: widths6[6], align: AlignmentType.CENTER, fontSize:20 }),
    ]}),
    new TableRow({ children: [
      cell("6", { width: widths6[0], align: AlignmentType.CENTER, bold:true, bottom:true, fontSize:20 }),
      cell("2022-07", { width: widths6[1], align: AlignmentType.CENTER, bold:true, bottom:true, fontSize:20 }),
      cell("26", { width: widths6[2], align: AlignmentType.CENTER, bold:true, bottom:true, fontSize:20 }),
      cell("+0.206", { width: widths6[3], align: AlignmentType.CENTER, bold:true, bottom:true, fontSize:20 }),
      cell("+0.576", { width: widths6[4], align: AlignmentType.CENTER, bold:true, bottom:true, fontSize:20 }),
      cell("+0.915", { width: widths6[5], align: AlignmentType.CENTER, bold:true, bottom:true, fontSize:20 }),
      cell("1st", { width: widths6[6], align: AlignmentType.CENTER, bold:true, bottom:true, fontSize:20 }),
    ]}),
  ],
});

children.push(tableCaption("Table 6. Episode-level spread changes: raw, full-sample z-score, and rolling 10-year z-score"));
children.push(tbl6);
children.push(tableNote("Note: ΔSpread is the difference between the mean BAA–AAA spread (or standardized spread) during the episode and the mean over the 12 months immediately preceding it. Full-sample z-score uses the 1986–2024 mean and standard deviation. Rolling 10-year z-score uses a 120-month trailing window, so it is undefined for Episodes 1 and 2 which begin before the window fills. Rank is by absolute value of the rolling z-score delta. Bold: Episode 6."));

children.push(body("The core finding is robust: Episode 6 (2022–2024) shows the largest spread move under every standardization. Its rolling z-score delta of +0.92 is more than ten times the magnitude of the next-largest positive move (+0.08 in Episode 5) and three times the absolute magnitude of the largest negative move (−0.03 in Episode 4). Standardization if anything strengthens the \"Episode 6 is distinctive\" claim, because Episode 6 occurred against a backdrop of compressed post-crisis spread volatility, making the same raw move much larger in standardized units. Re-estimating equation (2) with the z-scored spread as the dependent variable yields the identical Wald test statistic (χ²(5) = 436.7, p < 0.001); with the rolling z-score, the Wald test statistic is lower (χ²(5) = 153.5, p < 0.001) due to the smaller effective sample but still decisively rejects coefficient homogeneity. Per-episode predictive regressions on the six-month z-scored spread change preserve the finding that Episode 6 is the only episode with a statistically significant yield-curve coefficient (β = +0.61, t = 3.11, p = 0.002)."));

// ---- SECTION 6: CONCLUSION ----
children.push(h1("6. Conclusion"));

children.push(body("Using 39 years of U.S. data and six distinct yield curve inversion episodes, I document that the relationship between yield curve inversion and investment-grade credit spreads is strongly episode-dependent. Pooled regressions yield a null effect, but this null reflects cancellation across episodes with heterogeneous sign and magnitude, not a stable zero relationship. An episode-interacted specification rejects coefficient homogeneity at p < 0.001. The 2022–2024 inversion episode stands out as the only episode in the sample during which inversion depth significantly predicts six-month-ahead credit spread changes."));

children.push(body("These findings have three implications. First, empirical claims that yield curve inversion \"predicts\" or \"causes\" wider credit spreads on the basis of recent data should be interpreted cautiously: the relationship visible in 2022–2024 is not representative of prior episodes. Second, pooled specifications in the yield curve and credit spread literatures should test for episode-level parameter stability before reporting a single estimate; the Wald tests reported here suggest that such stability cannot be assumed. Third, the apparent novelty of the 2022–2024 episode—its depth, duration, and spread response—raises economically substantive questions about what distinguishes it from prior inversions, including the combination of supply-driven inflation, a compressed Fed tightening cycle, and near-zero real policy rates."));

children.push(body("This paper stops short of identifying the mechanism behind the 2022–2024 episode's distinct behavior. A natural extension would decompose the credit spread response into default-risk and excess-bond-premium components following Gilchrist and Zakrajšek (2012), and examine whether it is the default or the risk-premium channel that differs across episodes. Another extension would examine the episode-level heterogeneity using the near-term forward spread of Engstrom and Sharpe (2019), which may be less contaminated by term-premium variation than T10Y2Y. Both are left for future work."));

// ---- DECLARATIONS ----
children.push(h1("Declarations"));

children.push(bodyRuns([
  new TextRun({ text: "Conflict of interest. ", italics: true }),
  new TextRun({ text: "The author declares no conflict of interest, financial or otherwise, relevant to the content of this article." }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Funding. ", italics: true }),
  new TextRun({ text: "This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors." }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Data availability. ", italics: true }),
  new TextRun({ text: "All data used in this paper are publicly available from the Federal Reserve Economic Data (FRED) database at the Federal Reserve Bank of St. Louis (https://fred.stlouisfed.org). Series identifiers are listed in Section 2.2. Replication code (Python, using the statsmodels library) is available from the author on request and will be deposited in a public repository upon acceptance." }),
]));

children.push(bodyRuns([
  new TextRun({ text: "Declaration of generative AI use. ", italics: true }),
  new TextRun({ text: "During the preparation of this work the author used Claude (Anthropic) to assist with drafting prose, reviewing analysis code, and improving readability. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the publication." }),
]));

// ---- REFERENCES ----
children.push(h1("References"));

const refs = [
  "Ang, A., Piazzesi, M., Wei, M. (2006). What does the yield curve tell us about GDP growth? Journal of Econometrics 131, 359–403.",
  "Bauer, M. D., Mertens, T. M. (2018). Economic forecasts with the yield curve. FRBSF Economic Letter 2018-07.",
  "Bleaney, M., Mizen, P., Veleanu, V. (2016). Bond spreads and economic activity in eight European economies. Economic Modelling 60, 318–329.",
  "Engstrom, E. C., Sharpe, S. A. (2019). The near-term forward yield spread as a leading indicator: A less distorted mirror. Financial Analysts Journal 75(4), 37–49.",
  "Estrella, A., Hardouvelis, G. A. (1991). The term structure as a predictor of real economic activity. Journal of Finance 46, 555–576.",
  "Estrella, A., Mishkin, F. S. (1998). Predicting U.S. recessions: Financial variables as leading indicators. Review of Economics and Statistics 80, 45–61.",
  "Gertler, M., Lown, C. S. (1999). The information in the high-yield bond spread for the business cycle: Evidence and some implications. Oxford Review of Economic Policy 15(3), 132–150.",
  "Gilchrist, S., Zakrajšek, E. (2012). Credit spreads and business cycle fluctuations. American Economic Review 102, 1692–1720.",
  "Harvey, C. R. (1988). The real term structure and consumption growth. Journal of Financial Economics 22, 305–333.",
  "Mueller, P. (2009). Credit spreads and real activity. Working paper, London School of Economics.",
  "Newey, W. K., West, K. D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. Econometrica 55, 703–708.",
  "Newey, W. K., West, K. D. (1994). Automatic lag selection in covariance matrix estimation. Review of Economic Studies 61, 631–653.",
  "Rudebusch, G. D., Williams, J. C. (2009). Forecasting recessions: The puzzle of the enduring power of the yield curve. Journal of Business and Economic Statistics 27, 492–503.",
];

refs.forEach(r => {
  children.push(new Paragraph({
    children: [new TextRun({ text: r })],
    spacing: { after: 120, line: 360 },
    alignment: AlignmentType.JUSTIFIED,
    indent: { left: 360, hanging: 360 },
  }));
});

// ============================================================================
// BUILD DOCUMENT
// ============================================================================

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Times New Roman", size: 24 } } },
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

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/home/claude/yield_curve_manuscript.docx", buffer);
  console.log("Wrote /home/claude/yield_curve_manuscript.docx");
});
