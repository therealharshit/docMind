# TODOs

## Add selective OCR for scanned documents

What: Add selective Tesseract OCR by text-density threshold for scanned PDFs and image-heavy slides.

Why: OCR was explicitly deferred from the first slice, so scanned documents will not meet the original requirement.

Pros: Completes the original OCR requirement and improves real-world document coverage.

Cons: Adds CPU cost, threshold tuning, and more benchmark cases.

Context: First slice should record `ocr_skipped` diagnostics for image-only content. Start in `app/extraction/ocr.py`, add native/scanned/mixed fixtures, and benchmark the 50-page path after OCR is enabled.

Depends on / blocked by: Core parser/result schema must exist first.

## Add legacy `.ppt` conversion

What: Add `.ppt` support by converting legacy PowerPoint files to `.pptx` with LibreOffice headless before parsing.

Why: First slice accepts PPTX but rejects `.ppt` with a clear 415 response, so the original PPT requirement is not complete.

Pros: Completes the stated file-format matrix.

Cons: Adds a large Docker dependency, conversion failure cases, and more integration tests.

Context: First implementation should centralize upload type validation so `.ppt` rejection can later be replaced by a conversion stage. Start by adding a `conversion/` module, Docker LibreOffice package, and fixtures for valid/corrupt `.ppt`.

Depends on / blocked by: PPTX parser and durable job error model.
