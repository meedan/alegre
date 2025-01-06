from app.main.lib.elasticsearch import get_all_documents_matching_context
from app.main.lib import text_similarity
from app.main.lib import image_similarity
from flask import current_app as app
from sqlalchemy import text

from app.main import db
from app.main.lib.helpers import context_matches
from app.main.lib.similarity_helpers import get_context_query
from app.main.lib.error_log import ErrorLog
from app.main.model.video import Video
from app.main.model.image import ImageModel
from app.main.model.audio import Audio
from app.main.model.edge import Edge
from app.main.model.node import Node

from app.main.lib import similarity

def model_response_package(graph, url, doc_id):
  return {
    "url": url,
    "doc_id": doc_id,
    "context": graph.context,
    "command": "search",
    "threshold": graph.threshold,
    "match_across_content_types": True
  }

def audio_model():
  return SharedModel.get_client()

def video_model():
  return SharedModel.get_client(app.config['VIDEO_MODEL'])

def get_iterable_objects(graph, data_type):
  try:
    _ = graph.context.pop('project_media_id', None)
    context_query, _ = get_context_query(graph.context, False, False)
    if data_type == "image":
      return ImageModel.query.filter(text(context_query)).order_by(ImageModel.id.asc())
    elif data_type == "video":
      return Video.query.filter(text(context_query)).order_by(Video.id.asc())
    elif data_type == "audio":
      return Audio.query.filter(text(context_query)).order_by(Audio.id.asc())
    elif data_type == "text":
      return get_all_documents_matching_context(graph.context)
  except Exception as err:
    ErrorLog.notify(err)
  return []

def package_item_for_query(item, graph, data_type):
  if data_type == "image":
    return {"url": item.url, "context": graph.context, "threshold": graph.threshold}
  elif data_type == "video":
    return {"url": item.url, "doc_id": item.doc_id, "context": graph.context, "threshold": graph.threshold}
  elif data_type == "audio":
    return {"url": item.url, "doc_id": item.doc_id, "context": graph.context, "threshold": graph.threshold}
  elif data_type == "text":
    vector_keys = [k for k in item["_source"].keys() if "vector" in k]
    vector_key = ""
    model = graph.context.get("model") or "elasticsearch"
    if vector_keys:
      vector_key = vector_keys[0]
    return {
      "models": [model],
      "threshold": graph.threshold,
      "content": item.get("_source").get("content"),
      "vector": item.get("_source").get(vector_key),
    }

def get_matches_for_item(graph, item, data_type):
  try:
    response = similarity.get_similar_items(package_item_for_query(item, graph, data_type), data_type) 
    # image:
    #[{'id': 1, 'sha256': '1235', 'phash': 2938172487634, 'url': 'https://assets.checkmedia.org/uploads/blah.jpeg', 'context': [{'team_id': 1, 'project_media_id': 123}], 'score': 0}]
    # audio/video:
    #[{'id': 1234, 'doc_id': 'boop', 'chromaprint_fingerprint': [1,2,3], 'url': 'https://assets.checkmedia.org/uploads/blah.mp4', 'context': [{'team_id': 1, 'content_type': 'video', 'has_custom_id': True, 'project_media_id': 123456}], 'score': 1.0}]
    if data_type == "text":
      project_media_id = item.get("_source", {}).get("context", {}).get("project_media_id", 0) #ugly hack to grab only cases where they arrived earlier, we have no datestamps or implicit timing otherwise... this will need a refactor for all the items across alegre in order to address.
      response = restrict_text_result_to_predecessors(response, project_media_id)
    if response:
      results = response.get("result", [])
      if results:
        return [results[0]]
  except Exception as err:
    ErrorLog.notify(err)
  return []

def restrict_text_result_to_predecessors(text_result, project_media_id):
  return {"result": [e for e in text_result.get("result", []) if e.get("_source", {}).get("context", {}).get("project_media_id", project_media_id) < project_media_id]} #[{'_index': 'alegre_similarity', '_type': '_doc', '_id': '1232413rfaefa43ghgqfq', '_score': 82.726, '_source': {'content': 'Some content', 'context': {'team_id': 1, 'field': 'original_title', 'project_media_id': 1, 'has_custom_id': True}}}]

def get_node_context_from_item_or_match(item_or_match):
  context = []
  iom_context = []
  if isinstance(item_or_match, dict):
    iom_context = item_or_match.get("context")
  elif "context" in dir(item_or_match):
    iom_context = item_or_match.context
  if isinstance(iom_context, dict):
    context.append(iom_context)
  elif isinstance(iom_context, list):
    for c in iom_context:
      context.append(c)
  return context

def generate_edges_for_type(graph, data_type, item_iterator=get_iterable_objects, match_resolver=get_matches_for_item):
  for item in item_iterator(graph, data_type):
    item_node_data = get_node_context_from_item_or_match(item)
    item_node = get_or_init_node(get_item_or_match_id(item), data_type, get_node_context_from_item_or_match(item))
    for match in match_resolver(graph, item, data_type):
      match_node_data = get_node_context_from_item_or_match(match)
      match_node = get_or_init_node(get_item_or_match_id(match), data_type, get_node_context_from_item_or_match(match))
      nodes = [item_node, match_node]
      nodes.sort(key=lambda x:x.id)
      source, target = nodes
      edge = generate_edge(source, target, match, graph, data_type)

def get_context_for_node(node, graph):
  contexts = [c for c in node.context if context_matches(graph.context, c)]
  if contexts:
    return contexts[0]
  else:
    return {}
  
def generate_edge(source, target, match, graph, data_type):
  source_context = get_context_for_node(source, graph)
  target_context = get_context_for_node(target, graph)
  edge = Edge.query.filter_by(source_id=source.id, target_id=target.id, graph_id=graph.id, edge_context={"data_type": data_type}).first()
  if not edge:
    edge = Edge(
      source_id=source.id,
      source_context=source_context,
      target_id=target.id,
      target_context=target_context,
      graph_id=graph.id,
      edge_type="similarity",
      edge_weight=get_edge_score(match),
      edge_context={"data_type": data_type},
      context=graph.context
    )
    db.session.add(edge)
    db.session.flush()
    db.session.commit()
  return edge

def get_or_init_node(node_data_type_id, node_data_type, node_context):
  node = Node.query.filter_by(data_type_id=str(node_data_type_id), data_type=node_data_type).first()
  if node:
    return node
  else:
    node = Node(
      data_type_id=str(node_data_type_id),
      data_type=node_data_type,
      context=node_context,
      data=None
    )
    db.session.add(node)
    db.session.flush()
    db.session.commit()
  return node

def get_edge_score(match):
  return match.get("score") or match.get("_score") or 0

def get_item_or_match_id(item_or_match):
  if "id" in dir(item_or_match):
    return item_or_match.id
  elif isinstance(item_or_match, dict):
    if "id" in item_or_match:
      return item_or_match.get("id")
    elif "_id" in item_or_match:
      return item_or_match.get("_id")

