import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailService:
    """Email delivery helpers."""

    @staticmethod
    def send_email(
        subject,
        to_email,
        template_name,
        context=None,
        from_email=None,
        cc=None,
        bcc=None,
        attachments=None,
        fail_silently=False,
    ):
        if context is None:
            context = {}

        context.setdefault("site_name", "Starter API")
        context.setdefault("site_url", getattr(settings, "FRONTEND_URL", "http://localhost:3000"))

        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL

        if isinstance(to_email, str):
            to_email = [to_email]

        try:
            html_content = render_to_string(f"emails/{template_name}.html", context)
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email,
                cc=cc,
                bcc=bcc,
            )

            email.attach_alternative(html_content, "text/html")

            if attachments:
                for filename, content, mimetype in attachments:
                    email.attach(filename, content, mimetype)

            result = email.send(fail_silently=fail_silently)

            if result:
                logger.info(f'Email sent successfully to {", ".join(to_email)} - Subject: {subject}')
            else:
                logger.warning(f'Email sending returned 0 - To: {", ".join(to_email)}')

            return result

        except Exception as e:
            logger.error(f'Failed to send email to {", ".join(to_email)}: {str(e)}')
            if not fail_silently:
                raise
            return 0

    @staticmethod
    def send_welcome_email(user, docs_url=None):
        """
        Send welcome email to newly registered user.
        """
        context = {
            "user": user,
            "docs_url": docs_url or f"{settings.FRONTEND_URL}/docs",
        }

        return EmailService.send_email(
            subject="Welcome to Starter API!",
            to_email=user.email,
            template_name="welcome_email",
            context=context,
        )

    @staticmethod
    def send_password_reset_email(user, reset_token, expires_in="24 hours"):
        """
        Send password reset email with reset link.
        """
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        context = {
            "user": user,
            "reset_url": reset_url,
            "expires_in": expires_in,
        }

        return EmailService.send_email(
            subject="Password Reset Request",
            to_email=user.email,
            template_name="password_reset_email",
            context=context,
        )

    @staticmethod
    def send_verification_email(user, verification_token, expires_in="24 hours"):
        """
        Send email verification link.
        """
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

        context = {
            "user": user,
            "verification_url": verification_url,
            "expires_in": expires_in,
        }

        return EmailService.send_email(
            subject="Verify Your Email Address",
            to_email=user.email,
            template_name="email_verification",
            context=context,
        )

    @staticmethod
    def send_bulk_email(subject, template_name, recipients_context_list, from_email=None):
        """
        Send bulk emails with personalized context for each recipient.
        """
        total_sent = 0

        for recipient_data in recipients_context_list:
            email = recipient_data.get("email")
            context = recipient_data.get("context", {})

            try:
                sent = EmailService.send_email(
                    subject=subject,
                    to_email=email,
                    template_name=template_name,
                    context=context,
                    from_email=from_email,
                    fail_silently=True,
                )
                total_sent += sent
            except Exception as e:
                logger.error(f"Failed to send bulk email to {email}: {str(e)}")

        logger.info(f"Bulk email sent to {total_sent}/{len(recipients_context_list)} recipients")
        return total_sent
