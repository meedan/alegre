import json

from app.main import db

def drop_context_from_text_record(record, context):
    deleted = False
    record["contexts"] = [row for row in record.get("contexts", []) if context != row]
    db.session.add(record)
    try:
        db.session.commit()
    except Exception as exception:
        db.session.rollback()
        raise exception
    deleted = True
    return deleted

def drop_context_from_record(record, context):
    deleted = False
    record.context = [row for row in record.context if context != row]
    db.session.add(record)
    try:
        db.session.commit()
    except Exception as exception:
        db.session.rollback()
        raise exception
    deleted = True
    return deleted

def get_clause_for_list_value(key, value):
    context_clause = "("
    for i,v in enumerate(value):
        if value_as_json:
            context_clause += "context @> '[{\""+key+"\": "+json.dumps(v)+"}]'"
        else:
            if vars_as_hash:
              context_clause += "context @> '[{\""+key+"\": :context_"+key+"_"+str(i)+"}]'"
            else:
              context_clause += "context @> '[{\""+key+"\": "+json.dumps(v)+"}]'"
        if len(value)-1 != i:
            context_clause += " OR "
        context_hash[f"context_{key}_{i}"] = v
    context_clause += ")"
    return context_clause

def get_query_for_non_list_value(key, value):
    if value_as_json:
        return "context @>'[{\""+key+"\": "+json.dumps(value)+"}]'"
    else:
        if vars_as_hash:
            return "context @>'[{\""+key+"\": :context_"+key+"}]'"
        else:
            return "context @>'[{\""+key+"\": "+json.dumps(value)+"}]'"

def get_context_query(context, value_as_json=True, vars_as_hash=True):
    context_query = []
    context_hash = {}
    for key, value in context.items():
        if key not in ["project_media_id", "temporary_media", "content_type"]:
            if isinstance(value, list):
                context_query.append(get_clause_for_list_value(key, value))
            else:
                context_query.append(get_query_for_non_list_value(key, value))
                context_hash[f"context_{key}"] = value
    return str.join(" AND ",  context_query), context_hash
