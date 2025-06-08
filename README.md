# Django Celery Boilerplate

A production-ready Django application boilerplate with Celery for asynchronous task processing, containerized with Docker for easy development and deployment.

![Image](https://github.com/user-attachments/assets/95c3bd7f-d1fe-4b98-9bfa-05ded12c76bb)

## 🚀 Features

- **Django**: Web framework for rapid development
- **Celery**: Distributed task queue for background processing
- **Redis**: Message broker and result backend
- **PostgreSQL**: Production-ready database
- **Docker**: Containerized environment for consistency
- **Flower**: Web-based tool for monitoring Celery tasks
- **Gunicorn**: WSGI HTTP Server for production
- **Health Checks**: Built-in health monitoring
- **Makefile**: Simplified command execution

## 🏗️ Architecture


```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Django App    │────│    Redis     │────│   Celery    │
│   (Port 8000)   │    │ (Port 6379)  │    │   Worker    │
└─────────────────┘    └──────────────┘    └─────────────┘
         │                     │                   │
         │              ┌──────────────┐           │
         └──────────────│ PostgreSQL   │───────────┘
                        │              │
                        └──────────────┘
                               │
                      ┌──────────────────┐
                      │ Celery Beat      │
                      │ (Scheduler)      │
                      └──────────────────┘
                               │
                      ┌──────────────────┐
                      │ Flower Monitor   │
                      │ (Port 5555)      │
                      └──────────────────┘
```

## 📋 Prerequisites

- Docker & Docker Compose
- Make (optional, for using Makefile commands)

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/django-celery-boilerplate.git
cd django-celery-boilerplate
```


### 2. Environment Setup
Create a `.env` file in the project root:

```bash
cp .env.sample .env
```

### 3. Build and Run
Using Makefile `(recommended)`:

```
# Build Docker images
make build

# Start all services
make up

# View logs
make logs
```

Or using Docker Compose directly:

```
# Build images
docker-compose -f docker/docker-compose.yml build

# Start services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### 4. Access the Application

- **Django App:** `http://localhost:8000`
- **Flower (Celery Monitor):** `http://localhost:5555`
- **Health Check:** `http://localhost:8000/health/`

### 📁 Project Structure
```
django-celery-boilerplate/
├── app/                    # Django application code
│   ├── manage.py
│   ├── app/
│   │   ├── settings.py
│   │   ├── celery.py
│   │   └── wsgi.py
│   └── ...
├── docker/                 # Docker configuration
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example           # Environment variables template
├── .gitignore
├── Makefile              # Development commands
├── requirements.txt      # Python dependencies
├── requirements.dev.txt  # Development dependencies
└── README.md
```

### 🐳 Services

- **Django Application** (`app`)

- **Celery Worker** (`celery`)

- **Celery Beat** (`celery-beat`)

- **Flower** (`flower`)

- **Redis** (`redis`)

- **PostgreSQL** (`db`)

### Running Tests
```bash
# Using Make
make test

# Using Docker Compose
docker-compose -f docker/docker-compose.yml exec app python manage.py test
```

### Accessing Logs
```bash
# All services
make logs

# Specific service
docker-compose -f docker/docker-compose.yml logs -f app
docker-compose -f docker/docker-compose.yml logs -f celery
```

### 📊 Monitoring

#### Health Checks
- **Django:** `http://localhost:8000/health/`
- **Redis:** Built-in Redis ping
- **PostgreSQL:** Connection test every 5 seconds

#### Flower Dashboard
Access `http://localhost:5555` using username: `admin`, password: `admin` to monitor:

- Active tasks
- Task history
- Worker status
- Task statistics

**NOTE:** You change the flower auth credentials in the `docker/docker-compose.dev.yml` file


### 🚀 Production Deployment

1. Environment Variables: Ensure all production environment variables are set
2. Static Files: Run `make collectstatic`
3. Database: Run migrations with `make migrate`
4. SSL/TLS: Configure reverse proxy (`Nginx`) for HTTPS
5. Monitoring: Set up proper logging and monitoring solutions

### 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (git commit -m 'Add amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request

#### 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

# Author

## [`Abimbola Ronald`](https://www.linkedin.com/in/abimbola-ronald-977299224/)
