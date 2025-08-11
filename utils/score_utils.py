from pathlib import Path
import base64, tempfile
from music21 import converter, musicxml

def midi_to_musicxml_str(midi_path: str, max_measures: int | None = None) -> str:
    s = converter.parse(midi_path)

    # (optional) keep it light and consistent
    s = s.makeMeasures(inPlace=False)
    if max_measures:
        s = s.measures(1, max_measures)

    # robust exporter -> string (no temp file)
    exp = musicxml.m21ToXml.GeneralObjectExporter(s)
    xml_bytes = exp.parse()          # bytes
    return xml_bytes.decode("utf-8", errors="ignore")


def render_musicxml_osmd(xml_str: str, height: int = 800, compact: bool = True, zoom: float = 1.0):
    import streamlit as st, base64
    mode = "compact" if compact else "default"
    b64 = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    html = f"""
<div id="osmd-wrap" style="width:100%; text-align:center;">
  <div id="osmd" style="display:inline-block;"></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js"></script>
<script>
  const xml = atob("{b64}");
  const el  = document.getElementById('osmd');
  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {{ autoResize:true }});
  osmd.setOptions({{ drawingParameters: '{mode}' }});

  osmd.load(xml).then(() => {{
      osmd.render();
      osmd.zoom = {zoom};
      const svg = el.querySelector('svg');
      if (svg) {{
        svg.style.maxWidth = '100%';
        svg.style.display  = 'inline-block';
      }}
  }}).catch(e => {{
      el.innerHTML = '<pre style="white-space:pre-wrap;color:#b00;">OSMD load error: '+e+'</pre>';
  }});
</script>
"""
    st.components.v1.html(html, height=height, scrolling=True)
