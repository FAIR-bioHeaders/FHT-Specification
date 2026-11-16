# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Test-only FHT draft HTML reference implementation; not a toolkit capability.

DOM and typed-container code derives from FHP-Specification tests/fhp_microdata.py
at bc7110fedb6f05b52b1d2348b5b14a79b91b0637. See docs/FHT-MICRODATA.md.
No network access, released aliases, checksum verification or browser integration.
"""

import json
import math
import warnings
from html import escape
from html.parser import HTMLParser
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
FHT_ITEMTYPE = (
    "https://raw.githubusercontent.com/FAIR-bioHeaders/FHT-Specification/main/fht.json"
)
OTHER_FAMILY_TYPES = {
    "https://raw.githubusercontent.com/FAIR-bioHeaders/"
    + repo
    + "/main/"
    + kind
    + ".json"
    for repo in ["FAIR-bioHeaders-Specification", "FHR-Specification"]
    for kind in ["fhr", "fhp", "fhgff3"]
}

# Elements whose end tag HTML implies (shared MICRODATA.md M2). The values are
# the ancestors a start tag closes, and the scope its search must not cross.
_VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
_BASE_SCOPE = {
    "applet",
    "caption",
    "html",
    "marquee",
    "object",
    "table",
    "td",
    "th",
    "template",
}
_BUTTON_SCOPE = _BASE_SCOPE | {"button"}
_LIST_SCOPE = _BASE_SCOPE | {"ol", "ul"}
_TABLE_SCOPE = {"html", "table", "template"}

# Start tags that close an open p in button scope.
_P_CLOSERS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "details",
    "dialog",
    "div",
    "dl",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hgroup",
    "hr",
    "main",
    "menu",
    "nav",
    "ol",
    "p",
    "pre",
    "search",
    "section",
    "table",
    "ul",
    "li",
    "dt",
    "dd",
    "tr",
    "td",
    "th",
    "tbody",
    "thead",
    "tfoot",
}
_IMPLIED_BY_START = {
    "li": ({"li"}, _LIST_SCOPE),
    "dt": ({"dt", "dd"}, _BASE_SCOPE),
    "dd": ({"dt", "dd"}, _BASE_SCOPE),
    "option": ({"option"}, _BASE_SCOPE | {"select", "datalist"}),
    "optgroup": ({"option", "optgroup"}, _BASE_SCOPE | {"select"}),
    "tr": ({"tr"}, _TABLE_SCOPE),
    "td": ({"td", "th"}, _TABLE_SCOPE),
    "th": ({"td", "th"}, _TABLE_SCOPE),
    "tbody": ({"tbody", "thead", "tfoot"}, _TABLE_SCOPE),
    "thead": ({"tbody", "thead", "tfoot"}, _TABLE_SCOPE),
    "tfoot": ({"tbody", "thead", "tfoot"}, _TABLE_SCOPE),
    "colgroup": ({"colgroup"}, _TABLE_SCOPE),
}
# Elements whose defining attribute is the property value (shared MICRODATA.md M2).
_VALUE_ATTRIBUTE = {
    "meta": "content",
    "a": "href",
    "area": "href",
    "link": "href",
    "audio": "src",
    "embed": "src",
    "iframe": "src",
    "img": "src",
    "source": "src",
    "track": "src",
    "video": "src",
    "object": "data",
    "data": "value",
    "meter": "value",
    "time": "datetime",
}
_TYPED = {"string", "integer", "number", "boolean", "null"}

# Subtrees whose contents are inert in HTML: they create no item scopes or
# properties and contribute no scalar text (docs/FHT-MICRODATA.md F7).
_INERT_CONTENT = {"script", "template"}


class MicrodataError(ValueError):
    """The document is not valid FHT microdata."""


class _Node:
    __slots__ = (
        "tag",
        "attrs",
        "children",
        "itemscope",
        "itemtype",
        "itemprop",
        "datatype",
    )

    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = attrs
        self.children = []
        self.itemscope = "itemscope" in attrs
        self.itemtype = attrs.get("itemtype", "").split()
        self.itemprop = attrs.get("itemprop", "").split()
        self.datatype = attrs.get("data-fhr-type")


def _first_wins(attrs):
    """R9: the first of repeated attributes applies."""
    result = {}
    for name, value in attrs:
        if name not in result:
            result[name] = "" if value is None else value
    return result


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("#document", {})
        self.stack = [self.root]

    def _pop_through(self, targets, boundaries):
        """Close the nearest target ancestor and everything above it.

        The search skips inline descendants but stops at the scope boundary
        the HTML rule names, so an open span does not hide the p or table cell
        that the start tag has to close (shared MICRODATA.md M2).
        """
        for index in range(len(self.stack) - 1, 0, -1):
            node = self.stack[index]
            if node.tag in targets:
                del self.stack[index:]
                return True
            if node.tag in boundaries:
                return False
        return False

    def _close_implied(self, tag):
        if tag in _P_CLOSERS:
            self._pop_through({"p"}, _BUTTON_SCOPE)
        rule = _IMPLIED_BY_START.get(tag)
        if rule:
            self._pop_through(*rule)

    def handle_starttag(self, tag, attrs):
        self._close_implied(tag)
        node = _Node(tag, _first_wins(attrs))
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        # HTML ignores a self-closing slash on non-void elements.
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _nodes(node):
    for child in node.children:
        if isinstance(child, _Node):
            if child.tag in _INERT_CONTENT:
                continue
            yield child
            yield from _nodes(child)


def _text(node):
    parts = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        elif child.tag not in _INERT_CONTENT:
            parts.append(_text(child))
    return "".join(parts)


def _value_of(element):
    attribute = _VALUE_ATTRIBUTE.get(element.tag)
    if attribute and attribute in element.attrs:
        return element.attrs[attribute]
    return _text(element)


def _resolve(root, subschema):
    while isinstance(subschema, dict) and "$ref" in subschema:
        reference = subschema["$ref"]
        if not reference.startswith("#/$defs/"):
            raise MicrodataError(f"unsupported $ref {reference!r}")
        subschema = root["$defs"][reference.rsplit("/", 1)[-1]]
    return subschema


def _json_type(root, subschema):
    resolved = _resolve(root, subschema)
    if "type" in resolved:
        return resolved["type"]
    branches = resolved.get("anyOf") or resolved.get("oneOf")
    if branches:
        types = {_json_type(root, branch) for branch in branches}
        if len(types) == 1:
            return types.pop()
    return None


def _subschema(root, parent, name):
    return _resolve(root, parent).get("properties", {}).get(name, {})


def _parse_typed(raw, datatype):
    if datatype == "string":
        return raw
    try:
        value = json.loads(raw)
    except ValueError as error:
        raise MicrodataError(f"{datatype} value is not JSON: {raw!r}") from error
    if datatype == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise MicrodataError(f"integer value is not an integer: {raw!r}")
    elif datatype == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MicrodataError(f"number value is not a number: {raw!r}")
    elif datatype == "boolean":
        if not isinstance(value, bool):
            raise MicrodataError(f"boolean value is not a boolean: {raw!r}")
    elif datatype == "null":
        if value is not None:
            raise MicrodataError(f"null value is not null: {raw!r}")
    else:
        raise MicrodataError(f"unknown data-fhr-type {datatype!r}")
    return value


def _convert_untyped(raw, root, subschema):
    kind = _json_type(root, subschema)
    if kind in ("integer", "number", "boolean"):
        return _parse_typed(raw, kind)
    return raw


def _property_elements(scope):
    """Yield (element, property name) for the item's own properties (M1)."""

    def walk(node):
        for child in node.children:
            if not isinstance(child, _Node):
                continue
            if child.tag in _INERT_CONTENT:
                continue  # Script and template contents never contribute metadata.
            if child.datatype in ("array", "object"):
                # A typed container's children are the container's own values,
                # not properties of the enclosing item.
                if child.itemprop:
                    for name in child.itemprop:
                        yield child, name
                continue
            if child.itemprop:
                for name in child.itemprop:
                    yield child, name
                if child.itemscope:
                    continue  # A nested item; its properties are not the parent's.
                # An ordinary property element can contain further properties;
                # they still belong to the enclosing item (M1).
                yield from walk(child)
            elif child.itemscope:
                continue  # A separate item; its properties are not the parent's.
            else:
                yield from walk(child)

    yield from walk(scope)


def _item_subschema(root, subschema):
    """The schema for one occurrence of a field, using an array's items."""
    resolved = _resolve(root, subschema)
    if _json_type(root, subschema) == "array":
        return resolved.get("items", {})
    return subschema


def _read_value(element, root, subschema):
    datatype = element.datatype
    if datatype == "array":
        items = []
        for child in element.children:
            if isinstance(child, str):
                if child.strip():
                    raise MicrodataError("array container has stray text")
                continue
            if "item" not in child.itemprop:
                raise MicrodataError("array container child is not itemprop=item")
            items.append(
                _read_value(child, root, _resolve(root, subschema).get("items", {}))
            )
        return items
    # An array field may also appear as an ordinary occurrence (an untyped
    # item scope, or an explicitly typed object scope). Read it against the
    # item schema, not the array schema (M3).
    item_schema = _item_subschema(root, subschema)
    if datatype == "object":
        if not element.itemscope:
            raise MicrodataError("data-fhr-type=object without itemscope")
        return _read_scope(element, root, item_schema)
    if datatype in _TYPED:
        return _parse_typed(_value_of(element), datatype)
    if datatype is not None:
        raise MicrodataError(f"unknown data-fhr-type {datatype!r}")
    if element.itemscope:
        return _read_scope(element, root, item_schema)
    return _convert_untyped(_value_of(element), root, item_schema)


def _read_scope(scope, root, subschema):
    occurrences = {}
    for element, name in _property_elements(scope):
        value = _read_value(element, root, _subschema(root, subschema, name))
        occurrences.setdefault(name, []).append(value)
    record = {}
    for name, values in occurrences.items():
        field = _subschema(root, subschema, name)
        if _json_type(root, field) == "array":
            if len(values) == 1 and isinstance(values[0], list):
                # A single array container is unwrapped. Repeated containers
                # stay as nested lists, so schema validation rejects them
                # (docs/FHT-MICRODATA.md "Repeated properties").
                record[name] = values[0]
            else:
                # Ordinary repeated properties form one flat list (M4).
                record[name] = values
        elif len(values) == 1:
            record[name] = values[0]
        else:
            record[name] = values  # M4: a repeated property becomes a list.
    return record


def _finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise MicrodataError("non-finite numbers are not metadata values (R13)")
    if isinstance(value, dict):
        for item in value.values():
            _finite(item)
    elif isinstance(value, list):
        for item in value:
            _finite(item)


def _html_text(value):
    # Check only emitted/extracted text, not values omitted under M5.
    if isinstance(value, str) and any(
        char == "\x00" or 0xD800 <= ord(char) <= 0xDFFF for char in value
    ):
        raise MicrodataError("text is not losslessly representable in HTML")
    if isinstance(value, dict):
        for key, item in value.items():
            _html_text(key)
            _html_text(item)
    elif isinstance(value, list):
        for item in value:
            _html_text(item)


def resolve_schema(selection, schema):
    """V7 draft identity only: there is no released FHT contract to select."""
    if selection != FHT_ITEMTYPE:
        raise MicrodataError(f"unsupported FHT draft schema selection: {selection!r}")
    return schema


def _validate(record, schema):
    _finite(record)
    if record.get("schemaVersion") != "1.0":
        raise MicrodataError("unsupported FHT draft schemaVersion")
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record)
    )
    if errors:
        raise MicrodataError(
            "schema-invalid metadata: " + "; ".join(error.message for error in errors)
        )


def _draft_schema(allow_draft, schema):
    if not allow_draft:
        raise MicrodataError("FHT draft reference binding requires allow_draft=True")
    selected = (
        schema
        if schema is not None
        else json.loads((ROOT / "fht.json").read_text(encoding="utf-8"))
    )
    if selected.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise MicrodataError("reference requires the declared FHT Draft 2020-12 schema")
    Draft202012Validator.check_schema(selected)
    return selected


def read_page(text, schema=None, *, allow_draft=False):
    """Extract and schema-check one draft FHT record; never verify sequence bytes."""
    schema = _draft_schema(allow_draft, schema)
    builder = _TreeBuilder()
    # HTML preprocessing normalizes literal line endings before tokenization;
    # character references such as &#13; are decoded later and stay intact.
    builder.feed(text.replace("\r\n", "\n").replace("\r", "\n"))
    builder.close()
    scopes = [node for node in _nodes(builder.root) if node.itemscope]
    family = [
        node
        for node in scopes
        if ({FHT_ITEMTYPE} | OTHER_FAMILY_TYPES) & set(node.itemtype)
    ]
    if len(family) != 1 or FHT_ITEMTYPE not in family[0].itemtype:
        raise MicrodataError(
            "expected exactly one FHT scope and no conflicting family scope"
        )
    if OTHER_FAMILY_TYPES & set(family[0].itemtype):
        raise MicrodataError("mixed family itemtype identity")
    scope = family[0]
    selectors = [
        element for element, name in _property_elements(scope) if name == "schema"
    ]
    if len(selectors) != 1:
        raise MicrodataError("FHT scope requires exactly one schema property")
    selected = resolve_schema(_value_of(selectors[0]), schema)
    record = _read_scope(scope, selected, selected)
    if any(key.startswith("x-") for key in record):
        raise MicrodataError("extension fields are not permitted in microdata (M5)")
    _validate(record, selected)
    _html_text(record)
    return record


def _rows(record):
    return "".join(
        '<tr><th scope="row">'
        + escape(name)
        + "</th><td>"
        + _write_property(name, value)
        + "</td></tr>"
        for name, value in record.items()
    )


def _write_property(name, value):
    prop = escape(name, quote=True)
    if isinstance(value, dict):
        content = (
            "<table><caption>Object: "
            + prop
            + "</caption><tbody>"
            + _rows(value)
            + "</tbody></table>"
        )
        tag = "li" if name == "item" else "div"
        return f'<{tag} itemprop="{prop}" itemscope data-fhr-type="object">{content}</{tag}>'
    if isinstance(value, list):
        return (
            f'<ol itemprop="{prop}" data-fhr-type="array">'
            + "".join(_write_property("item", item) for item in value)
            + "</ol>"
        )
    if isinstance(value, bool):
        datatype, text = "boolean", json.dumps(value)
    elif isinstance(value, int):
        datatype, text = "integer", json.dumps(value)
    elif isinstance(value, float):
        datatype, text = "number", json.dumps(value, allow_nan=False)
    else:
        datatype, text = "string", value
    tag = "li" if name == "item" else "span"
    return f'<{tag} itemprop="{prop}" data-fhr-type="{datatype}">{escape(text).replace(chr(13), "&#13;")}</{tag}>'


def write_page(
    record, schema=None, *, allow_draft=False, title="FHT draft metadata", warn=None
):
    """Write one visible typed table; omit M5 extension fields with an explicit warning."""
    schema = _draft_schema(allow_draft, schema)
    selected = resolve_schema(record.get("schema"), schema)
    _validate(record, selected)
    keys = [name for name in record if name.startswith("x-")]
    if keys:
        message = "microdata extension fields omitted (M5): " + ", ".join(keys)
        if warn is None:
            warnings.warn(message, stacklevel=2)
        else:
            warn(message)
    omission = (
        (
            "<p>Extension fields omitted from HTML (M5): <code>"
            + escape(", ".join(keys))
            + "</code>. Retain the original JSON/YAML record.</p>"
        )
        if keys
        else ""
    )
    emitted = {
        name: value for name, value in record.items() if not name.startswith("x-")
    }
    _html_text(emitted)
    _html_text(title)
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="robots" content="noindex"><title>' + escape(title) + "</title>"
        "<style>body{font-family:system-ui;max-width:75em;margin:2em auto;padding:0 1em}"
        "table{border-collapse:collapse;max-width:100%}th,td{border:1px solid;padding:.4em;"
        "text-align:left;vertical-align:top;overflow-wrap:anywhere}span{white-space:pre-wrap}"
        "ol{margin:0;padding-left:1.5em}</style></head><body><h1>"
        + escape(title)
        + "</h1>"
        "<p>Unreleased FHT draft binding example. Structural validation is not file, parent or biological verification.</p>"
        + omission
        + f'<table itemscope itemtype="{FHT_ITEMTYPE}"><caption>FHT metadata record</caption><tbody>'
        + _rows(emitted)
        + "</tbody></table></body></html>\n"
    )
