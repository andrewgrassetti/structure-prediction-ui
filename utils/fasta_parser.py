"""
FASTA parser and input builder for Boltz-2 structure prediction.

Supported header formats
------------------------
- ``>CHAIN_ID|ENTITY_TYPE``              e.g. ``>A|protein``
- ``>CHAIN_ID|ENTITY_TYPE|MSA_PATH``     e.g. ``>A|protein|/path/to.a3m``
- ``>sequence_name``                     simple name, defaults to ``protein``
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

VALID_PROTEIN_CHARS = set("ACDEFGHIKLMNPQRSTVWYXacdefghiklmnpqrstvwyx")
VALID_DNA_CHARS = set("ACGTNacgtn")
VALID_RNA_CHARS = set("ACGUNacgun")
VALID_ENTITY_TYPES = {"protein", "dna", "rna", "ligand"}


@dataclass
class ParsedSequence:
    """One parsed entry from a FASTA file."""
    chain_id: str
    entity_type: str  # protein | dna | rna | ligand
    sequence: str
    msa_path: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.sequence)

    @property
    def preview(self) -> str:
        return self.sequence[:50]


def _parse_header(header: str) -> Tuple[str, str, Optional[str]]:
    """Return (chain_id, entity_type, msa_path) from a FASTA header line.

    The leading ``>`` must already be stripped.
    """
    parts = header.strip().split("|")
    chain_id = parts[0].strip() if parts else "A"
    if not chain_id:
        chain_id = "A"

    entity_type = "protein"
    msa_path = None

    if len(parts) >= 2:
        etype = parts[1].strip().lower()
        if etype in VALID_ENTITY_TYPES:
            entity_type = etype

    if len(parts) >= 3:
        msa_path = parts[2].strip() or None

    return chain_id, entity_type, msa_path


def _validate_sequence(sequence: str, entity_type: str) -> List[str]:
    """Return a (possibly empty) list of validation warnings."""
    warnings: List[str] = []
    if not sequence:
        warnings.append("Empty sequence.")
        return warnings

    if entity_type == "protein":
        invalid = set(sequence) - VALID_PROTEIN_CHARS
        if invalid:
            warnings.append(
                f"Unusual amino-acid characters: {', '.join(sorted(invalid))}"
            )
    elif entity_type == "dna":
        invalid = set(sequence) - VALID_DNA_CHARS
        if invalid:
            warnings.append(
                f"Non-standard DNA characters: {', '.join(sorted(invalid))}"
            )
    elif entity_type == "rna":
        invalid = set(sequence) - VALID_RNA_CHARS
        if invalid:
            warnings.append(
                f"Non-standard RNA characters: {', '.join(sorted(invalid))}"
            )
    return warnings


def parse_fasta(text: str) -> Tuple[List[ParsedSequence], List[str]]:
    """Parse FASTA-formatted text and return (sequences, errors).

    Parameters
    ----------
    text:
        Raw FASTA content as a string.

    Returns
    -------
    sequences:
        List of :class:`ParsedSequence` objects.
    errors:
        List of error strings for problems that prevented parsing an entry.
    """
    sequences: List[ParsedSequence] = []
    errors: List[str] = []
    seen_ids: set = set()

    current_header: Optional[str] = None
    current_lines: List[str] = []

    def _flush():
        nonlocal current_header, current_lines
        if current_header is None:
            return
        seq = "".join(current_lines).replace(" ", "").replace("\t", "")
        chain_id, entity_type, msa_path = _parse_header(current_header)

        if chain_id in seen_ids:
            errors.append(
                f"Duplicate chain ID '{chain_id}' — skipping second occurrence."
            )
            current_header = None
            current_lines = []
            return

        seen_ids.add(chain_id)
        warnings = _validate_sequence(seq, entity_type)
        sequences.append(
            ParsedSequence(
                chain_id=chain_id,
                entity_type=entity_type,
                sequence=seq,
                msa_path=msa_path,
                warnings=warnings,
            )
        )
        current_header = None
        current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith(">"):
            _flush()
            current_header = line[1:]
        else:
            if current_header is None:
                errors.append(
                    f"Sequence data found before any header — ignoring: '{line[:30]}'"
                )
            else:
                current_lines.append(line)

    _flush()

    if not sequences and not errors:
        errors.append("No sequences found in the input.")

    return sequences, errors


def validate_chain_ids(sequences: List[ParsedSequence]) -> List[str]:
    """Return warnings for chain IDs that look unusual (e.g. too long)."""
    warnings: List[str] = []
    valid_pattern = re.compile(r"^[A-Za-z0-9_\-]{1,10}$")
    for seq in sequences:
        if not valid_pattern.match(seq.chain_id):
            warnings.append(
                f"Chain ID '{seq.chain_id}' may cause issues with downstream tools "
                "(expected 1-10 alphanumeric characters)."
            )
    return warnings
