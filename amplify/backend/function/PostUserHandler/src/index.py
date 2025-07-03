import json
import boto3
import uuid
import re
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

def handler(event, context):
    """
    AWS Lambda handler for POST /users
    Creates a new user with email validation and duplicate checking
    """
    print('received event:')
    print(event)
    
    try:
        # Only allow POST method
        http_method = event.get('httpMethod')
        if http_method != 'POST':
            return {
                'statusCode': 405,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        return create_user(event)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Internal server error'})
        }

def create_user(event):
    """
    Create a new user with email validation and duplicate checking
    """
    try:
        # Check if body exists
        if 'body' not in event or event['body'] is None:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Request body is required'})
            }
        
        # Parse request body
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
        
        # Extract and validate email
        email = body.get('email')
        
        if not email or not email.strip():
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Email is required'})
            }
        
        # Clean email
        email = email.strip()
        
        # Validate email format
        if not is_valid_email(email):
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid email format'})
            }
        
        # Check if user with email already exists using GSI
        if user_exists_by_email(email):
            return {
                'statusCode': 409,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'User with this email already exists'})
            }
        
        # Create new user (only id and email fields)
        user_id = str(uuid.uuid4())
        user_data = {
            'id': user_id,
            'email': email
        }
        
        # Save to DynamoDB
        table.put_item(Item=user_data)
        
        return {
            'statusCode': 201,
            'headers': get_cors_headers(),
            'body': json.dumps(user_data)
        }
    
    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Database error'})
        }

def user_exists_by_email(email):
    """
    Check if a user with the given email already exists
    Uses GSI for efficient email lookup
    """
    try:
        # Query using GSI on email
        response = table.query(
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={':email': email}
        )
        
        return len(response.get('Items', [])) > 0
    
    except ClientError as e:
        print(f"Error checking user existence: {str(e)}")
        # Fallback to scan if GSI fails
        try:
            response = table.scan(
                FilterExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            return len(response.get('Items', [])) > 0
        except ClientError:
            # If both methods fail, assume user doesn't exist to allow creation
            return False

def is_valid_email(email):
    """
    Validate email format using regex
    """
    # Basic email validation regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def get_cors_headers():
    """
    Return CORS headers for web client compatibility
    """
    return {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    }