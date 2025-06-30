"""Type definitions for the PDF MCP server."""

from typing import Literal

from typing_extensions import TypedDict

# PDF Object Types
PDFValue = str | int | float | bool | None


class PDFName(TypedDict):
    type: Literal["name"]
    value: str


class PDFString(TypedDict):
    type: Literal["string"]
    value: str
    encoding: Literal["text", "bytes"]


class PDFNumber(TypedDict):
    type: Literal["number"]
    value: int | float


class PDFBoolean(TypedDict):
    type: Literal["boolean"]
    value: bool


class PDFNull(TypedDict):
    type: Literal["null"]
    value: None


class PDFIndirectRef(TypedDict):
    type: Literal["indirect_ref"]
    objnum: int
    gennum: int | None


class PDFArray(TypedDict):
    type: Literal["array"]
    value: list["PDFObject"]


class PDFDict(TypedDict):
    type: Literal["dict"]
    value: dict[str, "PDFObject"]


class PDFStream(TypedDict):
    type: Literal["stream"]
    dictionary: PDFDict
    has_data: bool
    data_length: int | None


class PDFUnknown(TypedDict):
    type: Literal["unknown"]
    python_type: str
    value: str


# Union of all PDF object types
PDFObject = (
    PDFName
    | PDFString
    | PDFNumber
    | PDFBoolean
    | PDFNull
    | PDFIndirectRef
    | PDFArray
    | PDFDict
    | PDFStream
    | PDFUnknown
)


# Response types
class LazyParseResponse(TypedDict):
    result: PDFObject


class FullParseResponse(TypedDict):
    indirect_objects: dict[str, PDFObject]
    result: PDFObject


class ShallowResolveResponse(TypedDict):
    object_id: str
    content: PDFObject


class DeepResolveResponse(TypedDict):
    object_id: str
    content: PDFObject
    indirect_objects: dict[str, PDFObject]


# Enums
ResolutionDepth = Literal["shallow", "deep"]
