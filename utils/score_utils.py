from pathlib import Path
import base64, tempfile
from music21 import converter
import streamlit as st, base64, uuid

def midi_to_musicxml_str(midi_path: str) -> str:
    """Convert a MIDI file to MusicXML text using music21."""
    s = converter.parse(midi_path)
    with tempfile.NamedTemporaryFile(suffix=".musicxml", delete=False) as tmp:
        out_path = tmp.name
    s.write("musicxml", fp=out_path)
    xml = Path(out_path).read_text(encoding="utf-8", errors="ignore")
    try:
        Path(out_path).unlink(missing_ok=True)
    except Exception:
        pass
    return xml

def render_musicxml_osmd(xml_str: str, height: int = 620, compact: bool = True):
    import streamlit as st, base64, uuid
    from string import Template

    uid  = "osmd_" + uuid.uuid4().hex
    mode = "compact" if compact else "default"
    b64  = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    html = Template(r"""
<div id="${uid}-wrap" style="width:100%;">
  <div style="display:flex; gap:8px; align-items:center; margin:0 0 8px;">
    <button id="${uid}-save-svg">Save SVG</button>
    <button id="${uid}-save-png">Save PNG</button>
  </div>
  <div id="${uid}" style="width:100%;"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
  const el  = document.getElementById("${uid}");
  const xml = atob("${b64}");

  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {
    autoResize: false,
    backend: "svg"
  });
  osmd.setOptions({
    drawingParameters: "${mode}",
    drawPartNames: false,
    drawTitle: false,
    pageFormat: "Endless"
  });

  // Render only after the element is visible and has a stable width
  let rendered = false;
  function waitForWidthAndRender() {
    if (rendered) return;
    const w = el.clientWidth;
    if (!w || w < 240) { requestAnimationFrame(waitForWidthAndRender); return; }

    osmd.load(xml).then(() => {
      // initial render to get intrinsic width
      osmd.render();
      fitToColumn(2);   // 2-step refine
      rendered = true;
    });
  }

  function fitToColumn(refines=1) {
    const svg = el.querySelector("svg");
    if (!svg) return;

    const vb = svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal : null;
    const scoreW = vb && vb.width ? vb.width : svg.getBBox().width;

    // usable content width inside the Streamlit column (leave tiny gutter)
    const style = getComputedStyle(el);
    const pad   = (parseFloat(style.paddingLeft)||0) + (parseFloat(style.paddingRight)||0);
    const colW  = Math.max(0, el.clientWidth - pad - 8);

    if (scoreW > 0 && colW > 0) {
      const targetZoom = Math.max(0.05, Math.min(colW / scoreW, 5));
      if (Math.abs(targetZoom - osmd.zoom) > 0.01) {
        osmd.zoom = targetZoom;
        osmd.render();
      }
    }

    // let CSS handle width from now on
    const finalSVG = el.querySelector("svg");
    if (finalSVG) {
      finalSVG.removeAttribute("width");
      finalSVG.removeAttribute("height");
      finalSVG.style.width  = "100%";
      finalSVG.style.height = "auto";
      finalSVG.style.display = "block";
    }

    // one or two small refinements help when fonts load late
    if (refines > 0) setTimeout(() => fitToColumn(refines - 1), 120);
  }

  // Start when the tab actually shows this element
  const io = new IntersectionObserver((entries, obs) => {
    if (entries.some(e => e.isIntersecting)) { obs.disconnect(); waitForWidthAndRender(); }
  }, { threshold: 0.1 });
  io.observe(el);

  // --- Save buttons ---
  function dl(name, blob) { const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; document.body.appendChild(a); a.click(); setTimeout(()=>{URL.revokeObjectURL(a.href); a.remove();},1000); }
  document.getElementById("${uid}-save-svg").onclick = () => {
    const svg = el.querySelector("svg"); if (!svg) return;
    const s = new XMLSerializer().serializeToString(svg);
    dl("score.svg", new Blob([s], {type:"image/svg+xml;charset=utf-8"}));
  };
  document.getElementById("${uid}-save-png").onclick = () => {
    const svg = el.querySelector("svg"); if (!svg) return;
    const s = new XMLSerializer().serializeToString(svg);
    const vb = svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal : null;
    const w  = vb && vb.width  ? vb.width  : svg.getBBox().width;
    const h  = vb && vb.height ? vb.height : svg.getBBox().height;
    const img = new Image();
    img.onload = () => {
      const scale = 2;
      const c = document.createElement("canvas");
      c.width  = Math.max(1, Math.round(w * scale));
      c.height = Math.max(1, Math.round(h * scale));
      const ctx = c.getContext("2d");
      ctx.setTransform(scale,0,0,scale,0,0);
      ctx.drawImage(img,0,0);
      c.toBlob(b => dl("score.png", b), "image/png");
    };
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(s);
  };
</script>
""").substitute(uid=uid, b64=b64, mode=mode)

    st.components.v1.html(html, height=height, scrolling=False)
