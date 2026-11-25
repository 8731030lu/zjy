#!/usr/bin/env python3
"""Build an editable academic PPTX (+ rendered previews + result.json) from slides.json.

This script is deterministic: it reads structured slide content (produced by the
agent), assembles a standard, editable .pptx, writes speaker notes and evidence
footers, renders PDF/PNG previews when an Office renderer is available, and
writes result.json that mirrors every field in the case's output_contract.

Nothing here fabricates scientific data: missing inputs are reported as
"unavailable"/"unable" and the deliverable is marked partial, never invented.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
from typing import Any

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    HAVE_PPTX = True
except Exception:  # pragma: no cover - exercised when python-pptx is absent
    HAVE_PPTX = False

STATUS_OK = "success"
STATUS_PARTIAL = "partial"
STATUS_UNABLE = "unable"

DARK = RGBColor(0x1F, 0x2A, 0x44)
GREY = RGBColor(0x6B, 0x72, 0x80)
ACCENT = RGBColor(0x2E, 0x5E, 0xAA)


def load_json(path: str, default: Any) -> Any:
    if not path or not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def read_case(case_path: str) -> dict:
    case = load_json(case_path, {})
    if not isinstance(case, dict):
        case = {}
    contract = case.get("output_contract", [])
    if isinstance(contract, dict):
        contract = list(contract.keys())
    if not isinstance(contract, list):
        contract = []
    return {
        "case_id": case.get("case_id") or case.get("id") or "unknown",
        "output_contract": contract,
        "paper_path": case.get("paper_path") or case.get("paper") or case.get("material"),
        "task": case.get("task") or case.get("instruction") or case.get("description"),
    }


def read_slides(path: str) -> dict:
    data = load_json(path, {})
    if not isinstance(data, dict):
        data = {}
    return data


def _fmt_anchor(b: dict) -> str:
    anchor = (b or {}).get("anchor")
    if anchor:
        return str(anchor)
    return "未定位"


def build_pptx(slides: dict, out_pptx: str) -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    paper = slides.get("paper") or {}
    summary = slides.get("summary") or {}
    items = slides.get("slides") or []
    case_id = slides.get("case_id") or ""

    title_layout = prs.slide_layouts[5]  # Title Only
    blank = prs.slide_layouts[6]         # Blank

    def add_title(slide, text):
        ph = slide.shapes.title
        if ph is not None:
            ph.text = text
            for p in ph.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(30)
                    r.font.bold = True
                    r.font.color.rgb = DARK

    def add_body(slide, bullets, top=1.35):
        box = slide.shapes.add_textbox(Inches(0.6), Inches(top), Inches(12.1), Inches(5.2))
        tf = box.text_frame
        tf.word_wrap = True
        first = True
        for b in bullets:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            text = (b or {}).get("text") or ""
            anchor = _fmt_anchor(b)
            status = (b or {}).get("evidence_status") or "reported"
            run = p.add_run()
            run.text = "• " + text
            run.font.size = Pt(18)
            run.font.color.rgb = RGBColor(0x20, 0x24, 0x2A)
            if status in ("unreported", "uncertain", "inferred"):
                meta = p.add_run()
                meta.text = f"  〔{status}·{anchor}〕"
                meta.font.size = Pt(12)
                meta.font.color.rgb = GREY
            p.space_after = Pt(10)

    def add_footer(slide, section, anchors):
        foot = slide.shapes.add_textbox(Inches(0.6), Inches(6.95), Inches(12.1), Inches(0.45))
        tf = foot.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = (f"来源章节：{section}    ·    证据锚点：" +
                    "；".join(_fmt_anchor(a) for a in anchors))
        run.font.size = Pt(10)
        run.font.color.rgb = GREY

    def add_notes(slide, text):
        if text:
            slide.notes_slide.notes_text_frame.text = text

    # 1) Title slide
    s = prs.slides.add_slide(title_layout)
    add_title(s, paper.get("title") or "（论文标题）")
    sub = slide_add_text(s, blank, top=2.2, size=18, color=GREY)
    sub.text = " · ".join(filter(None, [
        paper.get("authors") or "", paper.get("venue") or "", str(paper.get("year") or ""),
        paper.get("doi") or ""])) or "（作者 / 期刊 / 年份）"
    if case_id:
        add_footer(s, f"case_id: {case_id}", [])

    # 2) Overview slide
    s = prs.slides.add_slide(title_layout)
    add_title(s, "概览：研究问题与主要结论")
    overview_bullets = [
        {"text": f"研究问题：{summary.get('research_question') or '（未识别）'}",
         "anchor": summary.get("rq_anchor"), "evidence_status": summary.get("rq_status", "reported")},
        {"text": f"主要发现：{summary.get('key_finding') or '（未识别）'}",
         "anchor": summary.get("finding_anchor"), "evidence_status": summary.get("finding_status", "reported")},
        {"text": f"贡献：{summary.get('contribution') or '（未识别）'}",
         "anchor": summary.get("contrib_anchor"), "evidence_status": summary.get("contrib_status", "reported")},
    ]
    add_body(s, overview_bullets, top=1.5)
    add_footer(s, "概览", [summary.get("rq_anchor"), summary.get("finding_anchor")])
    add_notes(s, "开场讲稿：先用一句话说清这篇论文要解决什么问题、得到什么结论、贡献在哪。")

    # 3) Section slides (follow paper order)
    for it in items:
        s = prs.slides.add_slide(title_layout)
        title = it.get("title") or it.get("section") or "（未命名）"
        add_title(s, title)
        bullets = it.get("bullets") or []
        add_body(s, bullets, top=1.4)
        add_footer(s, it.get("section") or title, bullets)
        add_notes(s, it.get("speaker_notes") or "")

    # 4) Limitations slide (always present)
    s = prs.slides.add_slide(title_layout)
    add_title(s, "局限与证据边界")
    lim = slides.get("limitations") or []
    lim_bullets = [{"text": (x or {}).get("text") or "",
                    "anchor": (x or {}).get("anchor"),
                    "evidence_status": (x or {}).get("status", "unreported")} for x in lim]
    if not lim_bullets:
        lim_bullets = [{"text": "（未识别出明确的局限说明）", "anchor": None, "evidence_status": "unreported"}]
    add_body(s, lim_bullets, top=1.4)
    add_footer(s, "局限", lim_bullets)
    add_notes(s, "讲稿：明确说明哪些结论是原文报告的、哪些是推断的、哪些原文未报告或无法判断。")

    os.makedirs(os.path.dirname(os.path.abspath(out_pptx)) or ".", exist_ok=True)
    prs.save(out_pptx)


def slide_add_text(slide, layout, top=1.0, size=16, color=RGBColor(0x33, 0x33, 0x33)):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(top), Inches(12.1), Inches(1.0))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.font.size = Pt(size)
    run.font.color.rgb = color
    return run


def write_notes_md(slides: dict, out_md: str) -> None:
    paper = slides.get("paper") or {}
    summary = slides.get("summary") or {}
    items = slides.get("slides") or []
    lines = []
    lines.append(f"# {paper.get('title') or '论文结构化笔记'}")
    if paper.get("authors"):
        lines.append(f"\n**作者**：{paper['authors']}")
    if paper.get("venue") or paper.get("year"):
        lines.append(f"**出处**：{paper.get('venue') or ''} {paper.get('year') or ''}".strip())
    lines.append("\n## 概览")
    lines.append(f"- 研究问题：{summary.get('research_question') or '未识别'}")
    lines.append(f"- 主要发现：{summary.get('key_finding') or '未识别'}")
    lines.append(f"- 贡献：{summary.get('contribution') or '未识别'}")
    for it in items:
        lines.append(f"\n## {it.get('section') or it.get('title') or '未命名'}")
        for b in (it.get("bullets") or []):
            anchor = b.get("anchor") or "未定位"
            status = b.get("evidence_status") or "reported"
            lines.append(f"- {b.get('text') or ''}  〔{status}·{anchor}〕")
        if it.get("speaker_notes"):
            lines.append(f"\n> 讲稿：{it['speaker_notes']}")
    lim = slides.get("limitations") or []
    if lim:
        lines.append("\n## 局限与证据边界")
        for x in lim:
            lines.append(f"- {x.get('text') or ''}  〔{x.get('status', 'unreported')}·{x.get('anchor') or '未定位'}〕")
    os.makedirs(os.path.dirname(os.path.abspath(out_md)) or ".", exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def render_previews(pptx_path: str, out_dir: str) -> dict:
    result = {"pdf": None, "pngs": [], "renderer": None, "error": None}
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        result["error"] = "office-renderer (soffice/libreoffice) not found"
        return result
    pdf_dir = os.path.join(out_dir, "_pdf_tmp")
    os.makedirs(pdf_dir, exist_ok=True)
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", pdf_dir, pptx_path],
            check=True, capture_output=True, timeout=300,
        )
    except Exception as exc:
        result["error"] = f"pptx->pdf failed: {exc}"
        return result
    base = os.path.splitext(os.path.basename(pptx_path))[0]
    pdf_path = os.path.join(pdf_dir, base + ".pdf")
    if not os.path.exists(pdf_path):
        result["error"] = "soffice ran but produced no PDF"
        return result
    final_pdf = os.path.join(out_dir, "slides.pdf")
    shutil.move(pdf_path, final_pdf)
    result["pdf"] = os.path.basename(final_pdf)
    result["renderer"] = soffice

    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        png_dir = os.path.join(out_dir, "slides_preview")
        os.makedirs(png_dir, exist_ok=True)
        try:
            subprocess.run(
                [pdftoppm, "-png", "-r", "90", final_pdf, os.path.join(png_dir, "page")],
                check=True, capture_output=True, timeout=300,
            )
            result["pngs"] = sorted(
                os.path.basename(f) for f in os.listdir(png_dir) if f.endswith(".png")
            )
        except Exception as exc:
            result["error"] = (result["error"] or "") + f" pdf->png failed: {exc}"
    return result


def _best_value(*candidates: Any) -> Any:
    for c in candidates:
        if c not in (None, "", []):
            return c
    return None


def write_result(case: dict, slides: dict, artifacts: dict, status: str, reason: str,
                 out_json: str) -> dict:
    paper = slides.get("paper") or {}
    summary = slides.get("summary") or {}
    items = slides.get("slides") or []
    lim = slides.get("limitations") or []

    methods = [b for it in items if (it.get("section") or "").lower() in
               ("methods", "method", "实验方法", "方法", "实验", "experiments", "实验设置")
               for b in (it.get("bullets") or [])]
    findings = [b for it in items if (it.get("section") or "").lower() in
                ("results", "result", "结果", "讨论", "discussion", "conclusion", "结论")
                for b in (it.get("bullets") or [])]

    field_values = {
        "research_question": summary.get("research_question"),
        "key_finding": summary.get("key_finding"),
        "contribution": summary.get("contribution"),
        "methods": methods or summary.get("methods"),
        "findings": findings or summary.get("findings"),
        "results": findings or summary.get("results"),
        "data": summary.get("data"),
        "conclusion": summary.get("conclusion") or (findings[-1].get("text") if findings else None),
        "limitations": [x.get("text") for x in lim] or summary.get("limitations"),
        "evidence": [b.get("anchor") for it in items for b in (it.get("bullets") or [])],
        "sources": [b.get("anchor") for it in items for b in (it.get("bullets") or [])],
    }

    result: dict[str, Any] = {"case_id": case["case_id"]}
    for key in case["output_contract"]:
        k = str(key)
        val = _best_value(field_values.get(k), field_values.get(k.lower()),
                          summary.get(k), paper.get(k))
        result[k] = val if val is not None else None

    result.update({
        "status": status,
        "reason": reason,
        "paper": paper,
        "sections": [{"section": it.get("section"), "title": it.get("title"),
                      "evidence": [b.get("anchor") for b in (it.get("bullets") or [])]}
                     for it in items],
        "uncertainty": {
            "unreported": [b.get("text") for it in items for b in (it.get("bullets") or [])
                           if (b.get("evidence_status") in ("unreported",))],
            "inferred": [b.get("text") for it in items for b in (it.get("bullets") or [])
                         if (b.get("evidence_status") == "inferred")],
            "limitations": [x.get("text") for x in lim],
        },
        "artifacts": artifacts,
        "change_records": [
            {"what": "built editable PPTX + notes + evidence anchors from slides.json",
             "why": "produce re-usable, evidence-linked notes per the task contract"},
            {"what": "rendered PDF/PNG previews" if artifacts.get("pdf")
             else "rendering unavailable; preview not produced",
             "why": "make editable output inspectable"},
        ],
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    })
    os.makedirs(os.path.dirname(os.path.abspath(out_json)) or ".", exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Build editable PPTX + previews + result.json.")
    ap.add_argument("--case", required=True, help="path to /input/case.json")
    ap.add_argument("--slides", required=True, help="path to slides.json (structured slide content)")
    ap.add_argument("--out", required=True, help="output dir, e.g. /app/output")
    args = ap.parse_args()

    case = read_case(args.case)
    slides = read_slides(args.slides)
    if not slides.get("case_id"):
        slides["case_id"] = case["case_id"]
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    artifacts: dict[str, Any] = {}
    reasons = []
    status = STATUS_OK

    if HAVE_PPTX:
        pptx_path = os.path.join(out_dir, "slides.pptx")
        try:
            build_pptx(slides, pptx_path)
            artifacts["pptx"] = "slides.pptx"
        except Exception as exc:
            reasons.append(f"pptx generation failed: {exc}")
            status = STATUS_PARTIAL
    else:
        reasons.append("python-pptx not installed; slides.pptx not generated")
        status = STATUS_PARTIAL
        artifacts["pptx"] = None

    notes_path = os.path.join(out_dir, "paper_notes.md")
    try:
        write_notes_md(slides, notes_path)
        artifacts["notes"] = "paper_notes.md"
    except Exception as exc:
        reasons.append(f"notes generation failed: {exc}")

    slides_json_path = os.path.join(out_dir, "slides.json")
    try:
        with open(slides_json_path, "w", encoding="utf-8") as f:
            json.dump(slides, f, ensure_ascii=False, indent=2)
        artifacts["slides_json"] = "slides.json"
    except Exception as exc:
        reasons.append(f"slides.json write failed: {exc}")

    if HAVE_PPTX and os.path.exists(os.path.join(out_dir, "slides.pptx")):
        preview = render_previews(os.path.join(out_dir, "slides.pptx"), out_dir)
        if preview.get("pdf"):
            artifacts["pdf"] = preview["pdf"]
            artifacts["png_previews"] = preview["pngs"]
        else:
            reasons.append(preview.get("error") or "preview rendering unavailable")
            artifacts["pdf"] = None
            artifacts["png_previews"] = []
            if status == STATUS_OK:
                status = STATUS_PARTIAL

    if status == STATUS_OK and not reasons:
        reason = "完整产出：可编辑 PPTX + 讲稿备注 + 证据锚点 + 渲染预览 + result.json"
    elif status == STATUS_PARTIAL:
        reason = "部分完成：" + "；".join(reasons)
    else:
        reason = "；".join(reasons)

    result = write_result(case, slides, artifacts, status, reason,
                          os.path.join(out_dir, "result.json"))
    print(json.dumps({"status": status, "case_id": case["case_id"],
                      "artifacts": artifacts, "reason": reason,
                      "output_contract_fields": case["output_contract"]},
                     ensure_ascii=False))
    return 0 if status != STATUS_UNABLE else 2


if __name__ == "__main__":
    sys.exit(main())
