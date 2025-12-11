from celery import shared_task
import time


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