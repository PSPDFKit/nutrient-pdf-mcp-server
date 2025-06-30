"""PDF object tree parser with lazy loading support."""

import logging
from pathlib import Path
from typing import Any

import pypdf
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    ByteStringObject,
    DictionaryObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    NumberObject,
    StreamObject,
    TextStringObject,
)

from .exceptions import InvalidObjectIDError, InvalidPathError, ObjectNotFoundError, PDFParsingError
from .types import (
    DeepResolveResponse,
    FullParseResponse,
    LazyParseResponse,
    PDFObject,
    ResolutionDepth,
    ShallowResolveResponse,
)

logger = logging.getLogger(__name__)


class PDFObjectTreeParser:
    """Parser for PDF object trees with support for lazy loading and path navigation.

    This parser can operate in two modes:
    1. Lazy mode: Returns only indirect references without resolving them
    2. Full mode: Resolves all indirect references and returns complete object tree

    It also supports path navigation (e.g., "Pages.Kids.0") and selective object resolution.
    """

    def __init__(self) -> None:
        self.indirect_objects: dict[str, PDFObject] = {}
        self.visited_refs: set[str] = set()
        self.lazy_mode: bool = False

    def parse_pdf_lazy(
        self,
        pdf_path: str | Path,
        target_object_id: str | None = None,
        path: str | None = None,
    ) -> LazyParseResponse:
        """Parse PDF with lazy loading - only returns indirect references without resolving them.

        Args:
            pdf_path: Path to the PDF file
            target_object_id: Optional specific object ID to retrieve (e.g., '1 0')
            path: Optional object path to navigate (e.g., 'Pages.Kids.0')

        Returns:
            LazyParseResponse containing only the result object with unresolved references

        Raises:
            PDFParsingError: If PDF cannot be parsed
            InvalidObjectIDError: If target_object_id has invalid format
            InvalidPathError: If path navigation fails
        """
        self._reset_state(lazy_mode=True)
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise PDFParsingError(f"PDF file not found: {pdf_path}")

        try:
            with open(pdf_path, "rb") as file:
                reader = pypdf.PdfReader(file)

                if target_object_id:
                    result = self._parse_specific_object(reader, target_object_id)
                else:
                    # Parse root catalog
                    catalog = reader.trailer["/Root"]
                    result = self._serialize_object(catalog)

                    # Apply path navigation if provided
                    if path:
                        result = self._navigate_path(result, path, reader)

                return LazyParseResponse(result=result)

        except Exception as e:
            logger.error(f"Failed to parse PDF {pdf_path}: {e}")
            raise PDFParsingError(f"Error parsing PDF: {e}") from e

    def parse_pdf_full(
        self,
        pdf_path: str | Path,
        target_object_id: str | None = None,
        path: str | None = None,
    ) -> FullParseResponse:
        """Parse PDF with full resolution - resolves all indirect references.

        Args:
            pdf_path: Path to the PDF file
            target_object_id: Optional specific object ID to retrieve (e.g., '1 0')
            path: Optional object path to navigate (e.g., 'Pages.Kids.0')

        Returns:
            FullParseResponse containing resolved objects and result

        Raises:
            PDFParsingError: If PDF cannot be parsed
            InvalidObjectIDError: If target_object_id has invalid format
            InvalidPathError: If path navigation fails
        """
        self._reset_state(lazy_mode=False)
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise PDFParsingError(f"PDF file not found: {pdf_path}")

        try:
            with open(pdf_path, "rb") as file:
                reader = pypdf.PdfReader(file)

                if target_object_id:
                    result = self._parse_specific_object(reader, target_object_id)
                else:
                    # Parse root catalog
                    catalog = reader.trailer["/Root"]
                    result = self._serialize_object(catalog)

                    # Apply path navigation if provided
                    if path:
                        result = self._navigate_path(result, path, reader)

                return FullParseResponse(indirect_objects=self.indirect_objects, result=result)

        except Exception as e:
            logger.error(f"Failed to parse PDF {pdf_path}: {e}")
            raise PDFParsingError(f"Error parsing PDF: {e}") from e

    def resolve_object(
        self, pdf_path: str | Path, object_id: str, depth: ResolutionDepth = "shallow"
    ) -> ShallowResolveResponse | DeepResolveResponse:
        """Resolve a specific indirect object by its ID.

        Args:
            pdf_path: Path to PDF file
            object_id: Object ID in format "1-0"
            depth: Resolution depth - "shallow" (only direct properties) or "deep" (resolve all nested)

        Returns:
            Response containing the resolved object content

        Raises:
            PDFParsingError: If PDF cannot be parsed
            InvalidObjectIDError: If object_id has invalid format
            ObjectNotFoundError: If object is not found in PDF
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise PDFParsingError(f"PDF file not found: {pdf_path}")

        try:
            with open(pdf_path, "rb") as file:
                reader = pypdf.PdfReader(file)

                # Parse object ID (format: "1-0")
                try:
                    parts = object_id.split("-")
                    if len(parts) != 2:
                        raise InvalidObjectIDError(
                            f"Invalid object ID format: {object_id}. Expected format: '1-0'"
                        )

                    obj_num, gen_num = int(parts[0]), int(parts[1])
                except ValueError as e:
                    raise InvalidObjectIDError(
                        f"Invalid object ID format: {object_id}. Expected format: '1-0'"
                    ) from e

                # Create IndirectObject reference and resolve it
                try:
                    indirect_ref = IndirectObject(obj_num, gen_num, reader)
                    actual_obj = indirect_ref.get_object()
                except Exception as e:
                    raise ObjectNotFoundError(
                        f"Object {object_id} not found in PDF", details=str(e)
                    ) from e

                # Serialize the resolved object
                self._reset_state(lazy_mode=(depth == "shallow"))
                result = self._serialize_object(actual_obj)

                if depth == "shallow":
                    return ShallowResolveResponse(object_id=object_id, content=result)
                else:
                    return DeepResolveResponse(
                        object_id=object_id, content=result, indirect_objects=self.indirect_objects
                    )

        except (PDFParsingError, InvalidObjectIDError, ObjectNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to resolve object {object_id} in {pdf_path}: {e}")
            raise PDFParsingError(f"Error resolving object {object_id}: {e}") from e

    def _reset_state(self, lazy_mode: bool) -> None:
        """Reset parser state for a new operation."""
        self.indirect_objects = {}
        self.visited_refs = set()
        self.lazy_mode = lazy_mode

    def _parse_specific_object(self, reader: pypdf.PdfReader, target_object_id: str) -> PDFObject:
        """Parse a specific object by ID."""
        try:
            parts = target_object_id.split()
            if len(parts) < 2:
                raise InvalidObjectIDError(
                    f"Invalid object ID format: {target_object_id}. Expected format: '1 0'"
                )

            obj_num, gen_num = int(parts[0]), int(parts[1])
            indirect_ref = IndirectObject(obj_num, gen_num, reader)
            return self._serialize_object(indirect_ref)

        except ValueError as e:
            raise InvalidObjectIDError(
                f"Invalid object ID format: {target_object_id}. Expected format: '1 0'"
            ) from e
        except Exception as e:
            raise ObjectNotFoundError(
                f"Object {target_object_id} not found in PDF", details=str(e)
            ) from e

    def _serialize_object(self, obj: Any) -> PDFObject:
        """Convert PDF object to JSON-serializable format.

        Args:
            obj: PyPDF object to serialize

        Returns:
            Serialized PDF object
        """
        if isinstance(obj, IndirectObject):
            ref_id = f"{obj.idnum}-{obj.generation}"

            if self.lazy_mode:
                # In lazy mode, just return the reference without resolving
                return {"type": "indirect_ref", "id": ref_id}

            if ref_id in self.visited_refs:
                return {"type": "indirect_ref", "id": ref_id}

            self.visited_refs.add(ref_id)

            # Get the actual object
            actual_obj = obj.get_object()
            serialized = self._serialize_object(actual_obj)

            # Store in indirect_objects
            self.indirect_objects[ref_id] = serialized

            return {"type": "indirect_ref", "id": ref_id}

        elif isinstance(obj, DictionaryObject):
            result = {"type": "dict", "value": {}}
            for key, value in obj.items():
                key_str = str(key) if isinstance(key, NameObject) else key
                result["value"][key_str] = self._serialize_object(value)
            return result

        elif isinstance(obj, ArrayObject):
            return {"type": "array", "value": [self._serialize_object(item) for item in obj]}

        elif isinstance(obj, StreamObject):
            # For streams, include dictionary and indicate data presence
            return {
                "type": "stream",
                "dictionary": self._serialize_object(dict(obj)),
                "has_data": True,
                "data_length": len(obj.get_data()) if hasattr(obj, "get_data") else None,
            }

        elif isinstance(obj, NameObject):
            return {"type": "name", "value": str(obj)}

        elif isinstance(obj, (TextStringObject, ByteStringObject)):
            try:
                return {
                    "type": "string",
                    "value": str(obj),
                    "encoding": "text" if isinstance(obj, TextStringObject) else "bytes",
                }
            except Exception:
                return {"type": "string", "value": repr(obj), "encoding": "bytes"}

        elif isinstance(obj, (NumberObject, FloatObject)):
            return {
                "type": "number",
                "value": float(obj) if isinstance(obj, FloatObject) else int(obj),
            }

        elif isinstance(obj, BooleanObject):
            return {"type": "boolean", "value": bool(obj)}

        elif isinstance(obj, NullObject):
            return {"type": "null", "value": None}

        else:
            # Fallback for unknown types
            return {"type": "unknown", "python_type": type(obj).__name__, "value": str(obj)}

    def _navigate_path(self, obj: PDFObject, path: str, reader: pypdf.PdfReader) -> PDFObject:
        """Navigate through object path like 'Pages.Kids.0'.

        Args:
            obj: Starting object
            path: Dot-separated path to navigate
            reader: PDF reader for resolving references

        Returns:
            Object at the specified path

        Raises:
            InvalidPathError: If path navigation fails
        """
        parts = path.split(".")
        current = obj

        for i, part in enumerate(parts):
            try:
                current = self._navigate_single_step(current, part, reader)
            except Exception as e:
                current_path = ".".join(parts[: i + 1])
                raise InvalidPathError(
                    f"Failed to navigate path '{path}' at step '{part}'",
                    details=f"Error at '{current_path}': {e}",
                ) from e

        return current

    def _navigate_single_step(
        self, obj: PDFObject, step: str, reader: pypdf.PdfReader
    ) -> PDFObject:
        """Navigate a single step in the path.

        Args:
            obj: Current object
            step: Navigation step (key name or array index)
            reader: PDF reader for resolving references

        Returns:
            Object after navigation step

        Raises:
            InvalidPathError: If navigation step fails
        """
        # If this is an indirect reference, resolve it first
        if isinstance(obj, dict) and obj.get("type") == "indirect_ref":
            ref_id = obj["id"]
            if ref_id in self.indirect_objects:
                obj = self.indirect_objects[ref_id]
            else:
                # Need to resolve the reference
                parts = ref_id.split("-")
                if len(parts) == 2:
                    obj_num, gen_num = int(parts[0]), int(parts[1])
                    indirect_ref = IndirectObject(obj_num, gen_num, reader)
                    actual_obj = indirect_ref.get_object()
                    obj = self._serialize_object(actual_obj)
                else:
                    raise InvalidPathError(f"Invalid indirect reference format: {ref_id}")

        # Handle dictionary navigation
        if isinstance(obj, dict) and obj.get("type") == "dict":
            dict_value = obj.get("value", {})

            # Try with leading slash (PDF name convention)
            key_with_slash = f"/{step}"
            if key_with_slash in dict_value:
                return dict_value[key_with_slash]

            # Try without slash
            if step in dict_value:
                return dict_value[step]

            available_keys = list(dict_value.keys())
            raise InvalidPathError(
                f"Key '{step}' not found in dictionary", details=f"Available keys: {available_keys}"
            )

        # Handle array navigation
        elif isinstance(obj, dict) and obj.get("type") == "array":
            array_value = obj.get("value", [])
            try:
                index = int(step)
                if 0 <= index < len(array_value):
                    return array_value[index]
                else:
                    raise InvalidPathError(
                        f"Array index {index} out of range",
                        details=f"Array length: {len(array_value)}",
                    )
            except ValueError as e:
                raise InvalidPathError(f"Invalid array index: '{step}'") from e

        else:
            obj_type = obj.get("type", "unknown") if isinstance(obj, dict) else type(obj).__name__
            raise InvalidPathError(f"Cannot navigate into object of type: {obj_type}")
