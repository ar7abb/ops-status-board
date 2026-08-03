# Ops Status Board Architecture

> **Current status:** This document describes the planned architecture. The application, database, Nginx configuration, deployment, and cloud resources have not been implemented yet.

## Planned request path

```text
Browser or API client
        |
        v
      Nginx
        |
        v
  FastAPI application
        |
        v
    PostgreSQL
```

Nginx will receive HTTP requests on the deployed server and forward application requests to FastAPI. FastAPI will provide the API and application behavior. PostgreSQL will store persistent application data.

During early development, the client may connect directly to FastAPI. Nginx is introduced later when the application is deployed to the separate practice server.

## Planned environments

| Environment | Planned responsibility |
|---|---|
| Windows | Host WSL2, the browser, and terminal access |
| Ubuntu 24.04 under WSL2 | Develop, test, containerize, and automate the project |
| Separate Ubuntu server | Practise deployment, Nginx, operations, monitoring, backup, and recovery |
| AWS | Later adaptation of the proven local system after cost and safety gates pass |

## Planned delivery path

```text
Source code -> GitHub Actions -> container image -> GHCR -> deployment server
```

GitHub Actions will test the project and later publish a versioned container image to GitHub Container Registry (GHCR). The deployment server will pull and run that image. Cloud deployment is deferred until the local workflow is implemented and verified.

## Scope boundaries

- The core project is one FastAPI application and one PostgreSQL database managed with Docker Compose.
- Nginx is the planned server entry point; it is not the operating system or the server itself.
- Kubernetes, microservices, managed databases, and a JavaScript frontend are outside the core scope.
- Implementation evidence will be added only after each component is built and verified.
