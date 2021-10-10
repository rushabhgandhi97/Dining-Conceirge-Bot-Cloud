import boto3
import json
import logging
from boto3.dynamodb.conditions import Key, Attr
import requests
from botocore.exceptions import ClientError
from requests_aws4auth import AWS4Auth  
import random

senderEmailId="sk.1234cool@gmail.com"


def lambda_handler(event, context):

    #query SQS to get the messages and passing it to ES domain
    #message = getSQSMsg() #data will be a json object
    print(event)
    message=event['Records'][0]
    if message is None:
        print("No Cuisine or Phone Number key found in message")
        return
    
    cuisine = message["messageAttributes"]["cuisine"]["stringValue"]
    city = message["messageAttributes"]["city"]["stringValue"]
    #date = message["messageAttributes"]["date"]["stringValue"]
    time = message["messageAttributes"]["time"]["stringValue"]
    numberOfpeople = message["messageAttributes"]["numberOfpeople"]["stringValue"]
    phone = message["messageAttributes"]["phone"]["stringValue"]
    emailL = message["messageAttributes"]["emailL"]["stringValue"]
    phone = "+1" + phone
    
    #print(cuisine)
    #print(city)
    
    if not cuisine or not phone:
        print("No Cuisine or Phone Number key found in message")
        return
    
	
	#query to the database based on ES results, relevant info is stored. SNS implemented
    
    print("Searching for cuisine" + cuisine)
    region = 'us-east-1' # For example, us-west-1
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
   
    host = 'https://search-dine-bt-rzbhawabnrrhu3hvt5yc6vbnta.us-east-1.es.amazonaws.com/'
    index = 'restaurants'
    url = host + index + '/_search'
    query = {
        "size": 3,
        "query": {
            "multi_match": {
                "query": cuisine,
                "fields": ["categories"]
            }
        }
    }
    headers = { "Content-Type": "application/json" }
    r = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": '*'
        },
        "isBase64Encoded": False
    }
    response['body'] = r.text
    response['body'] = json.loads(response['body'])
   
    # Take a random restaurant based on cuisine and return its id
    
    
    matches = response['body']['hits']['hits']
    print(matches)
    ids= random.choices(matches,k=3)
    ids= [restaurant['_id'] for restaurant in matches]

    print(ids)
    
    dynamo = boto3.client('dynamodb')
    
    item=[]
    for id in ids:
        response = dynamo.get_item(
            TableName="yelp-dining-data",
            Key={
                "id" :{
                    "S":id
                }
            }
        )
        
        item.append(response['Item'])
        print(item)
        
    
    ses = boto3.client('ses')
    verifiedResponse = ses.list_verified_email_addresses()
    emailID= emailL
    if emailID not in verifiedResponse['VerifiedEmailAddresses']:
        verifyEmailResponse = ses.verify_email_identity(EmailAddress=emailID)
        return
    message = "Hi, Here is the list of {} restaurants I found that mights suit you: ".format(cuisine)
    message_restaurant = ""
    count = 1
    for restaurant in item:
        restName = restaurant['name']['S']
        restAddress = restaurant['address']['S']
        restZip = restaurant['zip_code']['S']
        revcount = restaurant['review_count']['N']
        rate = restaurant['rating']['N']
        message_restaurant += str(count)+". {} located at {}, {} with Ratings of {} and {} reviews. ".format(restName, restAddress, restZip, rate, revcount)
        message_restaurant += "\n"
        count += 1
    print(message_restaurant)
    # Send a mail to the user regarding the restaurant suggestions
    mailResponse = ses.send_email(
        Source=senderEmailId,
        Destination={'ToAddresses': [emailID]},
        Message={
            'Subject': {
                'Data': "Dining Conceirge Chatbot has a message for you!",
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': message+message_restaurant,
                    'Charset': 'UTF-8'
                },
                'Html': {
                    'Data': message+message_restaurant,
                    'Charset': 'UTF-8'
                }
            }
        }
    )