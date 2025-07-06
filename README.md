## API Requests

### Get User by Email
```bash
curl -X GET "https://tkc4uoslof.execute-api.eu-west-1.amazonaws.com/dev/users?email=john.doe@example.com"
```

### Create User
```bash
curl -X POST "https://tkc4uoslof.execute-api.eu-west-1.amazonaws.com/dev/users/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com"
  }'
```
