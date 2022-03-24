def context_matches(query_context, item_context):
  for k,v in query_context.items():
    if type(v) is list:
      if item_context.get(k) != v or v not in item_context.get(k):
        return False
    else:
      if item_context.get(k) != v:
        return False
  return True
