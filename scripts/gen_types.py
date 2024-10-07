import httpx

contexts = {
  'as': 'https://www.w3.org/ns/activitystreams#',
  'events': 'https://schema.org/Event'
}

def load_context(url):
  r = httpx.get(url, headers={'Accept': 'application/ld+jsonm, application/json'})
  try:
    return r.json()
  except:
    open('error.json', 'w').write(r.text)
    return None


if __name__ == '__main__':
  for name, url in contexts.items():
    print(f'===== {name} - {url} ======')
    print(load_context(url))
    print('')
