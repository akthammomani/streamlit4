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
    import streamlit as st, base64, uuid
    mode = "compact" if compact else "default"
    b64 = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")
    uid = "osmd_" + uuid.uuid4().hex

    html = f"""
<div id="{uid}_wrap" style="width:100%; text-align:center;">
  <div id="{uid}_msg" style="font:13px monospace;color:#555;margin:6px 0;">loading…</div>
  <div id="{uid}" style="display:inline-block;"></div>
</div>

<script>
  const XML_B64 = "{b64}";
  const MODE    = "{mode}";
  const ZOOM    = {zoom};
  const el  = document.getElementById("{uid}");
  const msg = document.getElementById("{uid}_msg");
  const say = (t, c) => {{ msg.textContent = t; if (c) msg.style.color = c; }};

  function ensureOSMD() {{
    return new Promise((resolve, reject) => {{
      if (window.opensheetmusicdisplay) return resolve();
      const srcs = [
        "https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js",
        "https://unpkg.com/opensheetmusicdisplay@1.9.0/build/opensheetmusicdisplay.min.js"
      ];
      const loadNext = (i) => {{
        if (i >= srcs.length) return reject("Failed to load OSMD from CDNs");
        const s = document.createElement("script");
        s.src = srcs[i];
        s.onload = () => resolve();
        s.onerror = () => loadNext(i+1);
        document.body.appendChild(s);
      }};
      loadNext(0);
    }});
  }}

  function renderXML() {{
    const xml = atob(XML_B64);
    const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {{ autoResize: true }});
    osmd.setOptions({{ drawingParameters: MODE }});
    return osmd.load(xml).then(() => {{
      osmd.render();
      osmd.zoom = ZOOM;
      const svg = el.querySelector("svg");
      if (svg) {{ svg.style.maxWidth = "100%"; svg.style.display = "inline-block"; }}
      say(""); // clear status
    }});
  }}

  ensureOSMD()
    .then(() => {{ say("rendering…"); return renderXML(); }})
    .catch(e => say(String(e), "#b00"));
</script>
"""
    st.components.v1.html(html, height=height, scrolling=True)
