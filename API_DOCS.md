# API Documentation

## Endpoints

### 1. GET /api/v1/resource
- **Description:** Retrieves a list of resources.
- **Response:** 200 OK with a JSON array of resources.

### 2. POST /api/v1/resource
- **Description:** Creates a new resource.
- **Request Body:** JSON object representing the resource.
- **Response:** 201 Created with the created resource.

### 3. GET /api/v1/resource/{id}
- **Description:** Retrieves a specific resource by ID.
- **Response:** 200 OK with the resource object.

### 4. PUT /api/v1/resource/{id}
- **Description:** Updates a specific resource by ID.
- **Request Body:** JSON object representing the updated resource.
- **Response:** 200 OK with the updated resource.

### 5. DELETE /api/v1/resource/{id}
- **Description:** Deletes a specific resource by ID.
- **Response:** 204 No Content.

## Authentication

- **Token:** All endpoints require a valid auth token in the header.