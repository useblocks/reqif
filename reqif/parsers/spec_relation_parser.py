import html
from typing import List, Optional

from reqif.models.error_handling import ReqIFMissingTagException
from reqif.models.reqif_spec_object import SpecObjectAttribute
from reqif.models.reqif_spec_relation import (
    ReqIFSpecRelation,
)
from reqif.models.reqif_types import SpecObjectAttributeType
from reqif.parsers.attribute_value_parser import AttributeValueParser


class SpecRelationParser:
    @staticmethod
    def parse(xml_spec_relation) -> ReqIFSpecRelation:
        assert xml_spec_relation.tag == "SPEC-RELATION"

        children_tags = list(map(lambda el: el.tag, list(xml_spec_relation)))
        assert "TYPE" in children_tags
        if "SOURCE" not in children_tags:
            raise ReqIFMissingTagException(
                xml_node=xml_spec_relation, tag="SOURCE"
            ) from None
        if "TARGET" not in children_tags:
            raise ReqIFMissingTagException(
                xml_node=xml_spec_relation, tag="TARGET"
            ) from None

        attributes = xml_spec_relation.attrib
        assert "IDENTIFIER" in attributes, f"{attributes}"
        identifier = attributes["IDENTIFIER"]

        description: Optional[str] = (
            attributes["DESC"] if "DESC" in attributes else None
        )

        last_change: Optional[str] = (
            attributes["LAST-CHANGE"] if "LAST-CHANGE" in attributes else None
        )

        long_name: Optional[str] = (
            attributes["LONG-NAME"] if "LONG-NAME" in attributes else None
        )

        relation_type_ref = (
            xml_spec_relation.find("TYPE").find("SPEC-RELATION-TYPE-REF").text
        )

        spec_relation_source = (
            xml_spec_relation.find("SOURCE").find("SPEC-OBJECT-REF").text
        )

        spec_relation_target = (
            xml_spec_relation.find("TARGET").find("SPEC-OBJECT-REF").text
        )

        values_attribute: Optional[SpecObjectAttribute] = None
        xml_values = xml_spec_relation.find("VALUES")
        if xml_values is not None:
            for xml_value in xml_values:
                if xml_value.tag == "ATTRIBUTE-VALUE-STRING":
                    attribute_value = xml_value.attrib["THE-VALUE"]
                    definition_ref = xml_value[0][0].text
                    values_attribute = SpecObjectAttribute(
                        xml_node=xml_value,
                        attribute_type=SpecObjectAttributeType.STRING,
                        definition_ref=definition_ref,
                        value=attribute_value,
                    )
                elif xml_value.tag == "ATTRIBUTE-VALUE-XHTML":
                    values_attribute = AttributeValueParser.parse_xhtml_attribute_value(
                        xml_value
                    )
                elif xml_value.tag == "ATTRIBUTE-VALUE-INTEGER":
                    attribute_value = xml_value.attrib["THE-VALUE"]
                    definition_ref = xml_value[0][0].text
                    values_attribute = SpecObjectAttribute(
                        xml_node=xml_value,
                        attribute_type=SpecObjectAttributeType.INTEGER,
                        definition_ref=definition_ref,
                        value=attribute_value,
                    )
                else:
                    raise NotImplementedError
                break

        spec_relation = ReqIFSpecRelation(
            xml_node=xml_spec_relation,
            description=description,
            identifier=identifier,
            last_change=last_change,
            long_name=long_name,
            relation_type_ref=relation_type_ref,
            source=spec_relation_source,
            target=spec_relation_target,
            values_attribute=values_attribute,
        )
        return spec_relation

    @staticmethod
    def unparse(spec_relation: ReqIFSpecRelation):
        parts: list[str] = ["        <SPEC-RELATION"]
        if spec_relation.description is not None:
            parts.append(f' DESC="{spec_relation.description}"')
        parts.append(f' IDENTIFIER="{spec_relation.identifier}"')
        if spec_relation.last_change is not None:
            parts.append(f' LAST-CHANGE="{spec_relation.last_change}"')
        if spec_relation.long_name is not None:
            parts.append(f' LONG-NAME="{html.escape(spec_relation.long_name)}"')
        parts.append(">\n")

        children_tags: List[str]
        if spec_relation.xml_node is not None:
            children_tags = list(map(lambda el: el.tag, list(spec_relation.xml_node)))
        else:
            children_tags = ["TYPE", "SOURCE", "TARGET", "VALUES"]
        for tag in children_tags:
            if tag == "TYPE":
                parts.append(
                    f"          <TYPE>\n"
                    f"            <SPEC-RELATION-TYPE-REF>{spec_relation.relation_type_ref}</SPEC-RELATION-TYPE-REF>\n"
                    f"          </TYPE>\n"
                )
            elif tag == "SOURCE":
                parts.append(
                    f"          <SOURCE>\n"
                    f"            <SPEC-OBJECT-REF>{spec_relation.source}</SPEC-OBJECT-REF>\n"
                    f"          </SOURCE>\n"
                )
            elif tag == "TARGET":
                parts.append(
                    f"          <TARGET>\n"
                    f"            <SPEC-OBJECT-REF>{spec_relation.target}</SPEC-OBJECT-REF>\n"
                    f"          </TARGET>\n"
                )
            elif tag == "VALUES":
                if spec_relation.values_attribute is not None:
                    parts.append(
                        AttributeValueParser.unparse_attribute_values(
                            [spec_relation.values_attribute]
                        )
                    )
            else:
                raise NotImplementedError(tag)

        parts.append("        </SPEC-RELATION>\n")
        return "".join(parts)
