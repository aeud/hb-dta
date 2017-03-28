import os
import json

"""
LAMBDA Definition: hbDtaWS
Web server, behind API Gateway
"""
def handler(event, context):
    if event.get("context").get("http-method") == "GET":
        return challenge(event, context)
    else:
        return bot(event, context)

"""
challenge is a method to catch the POST request from Facebook,
check the token, and complete the challenge
"""
def challenge(event, context):
    qs = event.get("params").get("querystring")

    token = qs.get("hub.verify_token")
    challenge = qs.get("hub.challenge")
    mode = qs.get("hub.mode")

    if mode == "subscribe" and token == os.getenv("MESSENGER_TOKEN"):
        # Cast as int the challenge, otherwise it doesn't work
        return int(challenge)
    return None

"""
api will catch the GET requests coming from Facebook messenger,
and return None (it doesn't have to return anything)
"""
def bot(event, context):
    print(event) # Log event
    """
    invoke_lambda is a trick to asynchronize the process workload
    it will invoke another AWS Lambda, asynchronously ("Event" invocation type)
    """
    invoke_lambda("hbDtaBot", event)
    return None

"""
invoke_lambda is a method to invoke asynchronously another lambda
"""
def invoke_lambda(function_name, payload):
    import boto3
    lambda_client = boto3.client("lambda")
    lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="Event",
        Payload=json.dumps(payload),
    )