from pathlib import Path
import base64, tempfile
from music21 import converter
import streamlit as st

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
    uid  = "osmd_" + uuid.uuid4().hex
    mode = "compact" if compact else "default"
    b64  = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    html = f"""
<div id="{uid}-wrap" style="width:100%;">
  <div id="{uid}" style="width:100%;"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
  const el  = document.getElementById("{uid}");
  const xml = atob("{b64}");

  // 1) No autoResize; we'll scale via CSS so no render loops
  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {{
    autoResize: false, backend: "svg"
  }});
  osmd.setOptions({{
    drawingParameters: "{mode}",
    drawPartNames: false,
    drawTitle: false,
    pageFormat: "Endless"
  }});

  function cssFill() {{
    const svg = el.querySelector("svg");
    if (!svg) return;
    // remove fixed size so CSS can stretch it
    svg.removeAttribute("width");
    svg.removeAttribute("height");
    svg.style.width  = "100%";
    svg.style.height = "auto";
    svg.style.display = "block";
  }}

  osmd.load(xml).then(() => {{
    osmd.render();   // one render only
    cssFill();

    // Cheap, debounced resize (no osmd.render)
    let t = null;
    window.addEventListener("resize", () => {{
      clearTimeout(t);
      t = setTimeout(cssFill, 120);
    }});
  }});
</script>
"""
    st.components.v1.html(html, height=height, scrolling=True)
