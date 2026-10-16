from typing import Dict, Any

class NotificationTemplates:
    """Formats customer notifications for WhatsApp delivery."""

    @classmethod
    def render_order_confirmation(cls, merchant_name: str, order_number: str, total_amount: float) -> str:
        return (
            f"✅ *{merchant_name} Order Confirmed!*\n\n"
            f"Your order *{order_number}* for *${total_amount:.2f}* has been successfully received.\n"
            "We are preparing your items now. Reply anytime to check your status."
        )

    @classmethod
    def render_order_status_update(cls, merchant_name: str, order_number: str, new_status: str) -> str:
        status_readable = new_status.replace("_", " ").title()
        return (
            f"📦 *{merchant_name} Order Update*\n\n"
            f"Order *{order_number}* is now *{status_readable}*."
        )

    @classmethod
    def render_order_cancelled(cls, merchant_name: str, order_number: str) -> str:
        return (
            f"❌ *{merchant_name} Order Cancelled*\n\n"
            f"Your order *{order_number}* has been cancelled as requested. Any applicable refund will be processed promptly."
        )

    @classmethod
    def render_appointment_confirmation(
        cls, merchant_name: str, service_name: str, date_str: str, time_str: str, booking_ref: str
    ) -> str:
        return (
            f"📅 *{merchant_name} Appointment Confirmed!*\n\n"
            f"Service: *{service_name}*\n"
            f"Date: *{date_str}*\n"
            f"Time: *{time_str}*\n"
            f"Booking Reference: *{booking_ref}*\n\n"
            "Please arrive 10 minutes early. To reschedule or cancel, reply to this chat."
        )

    @classmethod
    def render_appointment_reminder(
        cls, merchant_name: str, service_name: str, time_str: str, booking_ref: str
    ) -> str:
        return (
            f"⏰ *Reminder: Upcoming Appointment at {merchant_name}*\n\n"
            f"This is a friendly reminder for your *{service_name}* scheduled for *{time_str}*.\n"
            f"Reference: *{booking_ref}*.\n\n"
            "We look forward to seeing you!"
        )

    @classmethod
    def render_promotional_campaign(
        cls, merchant_name: str, title: str, details: str, opt_out_info: bool = True
    ) -> str:
        msg = f"🎉 *Exclusive Offer from {merchant_name}*\n\n*{title}*\n{details}\n"
        if opt_out_info:
            msg += "\n_Reply STOP to opt out of promotional updates._"
        return msg
