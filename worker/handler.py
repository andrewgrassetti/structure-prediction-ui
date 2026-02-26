"""
RunPod serverless worker handler for Boltz-2 structure prediction.

The handler receives a prediction request, writes the YAML input to disk,
runs ``boltz predict``, collects the output files, and returns them as
base64-encoded strings.
"""
import base64
import subprocess
import tempfile
from pathlib import Path

import runpod


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_OUTPUT_CHARS = 4000  # Max chars of stdout/stderr included in error responses


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_param(job_input: dict, key: str, default, cast=None):
    """Retrieve a parameter from job_input, applying an optional type cast."""
    value = job_input.get(key, default)
    if cast is not None:
        try:
            value = cast(value)
        except (ValueError, TypeError):
            value = cast(default)
    return value

def _b64_file(path: Path) -> str:
    """Read a file and return its content as a base64 string."""
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("utf-8")


def _find_output(out_dir: Path, pattern: str) -> Path | None:
    """Return the first file matching a glob pattern under out_dir, or None."""
    matches = list(out_dir.rglob(pattern))
    return matches[0] if matches else None


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

def handler(event: dict) -> dict:
    """RunPod serverless entry point.

    Parameters
    ----------
    event:
        RunPod event dict. ``event["input"]`` contains the prediction parameters
        produced by :func:`utils.yaml_builder.build_prediction_payload`.

    Returns
    -------
    dict
        On success:  ``{"structure_b64": ..., "structure_filename": ...,
                        "confidence_json_b64": ..., "affinity_json_b64": ...}``
        On failure:  ``{"error": "..."}``
    """
    job_input = event.get("input", {})

    yaml_content: str = _get_param(job_input, "yaml_content", "")
    job_name: str = _get_param(job_input, "job_name", "prediction")
    model: str = _get_param(job_input, "model", "boltz2")
    recycling_steps: int = _get_param(job_input, "recycling_steps", 3, int)
    sampling_steps: int = _get_param(job_input, "sampling_steps", 200, int)
    diffusion_samples: int = _get_param(job_input, "diffusion_samples", 1, int)
    max_parallel_samples: int = _get_param(job_input, "max_parallel_samples", 5, int)
    step_scale: float = _get_param(job_input, "step_scale", 1.5, float)
    output_format: str = _get_param(job_input, "output_format", "mmcif")
    use_msa_server: bool = bool(_get_param(job_input, "use_msa_server", True))
    msa_server_url: str = _get_param(job_input, "msa_server_url", "https://api.colabfold.com")
    use_potentials: bool = bool(_get_param(job_input, "use_potentials", False))
    override: bool = bool(_get_param(job_input, "override", False))
    no_kernels: bool = bool(_get_param(job_input, "no_kernels", False))

    if not yaml_content:
        return {"error": "No yaml_content provided in job input."}

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Write input YAML
        input_file = tmp_path / f"{job_name}.yaml"
        input_file.write_text(yaml_content, encoding="utf-8")

        # Output directory
        out_dir = tmp_path / "output"
        out_dir.mkdir()

        # Build boltz predict command
        cmd = [
            "boltz", "predict", str(input_file),
            "--out_dir", str(out_dir),
            "--model", model,
            "--recycling_steps", str(recycling_steps),
            "--sampling_steps", str(sampling_steps),
            "--diffusion_samples", str(diffusion_samples),
            "--max_parallel_samples", str(max_parallel_samples),
            "--step_scale", str(step_scale),
            "--output_format", output_format,
        ]

        if use_msa_server:
            cmd += ["--use_msa_server", "--msa_server_url", msa_server_url]
        if use_potentials:
            cmd.append("--use_potentials")
        if override:
            cmd.append("--override")
        if no_kernels:
            cmd.append("--no_kernels")

        # Run prediction
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour max
            )
        except subprocess.TimeoutExpired:
            return {"error": "boltz predict timed out after 3600 seconds."}
        except FileNotFoundError:
            return {
                "error": (
                    "boltz executable not found. "
                    "Ensure boltz[cuda] is installed in the Docker image."
                )
            }

        if result.returncode != 0:
            return {
                "error": f"boltz predict failed (exit {result.returncode}).",
                "stderr": result.stderr[-MAX_OUTPUT_CHARS:],
                "stdout": result.stdout[-MAX_OUTPUT_CHARS:],
            }

        # Collect outputs
        response: dict = {}

        # Structure file (CIF or PDB)
        ext = "cif" if output_format == "mmcif" else "pdb"
        structure_file = _find_output(out_dir, f"*_model_0.{ext}")
        if structure_file:
            response["structure_b64"] = _b64_file(structure_file)
            response["structure_filename"] = structure_file.name

        # Confidence JSON
        conf_file = _find_output(out_dir, "confidence_*.json")
        if conf_file:
            response["confidence_json_b64"] = _b64_file(conf_file)

        # Affinity JSON (optional)
        aff_file = _find_output(out_dir, "affinity_*.json")
        if aff_file:
            response["affinity_json_b64"] = _b64_file(aff_file)

        if not structure_file:
            return {
                "error": "Prediction completed but no structure file was found.",
                "stdout": result.stdout[-MAX_OUTPUT_CHARS:],
                "stderr": result.stderr[-MAX_OUTPUT_CHARS:],
            }

        return response


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
