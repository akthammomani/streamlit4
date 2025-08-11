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
# utils/score_utils.py
def render_musicxml_osmd(xml_str: str, height: int = 620, compact: bool = True):
    import streamlit as st, base64, uuid
    uid  = "osmd_" + uuid.uuid4().hex
    mode = "compact" if compact else "default"
    b64  = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    # This HTML and JavaScript has been updated to be simpler and more reliable.
    html = f"""
<div id="{uid}-wrap" style="width: 200%; height: 100%;">
  <div style="display:flex; gap:8px; align-items:center; margin:4px 0 8px;">
    <button id="{uid}-save-svg">Save SVG</button>
    <button id="{uid}-save-png">Save PNG</button>
  </div>
  <div id="{uid}" style="width: 200%; height: 100%;"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
  const el  = document.getElementById("{uid}");
  const xml = atob("{b64}");

  // 1. Enable autoResize, which is more reliable than manual resizing.
  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {{
    autoResize: true,
    backend: "svg"
  }});
  osmd.setOptions({{
    drawingParameters: "{mode}",
    drawPartNames: false,
    drawTitle: false,
    pageFormat: "Endless" // Endless format is required for auto-resizing to work well
  }});

  // 2. The rendering logic is now much simpler.
  //    We just load and render, and the library handles the rest.
  function render() {{
      osmd.load(xml).then(() => {{
          osmd.render();
      }});
  }}

  // We still use an IntersectionObserver to only render when the element is visible.
  const io = new IntersectionObserver((entries, obs) => {{
    if (entries.some(e => e.isIntersecting)) {{
      obs.disconnect();
      render();
    }}
  }}, {{ threshold: 0.1 }});
  io.observe(el);


  // --- Save SVG/PNG logic (unchanged from your original) ---
  function dl(name, blob) {{
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {{ URL.revokeObjectURL(a.href); a.remove(); }}, 1000);
  }}

  function saveSVG() {{
    const svg = el.querySelector("svg");
    if (!svg) return;
    const s = new XMLSerializer().serializeToString(svg);
    dl("score.svg", new Blob([s], {{type: "image/svg+xml;charset=utf-8"}}));
  }}

  function savePNG() {{
    const svg = el.querySelector("svg");
    if (!svg) return;
    const s = new XMLSerializer().serializeToString(svg);
    const vb = svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal : null;
    const w  = vb && vb.width  ? vb.width  : svg.getBBox().width;
    const h  = vb && vb.height ? vb.height : svg.getBBox().height;
    const img = new Image();
    img.onload = () => {{
      const scale = 2;
      const c = document.createElement("canvas");
      c.width  = Math.max(1, Math.round(w * scale));
      c.height = Math.max(1, Math.round(h * scale));
      const ctx = c.getContext("2d");
      ctx.setTransform(scale, 0, 0, scale, 0, 0);
      ctx.drawImage(img, 0, 0);
      c.toBlob(b => dl("score.png", b), "image/png");
    }};
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(s);
  }}

  document.getElementById("{uid}-save-svg").addEventListener("click", saveSVG);
  document.getElementById("{uid}-save-png").addEventListener("click", savePNG);
</script>
"""
    # 3. Set scrolling=False. Since the content now fits, we don't need scrollbars.
    st.components.v1.html(html, height=height, scrolling=False)
