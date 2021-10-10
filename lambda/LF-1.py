import json
import boto3

def lambda_handler(event, context):
    sqsClient = boto3.client('sqs')
    sqsQueueUrl = 'https://sqs.us-east-1.amazonaws.com/865289978067/DiningConciergeSQS'
   
    if event["currentIntent"]["name"] == "GreetingIntent":
        answer = "Hi there, how can I help?"
   
    elif event["currentIntent"]["name"] == "DiningSuggestionsIntent":
        identifiedSlots = event['currentIntent']['slots']
        messageAttributes = {
            'cuisine': {
                'DataType': 'String',
                'StringValue': identifiedSlots['cuisine']
            },
            'phone': {
                'DataType': 'Number',
                'StringValue': identifiedSlots['phone']
            },
            'numberOfpeople': {
                'DataType': 'Number',
                'StringValue': identifiedSlots['numberOfpeople']
            },
            'time': {
                'DataType': 'String',
                'StringValue': identifiedSlots['time']
            },
            'city': {
                'DataType': 'String',
                'StringValue': identifiedSlots['city']
            },
            'emailL':{
                'DataType' : 'String',
                'StringValue': identifiedSlots['emailL']
            }
       
        }
        answer = "You're all set. Once I am ready I will send you all the details over text Good day:D"
        sqsClient.send_message(QueueUrl=sqsQueueUrl, MessageBody="Sending message from lex", MessageAttributes=messageAttributes)
       
    elif event["currentIntent"]["name"] == "ThanksIntent":
        answer = "Your Welcome"
       
    response = {
        "sessionAttributes":{},
        "dialogAction":
            {
            "type": "Close",
            "fulfillmentState":"Fulfilled",
            "message":
                {
                    "contentType":"PlainText",
                    "content":answer
                }
            }
        }
   
    return response
