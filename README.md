Add the following **after your existing Installation section**. You don't need to delete what you already have:

````markdown
## Run the API

Start the server with:

```bash
uvicorn main:app --reload
````

The API will run at:

[http://127.0.0.1:8000](http://127.0.0.1:8000)

## Swagger UI

Open the interactive API documentation at:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Swagger UI allows all CRUD operations to be tested using the **Try it out** button.

## API Endpoints

| Method | Endpoint      | Description                       |
| ------ | ------------- | --------------------------------- |
| GET    | `/`           | Returns API information           |
| GET    | `/health`     | Checks whether the API is running |
| GET    | `/tasks`      | Returns all tasks                 |
| GET    | `/tasks/{id}` | Returns a single task             |
| POST   | `/tasks`      | Creates a new task                |
| PUT    | `/tasks/{id}` | Updates an existing task          |
| DELETE | `/tasks/{id}` | Deletes a task                    |

## HTTP Status Codes

| Status Code | Meaning            |
| ----------- | ------------------ |
| 200         | Successful request |
| 201         | Task created       |
| 204         | Task deleted       |
| 400         | Invalid request    |
| 404         | Task not found     |

## Validation

The API validates incoming task data.

A missing or empty `title` returns a **400 Bad Request** response.

An unknown task ID returns a **404 Not Found** response.

## Example: Create a Task

```powershell
$body = '{"title":"Buy milk"}'
curl.exe -i -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d $body
```

Example response:

```json
{
  "id": 4,
  "title": "Buy milk",
  "done": false
}
```

The response status is **201 Created**.

## Data Storage

Tasks are stored in an **in-memory Python list**. No database is used for this assignment. Tasks are reset when the server restarts.

## Swagger Screenshot

![Swagger UI](screenshots/crud%20FastAPI.PNG)

## GitHub Repository

[https://github.com/Usman-4773/task-api](https://github.com/Usman-4773/task-api)

```

**Important:** the screenshot line assumes you have renamed your screenshot folder to `screenshots`.
```
