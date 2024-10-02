import json
import boto3
import csv
import uuid
import io
from decimal import Decimal

# Initialise the Clients
comprehend = boto3.client('comprehend')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Name of your DynamoDB Table
table_name = 'SentimentResults'

def lambda_handler(event, context):
    # Get the bucket name and the key (file path) from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    
    
    try:
        # Get the CSV file from S3
        s3_object = s3.get_object(Bucket=bucket_name, Key=object_key)
        
        # Read the CSV file content
        csv_content = s3_object['Body'].read()
        
        # Try decoding with different encodings
        try:
            csv_content = csv_content.decode('utf-8')  # Attempt UTF-8
            
        except UnicodeDecodeError:
            csv_content = csv_content.decode('ISO-8859-1')  # Fallback to ISO-8859-1
        
        # Parse the CSV content
        csv_reader = csv.reader(io.StringIO(csv_content))
        
        try:
            # Convert the CSV reader to a list
            csv_list = list(csv_reader)
            
            # Extract the the email body from the second value from the second row
            email = csv_list[1][2]
            
            # Extract the the email body from the second value from the second row
            email_id = csv_list[1][0]

            print(email)
            
            language_code = event.get('language_code', 'en')
            
            # Call the DetectSentiment API
            response = comprehend.detect_sentiment(
                Text=email,
                LanguageCode=language_code
            )
                   
            print("Full Sentiment Response: ", json.dumps(response, indent=2))
            
            # Extract Sentiment Results
            sentiment = response['Sentiment']
            sentiment_scores = response['SentimentScore']
            
            # Generate a User ID for the Item
            item_id = str(uuid.uuid4())
            
            # Store the Results in DynamoDB
            table = dynamodb.Table(table_name)
            table.put_item(
                Item={
                    'id': item_id,
                    'email_id': email_id,
                    'text': email,
                    'sentiment': sentiment,
                    'postive_sentiment': Decimal(str(sentiment_scores['Positive'])),
                    'negative_sentiment': Decimal(str(sentiment_scores['Negative'])),
                    'neutral_sentiment': Decimal(str(sentiment_scores['Neutral'])),
                    'mixed_sentiment': Decimal(str(sentiment_scores['Mixed']))
                }
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'Id': item_id,
                    'Email_id': email_id,
                    'Input': email,
                    'Sentiment': sentiment,
                    'SentimentScores': response['SentimentScore']
                })
            }
            
        except Exception as e:
            return f"Error: {e}"

            
    except Exception as e:
        return f"Error: {e}"
