import os
import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


def send_password_reset_email(
    recipient_email: str,
    recipient_name: str,
    reset_url: str
):
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    from_name = os.getenv(
        "SENDGRID_FROM_NAME",
        "Learning Application"
    )

    if not api_key:
        raise ValueError("SENDGRID_API_KEY is not configured")

    if not from_email:
        raise ValueError("SENDGRID_FROM_EMAIL is not configured")

    subject = "Reset Your Password"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Reset Your Password</title>
    </head>

    <body style="
        margin: 0;
        padding: 0;
        background-color: #f5f7fb;
        font-family: Arial, sans-serif;
    ">

        <div style="
            max-width: 600px;
            margin: 40px auto;
            background: #ffffff;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        ">

            <h2 style="
                margin-top: 0;
                color: #212529;
            ">
                Reset Your Password
            </h2>

            <p style="color: #495057;">
                Hi {recipient_name},
            </p>

            <p style="color: #495057; line-height: 1.6;">
                We received a request to reset the password
                for your account.
            </p>

            <p style="color: #495057; line-height: 1.6;">
                Click the button below to create a new password.
                This link will expire in 30 minutes.
            </p>

            <div style="margin: 30px 0;">

                <a href="{reset_url}"
                   style="
                       display: inline-block;
                       padding: 12px 24px;
                       background-color: #0d6efd;
                       color: #ffffff;
                       text-decoration: none;
                       border-radius: 6px;
                       font-weight: bold;
                   ">
                    Reset Password
                </a>

            </div>

            <p style="
                color: #6c757d;
                font-size: 14px;
                line-height: 1.5;
            ">
                If you did not request a password reset,
                you can safely ignore this email.
            </p>

            <hr style="
                border: 0;
                border-top: 1px solid #dee2e6;
                margin: 30px 0;
            ">

            <p style="
                color: #adb5bd;
                font-size: 12px;
            ">
                This is an automated email. Please do not reply.
            </p>

        </div>

    </body>
    </html>
    """

    message = Mail(
        from_email=(from_email, from_name),
        to_emails=recipient_email,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(api_key)

        response = sg.send(message)

        logger.info(
            "Password reset email sent to %s. Status: %s",
            recipient_email,
            response.status_code
        )

        return True

    except Exception:
        logger.exception(
            "Failed to send password reset email to %s",
            recipient_email
        )

        return False