import sys
import os
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.linkml_model.meta import SchemaDefinition, ClassDefinition, SlotDefinition, EnumDefinition

schemas_dir = os.path.abspath('schemas')
files = os.listdir(schemas_dir)
schemas = {}
for filename in files:
    if filename.endswith('.yaml'):
        path = os.path.join(schemas_dir, filename)
        view = SchemaView(path)
        schemas[view.schema.name] = view