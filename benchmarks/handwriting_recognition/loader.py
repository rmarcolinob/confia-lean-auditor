import json
from pathlib import Path

from confia_lean_auditor.capture.schemas import CaptureDocument
from confia_lean_auditor.submissions.png import validate_png
from confia_lean_auditor.submissions.store import sha256
from benchmarks.handwriting_recognition.schema import RecognitionSample


def artifact_path(root: Path, relative: str) -> Path:
    supplied = Path(relative)
    if supplied.is_absolute() or ".." in supplied.parts:
        raise ValueError("sample artifact must be inside the dataset")
    path = root / supplied
    if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root.parent):
        raise ValueError("sample artifact symlink is not allowed")
    resolved = path.resolve()
    if root.resolve() not in resolved.parents:
        raise ValueError("artifact escaped dataset")
    return resolved


def load_samples(manifest: Path) -> list[RecognitionSample]:
    manifest = Path(manifest)
    samples = [RecognitionSample.model_validate(value) for value in json.loads(manifest.read_text(encoding="utf-8"))]
    if len({s.sample_id for s in samples}) != len(samples):
        raise ValueError("duplicate sample ID")
    for sample in samples:
        blobs = {}
        for artifact in (sample.png, sample.input_strokes):
            if artifact is None:
                continue
            data = artifact_path(manifest.parent, artifact.path).read_bytes()
            if sha256(data) != artifact.sha256:
                raise ValueError("sample artifact hash mismatch")
            blobs[artifact.path] = data
        image = blobs[sample.png.path]
        # validate_png also checks signature, dimensions, CRC, complete data and limits.
        if len(image) < 24:
            raise ValueError("invalid sample PNG")
        width, height = int.from_bytes(image[16:20], "big"), int.from_bytes(image[20:24], "big")
        validate_png(image, width, height)
        if sample.input_strokes is not None:
            snapshot = CaptureDocument.model_validate_json(blobs[sample.input_strokes.path])
            if any(s.page_index not in {p.index for p in snapshot.pages} for s in sample.gold_segments):
                raise ValueError("gold segment outside capture pages")
    return samples
