import json

def setup_handler(event, context):
    # TODO implement
    return {
        "statusCode": 200,
        "body": json.dumps('You Are Here, But No one else is')
    }

