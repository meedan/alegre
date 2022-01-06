def context_matches(context, search_context):
  for k,v in context.items():
    if search_context.get(k) != v:
      return False
  return True
