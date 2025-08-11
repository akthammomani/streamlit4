from pathlib import Path
import base64, tempfile
from music21 import converter

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

def render_musicxml_osmd(xml_str: str, height: int = 700, compact: bool = True):
    import streamlit as st, base64, uuid
    uid  = "osmd_" + uuid.uuid4().hex
    mode = "compact" if compact else "default"
    b64  = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    html = f"""
<div id="{uid}" style="width:100%;"></div>
<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
  const el  = document.getElementById("{uid}");
  const xml = atob("{b64}");

  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {{
    autoResize: true,
    backend: "svg"
  }});
  osmd.setOptions({{
    drawingParameters: "{mode}",
    drawPartNames: false,   // remove left labels → no gutter
    drawTitle: false,
    pageFormat: "Endless"
  }});

  function fitWidth() {{
    osmd.render();
    const svg = el.querySelector("svg");
    if (!svg) return;

    // compute score's intrinsic width (from viewBox or bbox)
    const vb = svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal : null;
    const scoreW = vb && vb.width ? vb.width : svg.getBBox().width;
    const colW   = el.clientWidth;
    if (scoreW > 0 && colW > 0) {{
      osmd.zoom = (colW - 16) / scoreW;   // small padding
      osmd.render();
    }}
    svg.style.width = "100%";
    svg.style.height = "auto";
    svg.style.display = "block";
  }}

  osmd.load(xml).then(() => {{
    fitWidth();
    new ResizeObserver(fitWidth).observe(el);  // keep fitting on resize
  }});
</script>
"""
    st.components.v1.html(html, height=height, scrolling=True)
