def context_matches(query_context, item_context):
  """
    Check a pair of contexts to determine if they match - first pass is
    typically overly permissive and based in postgres - this test does an
    exact check. We do *not* check for equality or present for project_media_id,
    as they are unique to all items, and as a result, if we did use it as a
    comparator when looking at the contexts, we would never match any items, ever.
    Add more globally unique context ids into that list. It's a hack for an
    assumption we try to make everywhere else that we are agnostic about
    context values, but in this small situation, we actually need to check
    against this.
  """
  irrelevant_keys = ["project_media_id", "temporary_media"] # Changed Since 4126 PR
  for k,v in query_context.items():
    if k not in irrelevant_keys:
      if isinstance(v, list):
        if isinstance(item_context.get(k), list): # Changed Since 4126 PR
          if not set(item_context.get(k)) & set(v): # Changed Since 4126 PR
            return False # Changed Since 4126 PR
        else: # Changed Since 4126 PR
          if item_context.get(k) != v and item_context.get(k) not in v: # Changed Since 4126 PR
            return False # Changed Since 4126 PR
      else:
        if item_context.get(k) != v:
          return False
  return True