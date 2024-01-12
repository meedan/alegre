def context_matches(query_context, item_context):
  for k,v in query_context.items():
    if k != "project_media_id":
      if isinstance(v, list):
        if item_context.get(k) != v and item_context.get(k) not in v:
          return False
      else:
        if item_context.get(k) != v:
          return False
  return True
