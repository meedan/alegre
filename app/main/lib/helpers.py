def merge_dict_lists(list1, list2):
    """
    Merge two lists of dictionaries, ensuring all unique dictionaries are present in the final result.
    
    :param list1: First list of dictionaries.
    :param list2: Second list of dictionaries.
    :return: Merged list of unique dictionaries.
    """
    def to_hashable(d):
        return tuple((k, tuple(v) if isinstance(v, list) else v) for k, v in sorted(d.items()))
    def to_dict(t):
        return {k: list(v) if isinstance(v, tuple) else v for k, v in t}
    unique = set(to_hashable(d) for d in list1 + list2)
    return [to_dict(d) for d in unique]


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