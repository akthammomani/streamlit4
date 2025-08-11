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

def render_musicxml_osmd(xml_str: str, height: int = 620, compact: bool = True):
    import streamlit as st, base64, uuid
    uid  = "osmd_" + uuid.uuid4().hex
    mode = "compact" if compact else "default"
    b64  = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")

    # This version includes a CSS reset and a forced delay to fix the sizing.
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden; /* Hide any accidental scrollbars */
    }}
  </style>
</head>
<body>

<div id="{uid}-wrap" style="width: 100%; height: 100%; display: flex; flex-direction: column;">
  <div style="padding: 4px 0 8px 0;">
    <button id="{uid}-save-svg">Save SVG</button>
    <button id="{uid}-save-png">Save PNG</button>
  </div>
  <div id="{uid}" style="width: 100%; flex-grow: 1;"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.4/build/opensheetmusicdisplay.min.js"></script>
<script>
  const el  = document.getElementById("{uid}");
  const xml = atob("{b64}");

  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(el, {{
    autoResize: false, // We are back to manual resize for more control
    backend: "svg"
  }});
  osmd.setOptions({{
    drawingParameters: "{mode}",
    drawPartNames: false,
w    drawTitle: false,
    pageFormat: "Endless"
  }});

  function tryRender() {{
    osmd.load(xml).then(() => {{
      osmd.render(); // Render once to get the natural score width
      const svg = el.querySelector("svg");
      if (!svg) return;

      const scoreWidth = svg.getBBox().width;
      const containerWidth = el.clientWidth;
      
      if (scoreWidth > 0 && containerWidth > 0) {{
        const zoom = containerWidth / scoreWidth;
        osmd.zoom = zoom;
        osmd.render(); // Re-render with the correct zoom to fit the container
      }}
    }});
  }}

  // We use an IntersectionObserver to know when the element is visible
  const observer = new IntersectionObserver((entries, obs) => {{
    if (entries[0].isIntersecting) {{
      // 2. THIS IS THE KEY FIX: Wait 100ms before rendering.
      // This gives Streamlit's layout time to stabilize.
      setTimeout(tryRender, 100);
      obs.disconnect(); // Stop observing after we've triggered the render
    }}
  }}, {{ threshold: 0.1 }});

  observer.observe(el);

  // --- Save SVG/PNG logic (unchanged) ---
  function dl(name, blob) {{
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {{ URL.revokeObjectURL(a.href); a.remove(); }}, 1000);
  }}
  function saveSVG() {{
    const svg = el.querySelector("svg"); if (!svg) return;
    const s = new XMLSerializer().serializeToString(svg);
    dl("score.svg", new Blob([s], {{type: "image/svg+xml;charset=utf-8"}}));
  }}
  function savePNG() {{
    const svg = el.querySelector("svg"); if (!svg) return;
    const s = new XMLSerializer().serializeToString(svg);
    const vb = svg.viewBox.baseVal;
    const img = new Image();
    img.onload = () => {{
      const scale = 2; const c = document.createElement("canvas");
      c.width = Math.max(1, Math.round(vb.width * scale));
      c.height = Math.max(1, Math.round(vb.height * scale));
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

</body>
</html>
"""
    # Set scrolling=False. The content should now fit perfectly.
    st.components.v1.html(html, height=height, scrolling=False)
