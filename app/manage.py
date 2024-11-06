#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess
import socket
import atexit
import threading

def check_redis_running():
    """Check if Redis is running on localhost:6379."""
    try:
        with socket.create_connection(("localhost", 6379), timeout=2):
            print("Redis is already running.")
            return True
    except socket.error:
        return False

def start_redis():
    """Start Redis as a Docker container if it's not already running."""
    subprocess.run(["docker", "rm", "-f", "redis_container"], stderr=subprocess.DEVNULL)
    print("Starting Redis container...")
    subprocess.run([
        "docker", "run", "-d", "--name", "redis_container",
        "-p", "6379:6379", "redis:latest"
    ], check=True)

def check_celery_running():
    """Check if a Celery container is already running."""
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", "name=celery_worker"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        print("Celery is already running in a container.")
        return True
    return False

def build_image():
    """Build the Docker image if it doesn't already exist."""
    # Check if the image already exists
    result = subprocess.run(
        ["docker", "images", "-q", "myapp_image:latest"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        print("Docker image already exists. Skipping build.")
        return
    print("Building Docker image...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    dockerfile_path = os.path.join(project_root, "Dockerfile")
    # Build the image
    subprocess.run([
        "docker", "build", "-t", "myapp_image",
        "-f", dockerfile_path,
        project_root
    ], check=True)

def start_celery():
    """Start a Celery worker in a Docker container and attach logs in real-time."""
    subprocess.run(["docker", "rm", "-f", "celery_worker"], stderr=subprocess.DEVNULL)
    print("Starting Celery worker container in detached mode...")
    subprocess.run([
        "docker", "run", "-d", "--name", "celery_worker",
        "--link", "redis_container:redis",
        "-e", "CELERY_BROKER_URL=redis://redis:6379/0",
        "-e", "CELERY_RESULT_BACKEND=redis://redis:6379/0",
        "myapp_image",
        "/scripts/worker.sh"  # Override CMD to run worker.sh
    ], check=True)
    # Start a thread to follow the Celery logs in real-time
    threading.Thread(target=follow_celery_logs, daemon=True).start()

def follow_celery_logs():
    """Follow the logs of the Celery worker container in real-time."""
    subprocess.run(["docker", "logs", "-f", "celery_worker"])

def check_flower_running():
    """Check if a Flower container is already running."""
    result = subprocess.run(
        ["docker", "ps", "-q", "-f", "name=flower"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        print("Flower is already running in a container.")
        return True
    return False

def start_flower():
    """Start Flower in a Docker container."""
    subprocess.run(["docker", "rm", "-f", "flower"], stderr=subprocess.DEVNULL)
    print("Starting Flower container...")
    subprocess.run([
        "docker", "run", "-d", "--name", "flower",
        "--link", "redis_container:redis",
        "--link", "celery_worker",
        "-p", "5555:5555",  # Expose Flower's default port
        "-e", "CELERY_BROKER_URL=redis://redis:6379/0",
        "myapp_image",
        "/scripts/flower.sh"  # Override CMD to run flower.sh
    ], check=True)
    # Start a thread to follow the Flower logs in real-time
    threading.Thread(target=follow_flower_logs, daemon=True).start()

def follow_flower_logs():
    """Follow the logs of the Flower container in real-time."""
    subprocess.run(["docker", "logs", "-f", "flower"])

def stop_containers():
    """Stop and remove the Redis, Celery, and Flower containers."""
    print("Stopping Redis, Celery, and Flower containers...")
    subprocess.run(["docker", "stop", "redis_container", "celery_worker", "flower"],
                   stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "rm", "redis_container", "celery_worker", "flower"],
                   stderr=subprocess.DEVNULL)

# Register the stop_containers function to be called on program exit
atexit.register(stop_containers)

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms.settings')
    # Check for the custom -c flag to start Redis, Celery, and Flower
    if "-c" in sys.argv:
        sys.argv.remove("-c")  # Remove the flag so it doesn’t interfere with Django commands
        # Start Redis if not running
        if not check_redis_running():
            start_redis()
        else:
            print("Redis is already running.")
        # Build Docker image if necessary
        build_image()
        # Start Celery if not running
        if not check_celery_running():
            start_celery()
        else:
            print("Celery is already running in a container.")
        # Start Flower if not running
        if not check_flower_running():
            start_flower()
        else:
            print("Flower is already running in a container.")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available "
            "on your PYTHONPATH environment variable? Did you forget to "
            "activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
