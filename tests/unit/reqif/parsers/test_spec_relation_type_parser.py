from lxml import etree

from reqif.models.reqif_spec_relation_type import ReqIFSpecRelationType
from reqif.parsers.spec_types.spec_relation_type_parser import (
    SpecRelationTypeParser,
)


def test_01_nominal_case_with_long_name() -> None:
    spec_relation_type_string = """
<SPEC-RELATION-TYPE IDENTIFIER="TEST_SPEC_RELATION_TYPE_ID" LAST-CHANGE="2025-09-26T13:38:16.654Z" LONG-NAME="TEST_SPEC_RELATION_TYPE_LONG_NAME">
  <SPEC-ATTRIBUTES />
</SPEC-RELATION-TYPE>
    """  # noqa: E501
    spec_relation_type_xml = etree.fromstring(spec_relation_type_string)

    reqif_spec_relation_type = SpecRelationTypeParser.parse(spec_relation_type_xml)
    assert isinstance(reqif_spec_relation_type, ReqIFSpecRelationType)
    assert reqif_spec_relation_type.identifier == "TEST_SPEC_RELATION_TYPE_ID"
    assert reqif_spec_relation_type.long_name == "TEST_SPEC_RELATION_TYPE_LONG_NAME"
    assert reqif_spec_relation_type.last_change == "2025-09-26T13:38:16.654Z"


def test_02_without_long_name() -> None:
    """Regression test for issue useblocks/ubconnect#155.

    According to the ReqIF XSD schema, LONG-NAME is `use="optional"` for
    SPEC-RELATION-TYPE. The parser must not crash when LONG-NAME is missing.
    """
    spec_relation_type_string = """
<SPEC-RELATION-TYPE IDENTIFIER="PV_2e48b7e166146a3741f5dc2643db1947" LAST-CHANGE="2025-09-26T13:38:16.654Z">
  <SPEC-ATTRIBUTES />
</SPEC-RELATION-TYPE>
    """  # noqa: E501
    spec_relation_type_xml = etree.fromstring(spec_relation_type_string)

    reqif_spec_relation_type = SpecRelationTypeParser.parse(spec_relation_type_xml)
    assert isinstance(reqif_spec_relation_type, ReqIFSpecRelationType)
    assert reqif_spec_relation_type.identifier == "PV_2e48b7e166146a3741f5dc2643db1947"
    assert reqif_spec_relation_type.long_name is None
    assert reqif_spec_relation_type.last_change == "2025-09-26T13:38:16.654Z"


def test_03_unparse_without_long_name_roundtrip() -> None:
    """Round-trip: parse SPEC-RELATION-TYPE without LONG-NAME, unparse, ensure
    LONG-NAME is not added in the output."""
    spec_relation_type_string = """<SPEC-RELATION-TYPE IDENTIFIER="PV_abc" LAST-CHANGE="2025-09-26T13:38:16.654Z"/>"""  # noqa: E501
    spec_relation_type_xml = etree.fromstring(spec_relation_type_string)

    reqif_spec_relation_type = SpecRelationTypeParser.parse(spec_relation_type_xml)
    output = SpecRelationTypeParser.unparse(reqif_spec_relation_type)
    assert "LONG-NAME" not in output
    assert 'IDENTIFIER="PV_abc"' in output
