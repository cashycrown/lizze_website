from django.contrib import admin, messages
from django.utils.html import format_html
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import path
from django.shortcuts import redirect
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'email', 'service', 'date',
        'paid', 'payment_verified', 'is_confirmed',
        'payment_proof_preview'
    )
    list_filter = ('service', 'paid', 'payment_verified', 'date')
    search_fields = ('name', 'email', 'reference')
    actions = ['mark_as_verified', 'resend_confirmation_email']
    readonly_fields = (
        'reference', 'created_at',
        'payment_proof_preview', 'verification_slip_preview',
        'send_email_button'  # Add custom button field
    )

    fields = (
        'name', 'email', 'service', 'date', 'custom_details',
        'fee', 'payment_method', 'paid', 'payment_verified',
        'payment_proof', 'payment_proof_preview',
        'verification_notes', 'verification_slip', 'verification_slip_preview',
        'reference', 'created_at', 'send_email_button',
    )

    def send_email_button(self, obj):
        if obj.id:
            return format_html(
                '<a class="button" style="padding:5px 10px; background:#28a745; color:white; border-radius:5px;" '
                'href="{}">📨 Send Confirmation Email</a>',
                f'?send_email=1'
            )
        return ""
    send_email_button.short_description = "Send Email"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)

        if 'send_email' in request.GET:
            if obj.paid and obj.payment_verified and obj.verification_slip:
                try:
                    message = render_to_string("emails/confirmation_email.html", {
                        'booking': obj,
                        'site_name': "Lashify Artistry",
                    })
                    email = EmailMessage(
                        subject="✅ Payment Verified - Lashify Artistry",
                        body=message,
                        from_email=None,
                        to=[obj.email],
                    )
                    email.content_subtype = "html"
                    email.attach_file(obj.verification_slip.path)
                    email.send(fail_silently=False)
                    self.message_user(request, f"Confirmation email sent to {obj.email}", messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"Error sending email: {e}", messages.ERROR)
            else:
                self.message_user(request, "Booking not eligible (check paid, verified, and slip).", messages.WARNING)
            return redirect(request.path)

        return super().change_view(request, object_id, form_url, extra_context)

    def is_confirmed(self, obj):
        return obj.paid and obj.payment_verified and obj.verification_slip
    is_confirmed.boolean = True
    is_confirmed.short_description = 'Confirmed'

    def payment_proof_preview(self, obj):
        if obj.payment_proof:
            return format_html('<img src="{}" style="max-height:150px; border:1px solid #ccc;" />', obj.payment_proof.url)
        return "No image"
    payment_proof_preview.short_description = 'Proof of Payment'

    def verification_slip_preview(self, obj):
        if obj.verification_slip:
            return format_html('<img src="{}" style="max-height:150px; border:1px solid #ccc;" />', obj.verification_slip.url)
        return "No slip"
    verification_slip_preview.short_description = 'Verification Slip'

    @admin.action(description="✅ Mark selected bookings as Verified")
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(payment_verified=True)
        self.message_user(request, f"{updated} bookings marked as verified.")

    @admin.action(description="📨 Resend confirmation email")
    def resend_confirmation_email(self, request, queryset):
        for booking in queryset:
            if booking.paid and booking.payment_verified and booking.verification_slip:
                try:
                    message = render_to_string("emails/confirmation_email.html", {
                        'booking': booking,
                        'site_name': "Lashify Artistry",
                    })
                    email = EmailMessage(
                        subject="✅ Payment Verified - Lashify Artistry",
                        body=message,
                        from_email=None,
                        to=[booking.email],
                    )
                    email.content_subtype = "html"
                    email.attach_file(booking.verification_slip.path)
                    email.send()
                    messages.success(request, f"Confirmation email sent to {booking.email}")
                except Exception as e:
                    messages.error(request, f"Failed for {booking.email}: {str(e)}")
            else:
                messages.warning(request, f"{booking.email} not eligible for confirmation email")
