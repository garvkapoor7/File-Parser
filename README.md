
# File Upload & Parsing Progress - Local Setup

This project provides a FastAPI backend and a simple HTML frontend for uploading files and tracking parsing progress in real-time.

## Prerequisites

- Python 3.7+
- Node.js & npm (for serving frontend with a simple HTTP server, e.g., `http-server`)
- Git (optional, for cloning repo)


## Setup Instructions

### 1. Clone the repository

### 2. Backend Setup
    
  - Create and activate a Python virtual environment:
    $python -m venv venv
    
    $.\venv\Scripts\activate
  - Install backend dependencies:
    $pip install -r requirements.txt

  - Start FastAPI backend: (Remember proper file path..  check by executing dir and see where is     your "app" folder)
  - 
    $uvicorn app.main:app --host 0.0.0.0 --port 8000

   - Backend will start on:
     ( "http://localhost:8000" )


### 3. Frontend Setup

- Served my frontend files using any static HTTP server, recommended:

- Install `http-server`:

  ```
  npm install -g http-server
  ```

- Navigate to the folder containing my frontend HTML file.

- Run the server:

  ```
  python -m http.server 8080
  ```

- Open the frontend page in your browser:
  ("http://localhost:8080/app/real.html")




### 4. Connecting Frontend and Backend

- The frontend is configured to send file uploads and connect via WebSocket to the backend on:
 ("http://localhost:8000", "ws://localhost:8000" )

- My frontend js uses these url to communicate with the backend

### 5. Testing

- Upload a file using the frontend UI.

- Observe the progress bar for parsing updates in real time.

- Backend stores files and simulates processing progress.


### 6. CORS Configuration

- The backend FastAPI app includes CORS middleware allowing requests from:
 ("http://localhost:8080")


### Notes

- This setup is for local development and testing only.

- For production, consider HTTPS, persistent storage, and cloud hosting.



### ADDITIONAL

- Deployment of Azure with Docker
  The backend FastAPI application uses containers (Docker) that bundles all the dependencies and   configuration files to allow easy deployment.

- What I have done using Docker and Azure:
  Built a Docker image of the FastAPI back.

  Pushed Docker image to a container registry (Azure Container Registry or Docker Hub).

  Pushed the container backend to Azure Container Instances.

  Associated the container instance with a public IP address to open the backend API to the        internet.

  Allowed the access to the backend to the assigned public IP to test and enable its use           remotely.

**--This method of deployment makes it easier to host in the cloud in that it offers easily scalable, isolated application environments with little overheard of management.**
