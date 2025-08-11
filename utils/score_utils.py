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

def render_musicxml_osmd(xml_str: str, height: int = 700, compact=True):
    """Render MusicXML in Streamlit using OpenSheetMusicDisplay."""
    import streamlit as st
    mode = "compact" if compact else "default"
    b64 = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")
    html = f"""
<div id="osmd-container"></div>
<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
  const xml = atob("{b64}");
  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(
    document.getElementById('osmd-container'),
    {{ drawingParameters: '{mode}', autoResize: true }}
  );
  osmd
    .load(xml)
    .then(() => osmd.render());
</script>
<style>
  #osmd-container {{ width: 100%; }}
</style>
"""
    st.components.v1.html(html, height=height, scrolling=True)
