from flask import Flask, request, Request, Response
from strawberry.flask.views import GraphQLView

from AuthHelper import get_access_token
from api.schema import schema
from markupsafe import escape

from dbs.DBSIndri import DatabaseIndri, db_semaphore

app = Flask(__name__)

app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view("graphql_view", schema=schema, graphiql=False)
)

@app.get('/oAuth/<user_id>')
def get_user_authentication(user_id):
    print(user_id)
    qs = request.query_string.decode()
    print("query_string:", qs)
    db_semaphore.acquire()
    db_indri = DatabaseIndri()
    db_indri.set_response_query_string(user_id, qs)
    consumer_data = db_indri.get_consumer_all(user_id)
    (access_key, access_secret) = get_access_token(
        consumer_data.consumer_key,
        consumer_data.consumer_secret,
        consumer_data.request_key,
        consumer_data.request_secret,
        qs
    )
    db_indri.set_access_key_and_secret(user_id, access_key, access_secret)
    db_indri.close()
    db_semaphore.release()

    return f"""
    <div
        style="
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        "
    >
        <p><bold>Thank You</bold></p>
        <p>We got your authentication user: {escape(user_id)}</p>
        <p>You can close this Tab and continue your import task</p>
    </div>
    """