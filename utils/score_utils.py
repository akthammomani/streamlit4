from pathlib import Path
import base64, tempfile
from music21 import converter, musicxml
import streamlit as st, base64

def midi_to_musicxml_str(midi_path: str, max_measures: int | None = 16) -> str:
    s = converter.parse(midi_path)

    # Clean & measure-ize (version-safe)
    s = s.makeMeasures(inPlace=False)
    s = s.makeNotation(inPlace=False)   # <- no betterRhythm kwarg

    # Keep rendering light
    if max_measures:
        s = s.measures(1, max_measures)

    # Export to MusicXML (string)
    exp = musicxml.m21ToXml.GeneralObjectExporter(s)
    xml_bytes = exp.parse()
    return xml_bytes.decode("utf-8", errors="ignore")


def render_musicxml_osmd(xml_str: str, height: int = 800, compact: bool = True, zoom: float = 1.0):
    import streamlit as st, base64
    mode = "compact" if compact else "default"
    b64 = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    html = f"""
<div id="status" style="font:12px monospace;color:#666;margin-bottom:6px;"></div>
<div id="osmd-wrap" style="width:100%; text-align:center;">
  <div id="osmd-container" style="display:inline-block;"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
  const say=(t,c)=>{{const s=document.getElementById('status'); s.textContent=t; if(c) s.style.color=c; }};
  try {{
    const xml = atob("{b64}");
    const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(
      document.getElementById('osmd-container'), {{ autoResize: true }}
    );
    osmd.setOptions({{ drawingParameters: '{mode}' }});
    osmd.load(xml).then(() => {{
      osmd.render();
      osmd.zoom = {zoom};
      const svg = document.querySelector('#osmd-container svg');
      if (svg) {{
        svg.style.maxWidth = '100%';
        svg.style.display  = 'inline-block';  // centers with the wrapper
      }}
      say('');
    }}).catch(e => say('OSMD load error: ' + e, '#b00'));
  }} catch(e) {{
    say('Top-level error: ' + e, '#b00');
  }}
</script>
"""
    st.components.v1.html(html, height=height, scrolling=True)

