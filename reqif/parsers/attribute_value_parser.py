import html
from typing import Any, List, Optional

from lxml import etree

from reqif.helpers.lxml import (
    lxml_convert_children_from_reqif_ns_xhtml_string,
    lxml_is_comment_node,
    lxml_stringify_children,
    lxml_stringify_namespaced_children,
)
from reqif.helpers.string.xhtml_indent import reqif_unindent_xhtml_string
from reqif.models.reqif_spec_object import SpecObjectAttribute
from reqif.models.reqif_types import SpecObjectAttributeType


def _escape_xml_attr(s: str) -> str:
    """Fast XML attribute escaping — skips replace chain when no special chars present."""
    if "&" not in s and "<" not in s and ">" not in s and '"' not in s:
        return s
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


ATTRIBUTE_STRING_TEMPLATE = """\
            <ATTRIBUTE-VALUE-STRING THE-VALUE="{value}">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-STRING-REF>{definition_ref}</ATTRIBUTE-DEFINITION-STRING-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-STRING>
"""

ATTRIBUTE_INTEGER_TEMPLATE = """\
            <ATTRIBUTE-VALUE-INTEGER THE-VALUE="{value}">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-INTEGER-REF>{definition_ref}</ATTRIBUTE-DEFINITION-INTEGER-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-INTEGER>
"""

ATTRIBUTE_REAL_TEMPLATE = """\
            <ATTRIBUTE-VALUE-REAL THE-VALUE="{value}">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-REAL-REF>{definition_ref}</ATTRIBUTE-DEFINITION-REAL-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-REAL>
"""

ATTRIBUTE_ENUM_VALUE_TEMPLATE = """\
                <ENUM-VALUE-REF>{value}</ENUM-VALUE-REF>
"""
ATTRIBUTE_ENUMERATION_TEMPLATE = """\
            <ATTRIBUTE-VALUE-ENUMERATION>
              <VALUES>
{values}
              </VALUES>
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-ENUMERATION-REF>{definition_ref}</ATTRIBUTE-DEFINITION-ENUMERATION-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-ENUMERATION>
"""
ATTRIBUTE_ENUMERATION_TEMPLATE_REVERSE = """\
            <ATTRIBUTE-VALUE-ENUMERATION>
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-ENUMERATION-REF>{definition_ref}</ATTRIBUTE-DEFINITION-ENUMERATION-REF>
              </DEFINITION>
              <VALUES>
{values}
              </VALUES>
            </ATTRIBUTE-VALUE-ENUMERATION>
"""

ATTRIBUTE_DATE_TEMPLATE = """\
            <ATTRIBUTE-VALUE-DATE THE-VALUE="{value}">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-DATE-REF>{definition_ref}</ATTRIBUTE-DEFINITION-DATE-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-DATE>
"""

ATTRIBUTE_XHTML_TEMPLATE = """\
            <ATTRIBUTE-VALUE-XHTML>
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-XHTML-REF>{definition_ref}</ATTRIBUTE-DEFINITION-XHTML-REF>
              </DEFINITION>
              <THE-VALUE>{value}</THE-VALUE>
            </ATTRIBUTE-VALUE-XHTML>
"""

ATTRIBUTE_BOOLEAN_TEMPLATE = """\
            <ATTRIBUTE-VALUE-BOOLEAN THE-VALUE="{value}">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-BOOLEAN-REF>{definition_ref}</ATTRIBUTE-DEFINITION-BOOLEAN-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-BOOLEAN>
"""


class AttributeValueParser:
    @staticmethod
    def parse_attribute_values(
        xml_attribute_values: Optional[Any],
    ) -> Optional[List[SpecObjectAttribute]]:
        if xml_attribute_values is None:
            return None

        attributes: List[SpecObjectAttribute] = []
        for attribute_xml in xml_attribute_values:
            if lxml_is_comment_node(attribute_xml):
                continue
            if attribute_xml.tag == "ATTRIBUTE-VALUE-STRING":
                attribute_value = attribute_xml.attrib["THE-VALUE"]
                attribute_definition_ref = attribute_xml[0][0].text
                attribute = SpecObjectAttribute(
                    xml_node=attribute_xml,
                    attribute_type=SpecObjectAttributeType.STRING,
                    definition_ref=attribute_definition_ref,
                    value=attribute_value,
                )
            elif attribute_xml.tag == "ATTRIBUTE-VALUE-ENUMERATION":
                attribute_definition_ref = (
                    attribute_xml.find("DEFINITION")
                    .find("ATTRIBUTE-DEFINITION-ENUMERATION-REF")
                    .text
                )
                attribute_xml_values = attribute_xml.find("VALUES")
                assert attribute_xml_values is not None
                xml_enum_value_refs = attribute_xml_values.getchildren()
                enum_value_refs: List[str] = []
                for xml_enum_value_ref in xml_enum_value_refs:
                    attribute_value = xml_enum_value_ref.text
                    enum_value_refs.append(attribute_value)
                attribute = SpecObjectAttribute(
                    xml_node=attribute_xml,
                    attribute_type=SpecObjectAttributeType.ENUMERATION,
                    definition_ref=attribute_definition_ref,
                    value=enum_value_refs,
                )
            elif attribute_xml.tag == "ATTRIBUTE-VALUE-INTEGER":
                attribute_value = attribute_xml.attrib["THE-VALUE"]

                attribute_definition_ref = (
                    attribute_xml.find("DEFINITION")
                    .find("ATTRIBUTE-DEFINITION-INTEGER-REF")
                    .text
                )
                attribute = SpecObjectAttribute(
                    xml_node=attribute_xml,
                    attribute_type=SpecObjectAttributeType.INTEGER,
                    definition_ref=attribute_definition_ref,
                    value=attribute_value,
                )
            elif attribute_xml.tag == "ATTRIBUTE-VALUE-REAL":
                attribute_value = attribute_xml.attrib["THE-VALUE"]

                attribute_definition_ref = (
                    attribute_xml.find("DEFINITION")
                    .find("ATTRIBUTE-DEFINITION-REAL-REF")
                    .text
                )
                attribute = SpecObjectAttribute(
                    xml_node=attribute_xml,
                    attribute_type=SpecObjectAttributeType.REAL,
                    definition_ref=attribute_definition_ref,
                    value=attribute_value,
                )
            elif attribute_xml.tag == "ATTRIBUTE-VALUE-BOOLEAN":
                attribute_value = attribute_xml.attrib["THE-VALUE"]

                attribute_definition_ref = (
                    attribute_xml.find("DEFINITION")
                    .find("ATTRIBUTE-DEFINITION-BOOLEAN-REF")
                    .text
                )
                attribute = SpecObjectAttribute(
                    xml_node=attribute_xml,
                    attribute_type=SpecObjectAttributeType.BOOLEAN,
                    definition_ref=attribute_definition_ref,
                    value=attribute_value,
                )
            elif attribute_xml.tag == "ATTRIBUTE-VALUE-DATE":
                attribute_value = attribute_xml.attrib["THE-VALUE"]

                attribute_definition_ref = (
                    attribute_xml.find("DEFINITION")
                    .find("ATTRIBUTE-DEFINITION-DATE-REF")
                    .text
                )
                attribute = SpecObjectAttribute(
                    xml_node=attribute_xml,
                    attribute_type=SpecObjectAttributeType.DATE,
                    definition_ref=attribute_definition_ref,
                    value=attribute_value,
                )
            elif attribute_xml.tag == "ATTRIBUTE-VALUE-XHTML":
                attribute = AttributeValueParser.parse_xhtml_attribute_value(
                    attribute_xml
                )
            else:
                raise NotImplementedError(etree.tostring(attribute_xml))
            attributes.append(attribute)

        return attributes

    @staticmethod
    def unparse_attribute_values(
        attribute_values: Optional[List[SpecObjectAttribute]],
    ):
        if attribute_values is None:
            return ""
        if len(attribute_values) == 0:
            return "          <VALUES/>\n"

        parts: List[str] = ["          <VALUES>\n"]
        _a = parts.append  # local alias avoids repeated attribute lookup
        for attribute in attribute_values:
            definition_ref = attribute.definition_ref
            value = attribute.value
            if attribute.attribute_type == SpecObjectAttributeType.STRING:
                assert isinstance(value, str), value
                _a('            <ATTRIBUTE-VALUE-STRING THE-VALUE="')
                _a(_escape_xml_attr(value))
                _a('">\n              <DEFINITION>\n                <ATTRIBUTE-DEFINITION-STRING-REF>')
                _a(definition_ref)
                _a("</ATTRIBUTE-DEFINITION-STRING-REF>\n              </DEFINITION>\n            </ATTRIBUTE-VALUE-STRING>\n")
            elif attribute.attribute_type == SpecObjectAttributeType.INTEGER:
                assert isinstance(value, str)
                _a('            <ATTRIBUTE-VALUE-INTEGER THE-VALUE="')
                _a(value)
                _a('">\n              <DEFINITION>\n                <ATTRIBUTE-DEFINITION-INTEGER-REF>')
                _a(definition_ref)
                _a("</ATTRIBUTE-DEFINITION-INTEGER-REF>\n              </DEFINITION>\n            </ATTRIBUTE-VALUE-INTEGER>\n")
            elif attribute.attribute_type == SpecObjectAttributeType.REAL:
                assert isinstance(value, str)
                _a('            <ATTRIBUTE-VALUE-REAL THE-VALUE="')
                _a(value)
                _a('">\n              <DEFINITION>\n                <ATTRIBUTE-DEFINITION-REAL-REF>')
                _a(definition_ref)
                _a("</ATTRIBUTE-DEFINITION-REAL-REF>\n              </DEFINITION>\n            </ATTRIBUTE-VALUE-REAL>\n")
            elif attribute.attribute_type == SpecObjectAttributeType.ENUMERATION:
                if attribute.xml_node is not None:
                    children_tags = list(
                        map(lambda el: el.tag, list(attribute.xml_node))
                    )
                else:
                    children_tags = ["VALUES", "DEFINITION"]
                enum_values_then_definition_order = children_tags.index(
                    "VALUES"
                ) < children_tags.index("DEFINITION")

                assert enum_values_then_definition_order is not None
                assert isinstance(value, list)
                enum_values: str = "".join(
                    f"                <ENUM-VALUE-REF>{v}</ENUM-VALUE-REF>\n"
                    for v in value
                ).rstrip()

                if enum_values_then_definition_order:
                    _a("            <ATTRIBUTE-VALUE-ENUMERATION>\n              <VALUES>\n")
                    _a(enum_values)
                    _a("\n              </VALUES>\n              <DEFINITION>\n                <ATTRIBUTE-DEFINITION-ENUMERATION-REF>")
                    _a(definition_ref)
                    _a("</ATTRIBUTE-DEFINITION-ENUMERATION-REF>\n              </DEFINITION>\n            </ATTRIBUTE-VALUE-ENUMERATION>\n")
                else:
                    _a("            <ATTRIBUTE-VALUE-ENUMERATION>\n              <DEFINITION>\n                <ATTRIBUTE-DEFINITION-ENUMERATION-REF>")
                    _a(definition_ref)
                    _a("</ATTRIBUTE-DEFINITION-ENUMERATION-REF>\n              </DEFINITION>\n              <VALUES>\n")
                    _a(enum_values)
                    _a("\n              </VALUES>\n            </ATTRIBUTE-VALUE-ENUMERATION>\n")
            elif attribute.attribute_type == SpecObjectAttributeType.DATE:
                assert isinstance(value, str)
                _a('            <ATTRIBUTE-VALUE-DATE THE-VALUE="')
                _a(value)
                _a('">\n              <DEFINITION>\n                <ATTRIBUTE-DEFINITION-DATE-REF>')
                _a(definition_ref)
                _a("</ATTRIBUTE-DEFINITION-DATE-REF>\n              </DEFINITION>\n            </ATTRIBUTE-VALUE-DATE>\n")
            elif attribute.attribute_type == SpecObjectAttributeType.XHTML:
                assert isinstance(value, str)
                _a("            <ATTRIBUTE-VALUE-XHTML>\n              <DEFINITION>\n                <ATTRIBUTE-DEFINITION-XHTML-REF>")
                _a(definition_ref)
                _a("</ATTRIBUTE-DEFINITION-XHTML-REF>\n              </DEFINITION>\n              <THE-VALUE>")
                _a(value)
                _a("</THE-VALUE>\n            </ATTRIBUTE-VALUE-XHTML>\n")
            elif attribute.attribute_type == SpecObjectAttributeType.BOOLEAN:
                assert isinstance(value, str)
                _a('            <ATTRIBUTE-VALUE-BOOLEAN THE-VALUE="')
                _a(value)
                _a('">\n              <DEFINITION>\n                <ATTRIBUTE-DEFINITION-BOOLEAN-REF>')
                _a(definition_ref)
                _a("</ATTRIBUTE-DEFINITION-BOOLEAN-REF>\n              </DEFINITION>\n            </ATTRIBUTE-VALUE-BOOLEAN>\n")
            else:
                raise NotImplementedError(attribute)

        _a("          </VALUES>\n")
        return "".join(parts)

    @staticmethod
    def parse_xhtml_attribute_value(xml_attribute_value) -> SpecObjectAttribute:
        assert "ATTRIBUTE-VALUE-XHTML" in xml_attribute_value.tag
        the_value = xml_attribute_value.find("THE-VALUE")

        # Edge case: There are no <xhtml:...> or <reqif-xhtml...> tags.
        if len(the_value.nsmap) > 0:
            attribute_value = lxml_stringify_namespaced_children(the_value)
            attribute_value_stripped_xhtml = reqif_unindent_xhtml_string(
                lxml_convert_children_from_reqif_ns_xhtml_string(the_value)
            )
        else:
            attribute_value = lxml_stringify_children(the_value)
            attribute_value_stripped_xhtml = reqif_unindent_xhtml_string(
                attribute_value
            )
        attribute_definition_ref = (
            xml_attribute_value.find("DEFINITION")
            .find("ATTRIBUTE-DEFINITION-XHTML-REF")
            .text
        )
        return SpecObjectAttribute(
            attribute_type=SpecObjectAttributeType.XHTML,
            definition_ref=attribute_definition_ref,
            value=attribute_value,
            value_stripped_xhtml=attribute_value_stripped_xhtml,
            xml_node=xml_attribute_value,
        )

    @staticmethod
    def unparse_xhtml_attribute_value(
        attribute_value: SpecObjectAttribute,
    ) -> str:
        assert isinstance(attribute_value.value, str)
        return ATTRIBUTE_XHTML_TEMPLATE.format(
            definition_ref=attribute_value.definition_ref,
            value=attribute_value.value,
        )
