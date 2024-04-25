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

def get_context_query(context, value_as_json=True, vars_as_hash=True):
    context_query = []
    context_hash = {}
    #Always force no results from temporary objects
    context["temporary_media"] = False
    for key, value in context.items():
        if key not in ["project_media_id", "content_type"]:
            if isinstance(value, list):
                context_clause = "("
                for i,v in enumerate(value):
                    if value_as_json:
                        context_clause += "context @> '[{\""+key+"\": "+json.dumps(value)+"}]'"
                    else:
                        if vars_as_hash:
                          context_clause += "context @> '[{\""+key+"\": :context_"+key+"_"+str(i)+"}]'"
                        else:
                          context_clause += "context @> '[{\""+key+"\": "+json.dumps(v)+"}]'"
                    if len(value)-1 != i:
                        context_clause += " OR "
                    context_hash[f"context_{key}_{i}"] = v
                context_clause += ")"
                context_query.append(context_clause)
            else:
                if value_as_json:
                    context_query.append("context @>'[{\""+key+"\": "+json.dumps(value)+"}]'")
                else:
                    if vars_as_hash:
                        context_query.append("context @>'[{\""+key+"\": :context_"+key+"}]'")
                    else:
                        context_query.append("context @>'[{\""+key+"\": "+json.dumps(value)+"}]'")
                context_hash[f"context_{key}"] = value
    return str.join(" AND ",  context_query), context_hash
