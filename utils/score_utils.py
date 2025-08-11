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

# utils/score_utils.py
def render_musicxml_osmd(xml_str: str, height: int = 620, compact: bool = False):
    
    uid  = "osmd_" + uuid.uuid4().hex
    mode = "compact" if compact else "default"
    b64  = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    html = f"""
<div id="{uid}-wrap" style="width:200%;">
  <div id="{uid}" style="width:200%;"></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
  const el  = document.getElementById("{uid}");
  const xml = atob("{b64}");

  // No autoResize. No observers. We will fit once and freeze.
  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {{
    autoResize: false, backend: "svg"
  }});
  osmd.setOptions({{
    drawingParameters: "{mode}",
    drawPartNames: false,
    drawTitle: false,
    pageFormat: "Endless"
  }});

  function fitOnceAndFreeze() {{
    // lock container width so later layout changes don't refire sizing
    const colW = el.getBoundingClientRect().width;
    el.style.width = colW + "px";

    // initial render to measure intrinsic score width
    osmd.render();
    const svg = el.querySelector("svg");
    if (!svg) return;

    const vb = svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal : null;
    const scoreW = vb && vb.width ? vb.width : svg.getBBox().width;

    // set zoom to fill container, render once more, then freeze sizes
    if (scoreW > 0 && colW > 0) {{
      osmd.zoom = (colW /* - 8 */) / scoreW;  // small padding
      osmd.render();
    }}

    // remove explicit width/height from SVG and set fixed px to stop reflows
    const finalSVG = el.querySelector("svg");
    if (finalSVG) {{
      finalSVG.removeAttribute("width");
      finalSVG.removeAttribute("height");
      finalSVG.style.width  = colW + "px";
      finalSVG.style.height = "auto";
      finalSVG.style.display = "block";
    }}
  }}

  osmd.load(xml).then(() => {{
    fitOnceAndFreeze();
    // no resize listeners or observers → no loops
  }});
</script>
"""
    st.components.v1.html(html, height=height, scrolling=True)
