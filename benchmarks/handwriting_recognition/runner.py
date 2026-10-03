"""Offline fixture replay or an explicitly registered local adapter; never audit/Lean."""
import argparse
import json
from pathlib import Path

from benchmarks.handwriting_recognition.loader import artifact_path, load_samples
from benchmarks.handwriting_recognition.metrics import compare_segments
from confia_lean_auditor.recognition.registry import RecognitionArtifact, RecognitionInput, configured_registry
from confia_lean_auditor.recognition.schemas import ProviderOutput


def run(manifest: Path, provider=None, registry=None):
    samples = load_samples(manifest)
    adapter = (registry or configured_registry()).create(provider) if provider else None
    reports = []
    for sample in samples:
        if adapter is None:
            if sample.recognized_segments is None:
                raise ValueError("fixture replay requires recognized_segments")
            predicted = sample.recognized_segments
        else:
            refs = []
            if adapter.input_mode in {"strokes", "strokes_and_image"}:
                if sample.input_strokes is None:
                    raise ValueError("adapter requires input strokes")
                refs.append((sample.input_strokes, None))
            if adapter.input_mode in {"image", "strokes_and_image"}:
                refs.append((sample.png, 0))
            artifacts = tuple(RecognitionArtifact(Path(r.path).name, page, r.sha256,
                              artifact_path(manifest.parent, r.path).read_bytes()) for r, page in refs)
            supplied = adapter.recognize(RecognitionInput(f"benchmark:{sample.sample_id}", artifacts))
            predicted = ProviderOutput.model_validate(supplied.model_dump()).segments
        reports.append({"sample_id": sample.sample_id, "metrics": compare_segments(sample.gold_segments, predicted)})
    return {"mode": "adapter" if adapter else "fixture_replay", "provider": provider,
            "samples": reports, "sample_count": len(reports)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--provider", help="Explicit registered local provider; omit for fixture replay")
    args = parser.parse_args()
    print(json.dumps(run(args.manifest, args.provider), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
