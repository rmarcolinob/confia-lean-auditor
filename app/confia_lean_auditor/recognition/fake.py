from confia_lean_auditor.recognition.registry import RecognitionInput
from confia_lean_auditor.recognition.schemas import ProviderOutput, RecognitionSegment


class FakeTestRecognizer:
    """Constant artificial output, independent of handwriting. This is NOT OCR."""
    provider = "fake_test"
    display_label = "Reconhecedor de teste"
    adapter = "confia_fake_test"
    adapter_version = "1.0.0"
    input_mode = "strokes_and_image"
    public_parameters = {"fixture": "constant_2_plus_2_equals_5", "real_ocr": False}

    def recognize(self, source: RecognitionInput) -> ProviderOutput:
        pages = sorted({a.page_index for a in source.artifacts if a.page_index is not None})
        return ProviderOutput(
            segments=[RecognitionSegment(page_index=p, order=0, kind="math", latex="2 + 2 = 5") for p in pages],
            warnings=["Reconhecedor de teste: saída artificial constante; não é OCR real."],
        )
