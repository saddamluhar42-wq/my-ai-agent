from pathlib import Path

from config import (
    MAX_FILE_CONTEXT_CHARS,
    MAX_FILE_SIZE_MB,
)


class FileProcessingError(Exception):
    """Raised when an uploaded file cannot be processed."""


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".py",
    ".html",
    ".xml",
    ".yaml",
    ".yml",
    ".css",
    ".js",
    ".ts",
    ".sql",
}


def validate_file_size(
    uploaded_file,
):
    max_bytes = (
        MAX_FILE_SIZE_MB
        * 1024
        * 1024
    )

    file_size = getattr(
        uploaded_file,
        "size",
        None,
    )

    if file_size is not None:
        if file_size > max_bytes:
            raise FileProcessingError(
                f"File exceeds the "
                f"{MAX_FILE_SIZE_MB} MB limit."
            )


def get_extension(
    filename,
):
    return Path(
        filename
    ).suffix.lower()


def read_text_file(
    uploaded_file,
):
    data = uploaded_file.getvalue()

    return data.decode(
        "utf-8",
        errors="ignore",
    )


def read_pdf_file(
    uploaded_file,
):
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise FileProcessingError(
            "PDF support requires the "
            "'pypdf' package."
        ) from error

    try:
        reader = PdfReader(
            uploaded_file
        )

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n\n".join(pages)

    except Exception as error:
        raise FileProcessingError(
            f"Unable to read PDF: {error}"
        ) from error


def read_docx_file(
    uploaded_file,
):
    try:
        from docx import Document
    except ImportError as error:
        raise FileProcessingError(
            "DOCX support requires the "
            "'python-docx' package."
        ) from error

    try:
        document = Document(
            uploaded_file
        )

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        return "\n".join(paragraphs)

    except Exception as error:
        raise FileProcessingError(
            f"Unable to read DOCX: {error}"
        ) from error


def extract_file_content(
    uploaded_file,
):
    validate_file_size(
        uploaded_file
    )

    filename = getattr(
        uploaded_file,
        "name",
        "uploaded_file",
    )

    extension = get_extension(
        filename
    )

    if extension in TEXT_EXTENSIONS:
        return read_text_file(
            uploaded_file
        )

    if extension == ".pdf":
        return read_pdf_file(
            uploaded_file
        )

    if extension == ".docx":
        return read_docx_file(
            uploaded_file
        )

    raise FileProcessingError(
        f"Unsupported file type: "
        f"{extension or 'unknown'}"
    )


def limit_context(
    text,
    max_chars=MAX_FILE_CONTEXT_CHARS,
):
    if not text:
        return ""

    text = str(text)

    if len(text) <= max_chars:
        return text

    return (
        text[:max_chars]
        + "\n\n"
        "[File content truncated because "
        "it exceeded the context limit.]"
    )


def process_uploaded_file(
    uploaded_file,
):
    filename = getattr(
        uploaded_file,
        "name",
        "uploaded_file",
    )

    content = extract_file_content(
        uploaded_file
    )

    content = limit_context(
        content
    )

    return {
        "name": filename,
        "extension": get_extension(
            filename
        ),
        "content": content,
        "size": getattr(
            uploaded_file,
            "size",
            None,
        ),
    }


def process_multiple_files(
    uploaded_files,
):
    results = []
    errors = []

    for uploaded_file in (
        uploaded_files or []
    ):
        try:
            results.append(
                process_uploaded_file(
                    uploaded_file
                )
            )

        except Exception as error:
            errors.append(
                {
                    "name": getattr(
                        uploaded_file,
                        "name",
                        "unknown",
                    ),
                    "error": str(error),
                }
            )

    return results, errors


def build_file_context(
    processed_files,
):
    if not processed_files:
        return ""

    sections = []

    for file_data in processed_files:
        name = file_data.get(
            "name",
            "unknown",
        )

        content = file_data.get(
            "content",
            "",
        )

        sections.append(
            f"FILE: {name}\n"
            f"{content}"
        )

    return "\n\n---\n\n".join(
        sections
    )
