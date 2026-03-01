# Pi Cloud

A self-hosted private cloud platform built on a Raspberry Pi 5, featuring a custom web dashboard, media streaming, and enterprise-grade security features.

## Features

- Secure login with session-based authentication
- Brute-force protection via rate limiting (5 attempts/minute)
- HTTPS/SSL encryption
- Real-time system stats (CPU, RAM, Disk, Temperature)
- Authentication logging with IP tracking for intrusion detection
- Media library with movie poster support
- Music and photo library management
- Fully Dockerized with auto-restart
- Globally accessible via Tailscale VPN

## Tech Stack

- Backend: Python, Flask
- Frontend: HTML, CSS, JavaScript
- Container: Docker
- Media Server: Jellyfin
- Security: Flask-Limiter, HTTPS/SSL, python-dotenv
- Remote Access: Tailscale VPN
- Hardware: Raspberry Pi 5, Debian Linux

## Setup

1. Clone the repo
2. Copy .env.example to .env and fill in your credentials
3. Generate SSL certificates
4. Build and run with Docker

## Security

- All login attempts are logged with timestamps and IP addresses
- Rate limiting prevents brute force attacks
- HTTPS encrypts all traffic
- Credentials stored as environment variables, never hardcoded

## Author

Marc Bordelon - Computer Science, University of Louisiana at Lafayette
