"""
3D structure visualization helpers using py3Dmol / stmol.
"""
from __future__ import annotations

from typing import Optional

try:
    import py3Dmol
    PY3DMOL_AVAILABLE = True
except ImportError:
    PY3DMOL_AVAILABLE = False

try:
    import streamlit.components.v1 as components
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


PLDDT_COLOR_SCHEME = {
    "scheme": "bFactor",
    "gradient": "roygb",
    "min": 0,
    "max": 100,
}

STYLE_PRESETS = {
    "cartoon": {"cartoon": {"color": "spectrum"}},
    "plddt": {"cartoon": PLDDT_COLOR_SCHEME},
    "stick": {"stick": {}},
    "sphere": {"sphere": {}},
    "surface": {"surface": {"opacity": 0.7, "color": "white"}},
}


def render_structure(
    structure_data: str,
    fmt: str = "mmcif",
    style: str = "plddt",
    width: int = 800,
    height: int = 500,
    spin: bool = False,
    background_color: str = "0x1E1E1E",
) -> Optional[object]:
    """Render a molecular structure with py3Dmol.

    Parameters
    ----------
    structure_data:
        Raw CIF or PDB file content as a string.
    fmt:
        File format: ``"mmcif"`` or ``"pdb"``.
    style:
        One of the keys in :data:`STYLE_PRESETS` or ``"plddt"``.
    width:
        Viewer width in pixels.
    height:
        Viewer height in pixels.
    spin:
        Whether to enable auto-rotation.
    background_color:
        Hex background colour string (e.g. ``"0x1E1E1E"``).

    Returns
    -------
    py3Dmol.view or None
        The py3Dmol view object, or ``None`` if py3Dmol is unavailable.
    """
    if not PY3DMOL_AVAILABLE:
        return None

    view = py3Dmol.view(width=width, height=height)
    view.addModel(structure_data, fmt)

    selected_style = STYLE_PRESETS.get(style, STYLE_PRESETS["plddt"])

    if style == "plddt":
        view.setStyle(
            {},
            {
                "cartoon": {
                    "colorscheme": {
                        "prop": "b",
                        "gradient": "roygb",
                        "min": 0,
                        "max": 100,
                    }
                }
            },
        )
    else:
        view.setStyle({}, selected_style)

    view.setBackgroundColor(background_color)
    view.zoomTo()
    if spin:
        view.spin(True)

    return view


def embed_viewer_html(view) -> str:
    """Return raw HTML string for a py3Dmol view object.

    Parameters
    ----------
    view:
        A ``py3Dmol.view`` instance (from :func:`render_structure`).

    Returns
    -------
    str
        HTML snippet that can be embedded via ``st.components.v1.html``.
    """
    if view is None:
        return "<p>py3Dmol is not available.</p>"
    # py3Dmol does not expose a public HTML-export method; _make_html() is the
    # de-facto standard way to embed a view in external HTML contexts.
    return view._make_html()


def show_structure_in_streamlit(
    structure_data: str,
    fmt: str = "mmcif",
    style: str = "plddt",
    width: int = 700,
    height: int = 450,
    spin: bool = False,
) -> None:
    """Convenience wrapper that renders a structure and displays it via Streamlit.

    Parameters
    ----------
    structure_data:
        Raw CIF or PDB file content.
    fmt:
        ``"mmcif"`` or ``"pdb"``.
    style:
        Visualisation style preset.
    width:
        Viewer width in pixels.
    height:
        Viewer height in pixels.
    spin:
        Enable auto-rotation.
    """
    if not PY3DMOL_AVAILABLE:
        if STREAMLIT_AVAILABLE:
            import streamlit as st
            st.warning(
                "py3Dmol is not installed. Install it with: `pip install py3Dmol`"
            )
        return

    if not STREAMLIT_AVAILABLE:
        return

    import streamlit as st

    view = render_structure(
        structure_data, fmt=fmt, style=style, width=width, height=height, spin=spin
    )
    if view is None:
        st.warning("Failed to create py3Dmol viewer.")
        return

    html = embed_viewer_html(view)
    components.html(html, width=width, height=height)
