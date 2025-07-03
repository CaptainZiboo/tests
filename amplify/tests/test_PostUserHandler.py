import pytest
import json
import boto3
import os
from moto import mock_dynamodb
from unittest.mock import patch
import uuid

# Set environment variables for the lambda
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@mock_dynamodb
class TestPostUserHandler:
    
    def setup_method(self):
        """Setup method called before each test - creates DynamoDB table"""
        # Create mock DynamoDB
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create users table
        self.table = self.dynamodb.create_table(
            TableName='users',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'email-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'email',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        # Wait for table to be created
        self.table.meta.client.get_waiter('table_exists').wait(TableName='users')

    def test_create_user_success(self):
        """Test POST /users - creates new user successfully"""
        # Arrange
        from PostUserHandler import handler  # Import will be available after implementation
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'email': 'test@example.com'})
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 201
        assert 'Access-Control-Allow-Origin' in response['headers']
        
        body = json.loads(response['body'])
        assert 'id' in body
        assert body['email'] == 'test@example.com'
        assert len(body['id']) == 36  # UUID length
        
        # Verify user was actually created in DynamoDB
        created_user = self.table.get_item(Key={'id': body['id']})
        assert 'Item' in created_user
        assert created_user['Item']['email'] == 'test@example.com'

    def test_create_user_missing_email(self):
        """Test POST /users - missing email field"""
        # Arrange
        from PostUserHandler import handler
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({})
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Email is required'

    def test_create_user_empty_email(self):
        """Test POST /users - empty email field"""
        # Arrange
        from PostUserHandler import handler
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'email': ''})
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Email is required'

    def test_create_user_invalid_email_format(self):
        """Test POST /users - invalid email format"""
        # Arrange
        from PostUserHandler import handler
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'email': 'invalid-email'})
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Invalid email format'

    def test_create_user_duplicate_email(self):
        """Test POST /users - email already exists"""
        # Arrange
        from PostUserHandler import handler
        
        # Create first user
        existing_user = {
            'id': str(uuid.uuid4()),
            'email': 'existing@example.com'
        }
        self.table.put_item(Item=existing_user)
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'email': 'existing@example.com'})
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert body['error'] == 'User with this email already exists'

    def test_create_user_invalid_json(self):
        """Test POST /users - invalid JSON body"""
        # Arrange
        from PostUserHandler import handler
        
        event = {
            'httpMethod': 'POST',
            'body': 'invalid json'
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Invalid JSON in request body'

    def test_create_user_no_body(self):
        """Test POST /users - no body provided"""
        # Arrange
        from PostUserHandler import handler
        
        event = {
            'httpMethod': 'POST'
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Request body is required'

    def test_create_user_additional_fields_ignored(self):
        """Test POST /users - additional fields are ignored"""
        # Arrange
        from PostUserHandler import handler
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'email': 'test@example.com',
                'name': 'Test User',
                'age': 30,
                'malicious_field': 'hack'
            })
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['email'] == 'test@example.com'
        assert 'name' not in body
        assert 'age' not in body
        assert 'malicious_field' not in body

    def test_unsupported_http_method(self):
        """Test unsupported HTTP method"""
        # Arrange
        from PostUserHandler import handler
        
        event = {
            'httpMethod': 'GET'
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 405
        body = json.loads(response['body'])
        assert body['error'] == 'Method not allowed'

    def test_cors_headers_present(self):
        """Test CORS headers are present in response"""
        # Arrange
        from PostUserHandler import handler
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'email': 'test@example.com'})
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'

    def test_database_error_handling(self):
        """Test database error handling"""
        # Arrange
        from PostUserHandler import handler
        
        # Delete the table to simulate database error
        self.table.delete()
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'email': 'test@example.com'})
        }
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['error'] == 'Database error'

    def test_general_exception_handling(self):
        """Test general exception handling"""
        # Arrange
        from PostUserHandler import handler
        
        event = {}  # Missing httpMethod to trigger exception
        
        # Act
        response = handler(event, {})
        
        # Assert
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['error'] == 'Internal server error'

    def test_uuid_generation(self):
        """Test that UUIDs are properly generated and unique"""
        # Arrange
        from PostUserHandler import handler
        
        event1 = {
            'httpMethod': 'POST',
            'body': json.dumps({'email': 'user1@example.com'})
        }
        
        event2 = {
            'httpMethod': 'POST',
            'body': json.dumps({'email': 'user2@example.com'})
        }
        
        # Act
        response1 = handler(event1, {})
        response2 = handler(event2, {})
        
        # Assert
        assert response1['statusCode'] == 201
        assert response2['statusCode'] == 201
        
        body1 = json.loads(response1['body'])
        body2 = json.loads(response2['body'])
        
        assert body1['id'] != body2['id']  # UUIDs should be unique
        assert len(body1['id']) == 36  # Standard UUID length
        assert len(body2['id']) == 36  # Standard UUID length

# Test fixtures
@pytest.fixture
def valid_create_user_event():
    return {
        'httpMethod': 'POST',
        'body': json.dumps({'email': 'test@example.com'})
    }

@pytest.fixture
def invalid_email_event():
    return {
        'httpMethod': 'POST',
        'body': json.dumps({'email': 'invalid-email'})
    }

@pytest.fixture
def missing_email_event():
    return {
        'httpMethod': 'POST',
        'body': json.dumps({})
    }