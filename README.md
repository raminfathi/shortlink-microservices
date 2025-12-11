# ShortLink Microservices 🚀

A high-performance, scalable, and production-ready URL shortener system built with a **Microservices Architecture**.

This project demonstrates advanced backend concepts including **Asynchronous Communication**, **Event-Driven Design**, **Background Processing**, **Distributed Tracing**, and **Real-time Monitoring**.

---

## 🏗️ Architecture

The system is composed of multiple isolated services orchestrated via Docker Compose:

1. **Core API (FastAPI):**
   * Handles high-throughput HTTP requests.
   * Manages URL redirection (using Redis Strings for speed).
   * Publishes events to Redis Streams (Producer).
   * Serves static files (QR Codes) via Nginx.

2. **Auth Service (Django + DRF):**
   * Manages User Registration and Authentication.
   * Issues **JWT** tokens (verified by Core API via Shared Secret).
   * Uses **PostgreSQL** for persistent user data.

3. **Worker (Python Asyncio):**
   * Consumes events from Redis Streams.
   * Generates QR Codes.
   * Updates Analytics (Hash, Sorted Set Leaderboard, TimeSeries, HyperLogLog).
   * Uses **Bloom Filter** to prevent cache penetration.

4. **Celery Worker & Beat:**
   * Handles heavy background tasks (e.g., Sending Emails).
   * Schedules periodic tasks (e.g., Daily Reports).

5. **Infrastructure & Monitoring:**
   * **Nginx:** Reverse Proxy & API Gateway (HTTPS).
   * **Redis Stack:** Primary DB, Cache, Message Broker.
   * **Prometheus & Grafana:** Real-time metrics dashboard.
   * **Jaeger:** Distributed Tracing.

---

## 🛠️ Tech Stack

* **Languages:** Python 3.11
* **Web Frameworks:** FastAPI, Django REST Framework
* **Databases:** Redis Stack (TimeSeries, BloomFilter, Search), PostgreSQL
* **Async & Queues:** Redis Streams, Celery
* **DevOps:** Docker, Docker Compose, GitHub Actions (CI)
* **Monitoring:** Prometheus, Grafana, cAdvisor, Jaeger, OpenTelemetry

---

## 🚀 Quick Start

### Prerequisites

* Docker & Docker Compose
* Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/raminfathi/shortlink-microservices.git](https://github.com/raminfathi/shortlink-microservices.git)
   cd shortlink-microservices
   ```

2. **Setup Environment Variables:**
   Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
   *(Edit `.env` if you want to change default passwords).*

3. **Generate SSL Certificates (for Nginx HTTPS):**
   Run the following command in your terminal (Git Bash on Windows):
   ```bash
   mkdir -p nginx/certs
   MSYS_NO_PATHCONV=1 openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout nginx/certs/server.key \
     -out nginx/certs/server.crt \
     -subj "/C=IR/ST=Tehran/L=Tehran/O=ShortLink/OU=IT/CN=localhost"
   ```

4. **Build and Run:**
   ```bash
   docker-compose up --build -d
   ```

5. **Initialize Database (First time only):**
   Run the migrations for the Django Auth Service:
   ```bash
   docker-compose run --rm auth-service python manage.py migrate
   ```

---

## 📡 API Endpoints

Access the system at **`https://localhost`** (Self-signed certificate). Accept the browser warning to proceed.

| Service | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | POST | `/api/auth/register/` | Register a new user |
| **Auth** | POST | `/api/auth/login/` | Get JWT tokens |
| **Core** | POST | `/links` | Create a short link (Requires Auth) |
| **Core** | GET | `/{short_id}` | Redirect to original URL |
| **Core** | GET | `/{short_id}/stats` | Get link statistics & QR Code |
| **Core** | GET | `/stats/top` | Get global leaderboard |
| **Core** | GET | `/{short_id}/stats/history` | Get click history chart |

---

## 📊 Dashboards & Tools

* **Grafana:** `https://localhost/grafana/`
  * Default User: `admin`
  * Default Password: See `GRAFANA_PASSWORD` in `.env` (default: `admin`)
* **Jaeger Tracing:** `http://localhost:16686`
* **Prometheus:** `http://localhost:9090`
* **RedisInsight:** `http://localhost:8002`

---

## 🧪 Running Tests

To run the integration tests inside the containers:

```bash
# Core API Integration Tests
docker-compose exec core-api pytest

# Auth Service Tests
docker-compose run --rm auth-service pytest
```