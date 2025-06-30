"""Tests for type definitions and serialization."""

import pytest

from pdf_mcp.types import (
    DeepResolveResponse,
    FullParseResponse,
    LazyParseResponse,
    PDFArray,
    PDFBoolean,
    PDFDict,
    PDFIndirectRef,
    PDFName,
    PDFNull,
    PDFNumber,
    PDFStream,
    PDFString,
    PDFUnknown,
    ResolutionDepth,
    ShallowResolveResponse,
)


class TestPDFTypes:
    """Test PDF type definitions."""

    def test_pdf_name_type(self):
        """Test PDFName type structure."""
        name: PDFName = {"type": "name", "value": "/Pages"}
        assert name["type"] == "name"
        assert name["value"] == "/Pages"

    def test_pdf_string_type(self):
        """Test PDFString type structure."""
        string: PDFString = {"type": "string", "value": "test", "encoding": "text"}
        assert string["type"] == "string"
        assert string["value"] == "test"
        assert string["encoding"] == "text"

    def test_pdf_number_type(self):
        """Test PDFNumber type structure."""
        number: PDFNumber = {"type": "number", "value": 42}
        assert number["type"] == "number"
        assert number["value"] == 42

        float_number: PDFNumber = {"type": "number", "value": 3.14}
        assert float_number["value"] == 3.14

    def test_pdf_boolean_type(self):
        """Test PDFBoolean type structure."""
        boolean: PDFBoolean = {"type": "boolean", "value": True}
        assert boolean["type"] == "boolean"
        assert boolean["value"] is True

    def test_pdf_null_type(self):
        """Test PDFNull type structure."""
        null: PDFNull = {"type": "null", "value": None}
        assert null["type"] == "null"
        assert null["value"] is None

    def test_pdf_indirect_ref_type(self):
        """Test PDFIndirectRef type structure."""
        ref: PDFIndirectRef = {"type": "indirect_ref", "id": "1-0"}
        assert ref["type"] == "indirect_ref"
        assert ref["id"] == "1-0"

    def test_pdf_array_type(self):
        """Test PDFArray type structure."""
        name_obj: PDFName = {"type": "name", "value": "/Test"}
        array: PDFArray = {"type": "array", "value": [name_obj]}
        assert array["type"] == "array"
        assert len(array["value"]) == 1
        assert array["value"][0]["type"] == "name"

    def test_pdf_dict_type(self):
        """Test PDFDict type structure."""
        name_obj: PDFName = {"type": "name", "value": "/Pages"}
        dict_obj: PDFDict = {"type": "dict", "value": {"/Type": name_obj}}
        assert dict_obj["type"] == "dict"
        assert "/Type" in dict_obj["value"]
        assert dict_obj["value"]["/Type"]["value"] == "/Pages"

    def test_pdf_stream_type(self):
        """Test PDFStream type structure."""
        dict_obj: PDFDict = {"type": "dict", "value": {}}
        stream: PDFStream = {
            "type": "stream",
            "dictionary": dict_obj,
            "has_data": True,
            "data_length": 1024,
        }
        assert stream["type"] == "stream"
        assert stream["has_data"] is True
        assert stream["data_length"] == 1024

    def test_pdf_unknown_type(self):
        """Test PDFUnknown type structure."""
        unknown: PDFUnknown = {
            "type": "unknown",
            "python_type": "SomeClass",
            "value": "string representation",
        }
        assert unknown["type"] == "unknown"
        assert unknown["python_type"] == "SomeClass"
        assert unknown["value"] == "string representation"


class TestResponseTypes:
    """Test response type definitions."""

    def test_lazy_parse_response(self):
        """Test LazyParseResponse type structure."""
        name_obj: PDFName = {"type": "name", "value": "/Catalog"}
        response: LazyParseResponse = {"result": name_obj}
        assert "result" in response
        assert response["result"]["type"] == "name"

    def test_full_parse_response(self):
        """Test FullParseResponse type structure."""
        name_obj: PDFName = {"type": "name", "value": "/Catalog"}
        response: FullParseResponse = {"indirect_objects": {}, "result": name_obj}
        assert "result" in response
        assert "indirect_objects" in response
        assert isinstance(response["indirect_objects"], dict)

    def test_shallow_resolve_response(self):
        """Test ShallowResolveResponse type structure."""
        name_obj: PDFName = {"type": "name", "value": "/Pages"}
        response: ShallowResolveResponse = {"object_id": "1-0", "content": name_obj}
        assert response["object_id"] == "1-0"
        assert "content" in response
        assert response["content"]["type"] == "name"

    def test_deep_resolve_response(self):
        """Test DeepResolveResponse type structure."""
        name_obj: PDFName = {"type": "name", "value": "/Pages"}
        response: DeepResolveResponse = {
            "object_id": "1-0",
            "content": name_obj,
            "indirect_objects": {},
        }
        assert response["object_id"] == "1-0"
        assert "content" in response
        assert "indirect_objects" in response

    def test_resolution_depth_literal(self):
        """Test ResolutionDepth literal type."""
        shallow: ResolutionDepth = "shallow"
        deep: ResolutionDepth = "deep"
        assert shallow == "shallow"
        assert deep == "deep"


class TestComplexStructures:
    """Test complex nested structures."""

    def test_nested_pdf_structure(self):
        """Test a complex nested PDF structure."""
        # Create a complex structure similar to what parser produces
        ref: PDFIndirectRef = {"type": "indirect_ref", "id": "3-0"}
        array: PDFArray = {"type": "array", "value": [ref]}

        dict_obj: PDFDict = {
            "type": "dict",
            "value": {
                "/Type": {"type": "name", "value": "/Pages"},
                "/Count": {"type": "number", "value": 2},
                "/Kids": array,
            },
        }

        # Verify structure
        assert dict_obj["type"] == "dict"
        assert dict_obj["value"]["/Type"]["value"] == "/Pages"
        assert dict_obj["value"]["/Count"]["value"] == 2
        assert dict_obj["value"]["/Kids"]["type"] == "array"
        assert dict_obj["value"]["/Kids"]["value"][0]["type"] == "indirect_ref"
        assert dict_obj["value"]["/Kids"]["value"][0]["id"] == "3-0"

    def test_response_with_complex_objects(self):
        """Test response containing complex PDF objects."""
        # Create complex objects
        page_ref: PDFIndirectRef = {"type": "indirect_ref", "id": "2-0"}
        kids_array: PDFArray = {"type": "array", "value": [page_ref]}

        pages_dict: PDFDict = {
            "type": "dict",
            "value": {
                "/Type": {"type": "name", "value": "/Pages"},
                "/Kids": kids_array,
                "/Count": {"type": "number", "value": 1},
            },
        }

        # Create full response
        response: FullParseResponse = {
            "indirect_objects": {"3-0": pages_dict},
            "result": {"type": "indirect_ref", "id": "3-0"},
        }

        # Verify the response structure
        assert "result" in response
        assert "indirect_objects" in response
        assert response["result"]["id"] == "3-0"
        assert "3-0" in response["indirect_objects"]
        assert response["indirect_objects"]["3-0"]["type"] == "dict"


if __name__ == "__main__":
    pytest.main([__file__])
