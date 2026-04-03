import io
from typing import List
from zipfile import ZIP_DEFLATED, ZipFile

from reqif.models.reqif_namespace_info import ReqIFNamespaceInfo
from reqif.models.reqif_relation_group_type import ReqIFRelationGroupType
from reqif.models.reqif_spec_object_type import ReqIFSpecObjectType
from reqif.models.reqif_spec_relation_type import ReqIFSpecRelationType
from reqif.models.reqif_specification_type import ReqIFSpecificationType
from reqif.parsers.data_type_parser import DataTypeParser
from reqif.parsers.header_parser import ReqIFHeaderParser
from reqif.parsers.relation_group_parser import ReqIFRelationGroupParser
from reqif.parsers.spec_object_parser import SpecObjectParser
from reqif.parsers.spec_relation_parser import SpecRelationParser
from reqif.parsers.spec_types.relation_group_type_parser import (
    RelationGroupTypeParser,
)
from reqif.parsers.spec_types.spec_object_type_parser import (
    SpecObjectTypeParser,
)
from reqif.parsers.spec_types.spec_relation_type_parser import (
    SpecRelationTypeParser,
)
from reqif.parsers.spec_types.specification_type_parser import (
    SpecificationTypeParser,
)
from reqif.parsers.specification_parser import ReqIFSpecificationParser
from reqif.reqif_bundle import ReqIFBundle, ReqIFZBundle


class ReqIFUnparser:
    @staticmethod
    def unparse(bundle: ReqIFBundle) -> str:
        parts: List[str] = ['<?xml version="1.0" encoding="UTF-8"?>\n']

        parts.append(ReqIFUnparser.unparse_namespace_info(bundle.namespace_info))

        if bundle.req_if_header is not None:
            parts.append(ReqIFHeaderParser.unparse(bundle.req_if_header))

        if bundle.core_content is not None:
            parts.append("  <CORE-CONTENT>\n")
            reqif_content = bundle.core_content.req_if_content
            if reqif_content:
                parts.append("    <REQ-IF-CONTENT>\n")

                if reqif_content.data_types is not None:
                    parts.append("      <DATATYPES>\n")
                    for data_type in reqif_content.data_types:
                        parts.append(DataTypeParser.unparse(data_type))
                    parts.append("      </DATATYPES>\n")

                if reqif_content.spec_types is not None:
                    parts.append("      <SPEC-TYPES>\n")
                    for spec_type in reqif_content.spec_types:
                        if isinstance(spec_type, ReqIFSpecObjectType):
                            parts.append(SpecObjectTypeParser.unparse(spec_type))
                        elif isinstance(spec_type, ReqIFSpecRelationType):
                            parts.append(SpecRelationTypeParser.unparse(spec_type))
                        elif isinstance(spec_type, ReqIFSpecificationType):
                            parts.append(SpecificationTypeParser.unparse(spec_type))
                        elif isinstance(spec_type, ReqIFRelationGroupType):
                            parts.append(RelationGroupTypeParser.unparse(spec_type))
                    parts.append("      </SPEC-TYPES>\n")

                if reqif_content.spec_objects is not None:
                    parts.append("      <SPEC-OBJECTS>\n")
                    for spec_object in reqif_content.spec_objects:
                        parts.append(SpecObjectParser.unparse(spec_object))
                    parts.append("      </SPEC-OBJECTS>\n")

                if reqif_content.spec_relations is not None:
                    parts.append("      <SPEC-RELATIONS>\n")
                    for spec_relation in reqif_content.spec_relations:
                        parts.append(SpecRelationParser.unparse(spec_relation))
                    parts.append("      </SPEC-RELATIONS>\n")

                if reqif_content.specifications is not None:
                    parts.append("      <SPECIFICATIONS>\n")
                    for specification in reqif_content.specifications:
                        parts.append(ReqIFSpecificationParser.unparse(specification))
                    parts.append("      </SPECIFICATIONS>\n")

                if reqif_content.spec_relation_groups is not None:
                    parts.append("      <SPEC-RELATION-GROUPS>\n")
                    for spec_relation_group in reqif_content.spec_relation_groups:
                        parts.append(ReqIFRelationGroupParser.unparse(spec_relation_group))
                    parts.append("      </SPEC-RELATION-GROUPS>\n")

                parts.append("    </REQ-IF-CONTENT>\n")
            parts.append("  </CORE-CONTENT>\n")

        if bundle.tool_extensions_tag_exists:
            parts.append("  <TOOL-EXTENSIONS>\n")
            parts.append("  </TOOL-EXTENSIONS>\n")

        parts.append("</REQ-IF>\n")
        return "".join(parts)

    @staticmethod
    def unparse_namespace_info(namespace_info: ReqIFNamespaceInfo) -> str:
        assert isinstance(namespace_info, ReqIFNamespaceInfo)

        if namespace_info.original_reqif_tag_dump is not None:
            return namespace_info.original_reqif_tag_dump + "\n"

        xml_output = "<REQ-IF "

        namespace_components: List[str] = []
        if namespace_info.namespace is not None:
            namespace_components.append(f'xmlns="{namespace_info.namespace}"')
        if namespace_info.schema_namespace is not None:
            namespace_components.append(
                f'xmlns:xsi="{namespace_info.schema_namespace}"'
            )
        if namespace_info.configuration is not None:
            namespace_components.append(
                f'xmlns:configuration="{namespace_info.configuration}"'
            )
        if namespace_info.namespace_id is not None:
            namespace_components.append(f'xmlns:id="{namespace_info.namespace_id}"')
        if namespace_info.namespace_xhtml is not None:
            namespace_components.append(
                f'xmlns:xhtml="{namespace_info.namespace_xhtml}"'
            )
        if namespace_info.schema_location is not None:
            namespace_components.append(
                f'xsi:schemaLocation="{namespace_info.schema_location}"'
            )
        if namespace_info.language is not None:
            namespace_components.append(f'xml:lang="{namespace_info.language}"')
        assert len(namespace_components) > 0, (
            "Expect at least one namespace component, got none."
        )
        xml_output += " ".join(namespace_components)

        xml_output += ">\n"
        return xml_output


class ReqIFZUnparser:
    @staticmethod
    def unparse(bundle: ReqIFZBundle) -> bytes:
        """
        Based on:
        Python in-memory zip library
        https://stackoverflow.com/a/44946732/598057
        """

        zip_buffer = io.BytesIO()
        with ZipFile(zip_buffer, "a", ZIP_DEFLATED) as zip_file:
            # First write, the ReqIF files themselves.
            for filename_, reqif_bundle_ in bundle.reqif_bundles.items():
                reqif_string_ = ReqIFUnparser.unparse(reqif_bundle_)
                zip_file.writestr(filename_, reqif_string_)

            # Then write the attachments.
            for attachment, attachment_bytes in bundle.attachments.items():
                zip_file.writestr(attachment, attachment_bytes)

        return zip_buffer.getvalue()
