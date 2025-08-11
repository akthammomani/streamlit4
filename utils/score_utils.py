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


def render_musicxml_osmd(xml_str: str, height: int = 700, compact=True, zoom: float = 1.0):
    import streamlit as st, base64
    mode = "compact" if compact else "default"
    b64 = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    html = f"""
<div id="osmd-outer" style="width:100%; text-align:center;">
  <div id="osmd-container" style="display:inline-block;"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
try {{
  const xml = atob("{b64}");
  const el = document.getElementById('osmd-container');
  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {{ autoResize: true }});
  osmd.setOptions({{ drawingParameters: '{mode}' }});
  osmd.load(xml).then(() => {{
      osmd.render();
      osmd.zoom = {zoom};
      const svg = el.querySelector('svg');
      if (svg) {{
        svg.style.maxWidth = '100%';
        svg.style.display = 'inline-block';
      }}
  }});
}} catch(e) {{
  const outer = document.getElementById('osmd-outer');
  if (outer) outer.innerHTML = '<pre style="white-space:pre-wrap;color:#b00;">'+e+'</pre>';
}}
</script>
"""
    st.components.v1.html(html, height=height, scrolling=True)

