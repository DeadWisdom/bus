# valet

- Put things in places...
- Side effects / Rules
- Get Handlers
- Post Handlers
- Validators

- Collections
- Resources
- Federation
- Schemas
- Functions

- Resource Type ->
  - Get Handler
  - Post Handler
  - Validator
  - Side Effects
  - Items

So we define our Resource Types...


class ResourceType(Object):
  id
  name
  handlers: list[Handler]
  items: list[ResourceType]


class Function(Object):
  id
  name
  summary
  content
  mediaType: python
  
  trigger: strings