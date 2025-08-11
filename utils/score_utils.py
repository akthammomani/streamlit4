from pathlib import Path
import base64, tempfile
from music21 import converter, musicxml
import streamlit as st, base64

def midi_to_musicxml_str(midi_path: str, max_measures: int | None = 16) -> str:
    s = converter.parse(midi_path)

    # Make clean measures + fix rhythms/tuplets/overlaps
    s = s.makeMeasures(inPlace=False)
    s = s.makeNotation(inPlace=False, betterRhythm=True)

    # Trim to keep rendering light (bump if you like)
    if max_measures:
        s = s.measures(1, max_measures)

    # Export to MusicXML (string, no temp files)
    exp = musicxml.m21ToXml.GeneralObjectExporter(s)
    xml_bytes = exp.parse()
    return xml_bytes.decode("utf-8", errors="ignore")


def render_musicxml_osmd(xml_str: str, height: int = 800, compact: bool = True, zoom: float = 1.0):
    
    mode = "compact" if compact else "default"
    b64 = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    html = f"""
<div id="osmd-wrap" style="width:100%; text-align:center;">
  <div id="osmd" style="display:inline-block;"></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
  const target = document.getElementById('osmd');
  function showErr(msg) {{
    target.innerHTML = '<pre style="white-space:pre-wrap;color:#b00;">'+msg+'</pre>';
  }}
  try {{
    const xml = atob("{b64}");
    const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(target, {{ autoResize:true }});
    osmd.setOptions({{ drawingParameters: '{mode}' }});
    osmd.load(xml)
      .then(() => {{
        try {{
          osmd.render();
          osmd.zoom = {zoom};
          const svg = target.querySelector('svg');
          if (svg) {{
            svg.style.maxWidth = '100%';
            svg.style.display  = 'inline-block';
          }}
        }} catch(e) {{ showErr('OSMD render error: ' + e); }}
      }})
      .catch(e => showErr('OSMD load error: ' + e));
  }} catch(e) {{ showErr('OSMD top-level error: ' + e); }}
</script>
"""
    st.components.v1.html(html, height=height, scrolling=True)
