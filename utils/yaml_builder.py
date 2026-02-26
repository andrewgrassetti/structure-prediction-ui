"""
Builds Boltz-2 YAML input from parsed sequences and optional ligands.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import yaml

from utils.fasta_parser import ParsedSequence


@dataclass
class LigandEntry:
    """A small-molecule ligand defined by SMILES or CCD code."""
    chain_id: str
    smiles: Optional[str] = None
    ccd: Optional[str] = None

    def __post_init__(self):
        if not self.smiles and not self.ccd:
            raise ValueError(
                f"Ligand '{self.chain_id}' must have either a SMILES string or a CCD code."
            )


def build_boltz_yaml(
    sequences: List[ParsedSequence],
    ligands: Optional[List[LigandEntry]] = None,
    version: int = 1,
) -> str:
    """Convert parsed sequences (and optional ligands) to a Boltz-2 YAML string.

    Parameters
    ----------
    sequences:
        Protein/DNA/RNA chains parsed from FASTA input.
    ligands:
        Optional list of small-molecule ligands.
    version:
        YAML schema version (default 1).

    Returns
    -------
    str
        YAML string suitable for passing to ``boltz predict``.
    """
    seq_entries = []
    for seq in sequences:
        entry: dict = {}
        inner: dict = {"id": seq.chain_id, "sequence": seq.sequence}
        if seq.msa_path:
            inner["msa"] = seq.msa_path
        entry[seq.entity_type] = inner
        seq_entries.append(entry)

    if ligands:
        for lig in ligands:
            lig_inner: dict = {"id": lig.chain_id}
            if lig.smiles:
                lig_inner["smiles"] = lig.smiles
            elif lig.ccd:
                lig_inner["ccd"] = lig.ccd
            seq_entries.append({"ligand": lig_inner})

    doc = {"version": version, "sequences": seq_entries}
    return yaml.dump(doc, default_flow_style=False, sort_keys=False, allow_unicode=True)


def build_prediction_payload(
    yaml_content: str,
    job_name: str = "prediction",
    model: str = "boltz2",
    recycling_steps: int = 3,
    sampling_steps: int = 200,
    diffusion_samples: int = 1,
    max_parallel_samples: int = 5,
    step_scale: float = 1.5,
    output_format: str = "mmcif",
    use_msa_server: bool = True,
    msa_server_url: str = "https://api.colabfold.com",
    use_potentials: bool = False,
    override: bool = False,
    no_kernels: bool = False,
) -> dict:
    """Build the RunPod job input payload for a Boltz-2 prediction.

    Parameters
    ----------
    yaml_content:
        The Boltz-2 YAML input as a string.
    job_name:
        A short identifier used for output naming.
    model:
        ``"boltz2"`` (default) or ``"boltz1"``.
    recycling_steps:
        Number of recycling iterations (1–10).
    sampling_steps:
        Diffusion sampling steps (50–500).
    diffusion_samples:
        Number of diffusion samples per recycling (1–10).
    max_parallel_samples:
        Maximum samples processed in parallel.
    step_scale:
        Diffusion step scale factor.
    output_format:
        ``"mmcif"`` (default) or ``"pdb"``.
    use_msa_server:
        Whether to query the MSA server automatically.
    msa_server_url:
        URL of the ColabFold MSA server.
    use_potentials:
        Enable auxiliary potentials.
    override:
        Overwrite existing output files.
    no_kernels:
        Disable cuEquivariance kernels (for older GPUs).

    Returns
    -------
    dict
        Dictionary to be placed under the ``"input"`` key of the RunPod
        request body.
    """
    return {
        "yaml_content": yaml_content,
        "job_name": job_name,
        "model": model,
        "recycling_steps": recycling_steps,
        "sampling_steps": sampling_steps,
        "diffusion_samples": diffusion_samples,
        "max_parallel_samples": max_parallel_samples,
        "step_scale": step_scale,
        "output_format": output_format,
        "use_msa_server": use_msa_server,
        "msa_server_url": msa_server_url,
        "use_potentials": use_potentials,
        "override": override,
        "no_kernels": no_kernels,
    }
