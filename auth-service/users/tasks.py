from celery import shared_task
import time
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def send_welcome_email(user_email):
    """
    Simulates sending a welcome email (heavy task).
    """
    print(f"--- Starting to send email to {user_email} ---")

    # Simulate network delay (e.g., connecting to SMTP server)
    time.sleep(5)

    print(f"--- Email sent successfully to {user_email} ---")
    return f"Email sent to {user_email}"

@shared_task
def generate_daily_report():
    """
    A periodic task to count total users.
    This will be scheduled by Celery Beat.
    """
    # Count total users in the database
    total_users = User.objects.count()

    print(f"--- DAILY REPORT: We have {total_users} registered users so far! ---")

    return f"Report generated. Total users: {total_users}"
