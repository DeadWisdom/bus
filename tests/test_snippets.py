from valet.templates import render_snippet

class SchemaDefinition:
    name: str

expected = """
  <schema-item class="class element" itemscope itemid="https://w3id.org/linkml/examples/personinfo" itemtype="https://w3id.org/linkml/SchemaDefinition">
  <a href="/ns/personinfo">
    <sl-icon class="icon" name="icon" aria-hidden="true" library="default"></sl-icon>
    <span class="name" itemprop="name">personinfo</span>
  </a>
  </schema-item>
"""

def test_load():
    personinfo = SchemaDefinition()
    personinfo.name = "personinfo"
    result = render_snippet('classElement', 
                            element=personinfo, 
                            id="https://w3id.org/linkml/examples/personinfo", 
                            url="/ns/personinfo",
                            type="https://w3id.org/linkml/SchemaDefinition",
                            icon="person-circle")
    print(result)
    print(expected)
    assert result.strip() == expected.strip()
