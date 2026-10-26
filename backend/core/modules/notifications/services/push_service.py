"""Committed review outbox -> exact active mobile installation -> Firebase."""
import logging
import re
import threading
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from api.models import CampusHubUser, Product, ProductApprovalPush, PushDeviceRegistration, SellerRequest

logger = logging.getLogger(__name__)
_app_lock = threading.Lock()


def queue_product_review(product):
    """One committed review decision per eligible device; rollback removes it."""
    if (not product.mobile_seller_id or product.is_archived or
            product.approval_status not in {Product.STATUS_APPROVED, Product.STATUS_REJECTED}):
        return
    devices = PushDeviceRegistration.objects.filter(
        user_id=product.mobile_seller_id, is_active=True, valid_until__gt=timezone.now())
    for device in devices:
        ProductApprovalPush.objects.get_or_create(
            product=product, device=device, approved_at=product.approved_at,
            decision=product.approval_status,
            defaults={"recipient_id": product.mobile_seller_id, "session_digest": device.session_digest})


def _firebase_app():
    import firebase_admin
    with _app_lock:
        try:
            app = firebase_admin.get_app("campushub-push")
        except ValueError:
            app = firebase_admin.initialize_app(options={
                "projectId": settings.CAMPUSHUB_FIREBASE_PROJECT_ID,
                "httpTimeout": 5,
            }, name="campushub-push")
        if app.project_id != settings.CAMPUSHUB_FIREBASE_PROJECT_ID:
            raise ValueError("Firebase project mismatch")
        return app


def send_to_installation(fid, *, product_id, delivery_id, recipient_id,
                         decision="approved", product_name="product"):
    """No credential in payload; FID uses the current Admin SDK targeting API."""
    from firebase_admin import messaging
    if decision not in {Product.STATUS_APPROVED, Product.STATUS_REJECTED}:
        raise ValueError("Unknown product review decision")
    message = messaging.Message(
        fid=fid,
        notification=messaging.Notification(
            title="Product Approved!" if decision == "approved" else "Product Rejected",
            body=f"Your {product_name[:150]} listing has been {decision}."),
        data={"type": f"product_{decision}", "product_id": str(product_id),
              "recipient_id": str(recipient_id), "delivery_id": str(delivery_id)},
        android=messaging.AndroidConfig(
            priority="high", ttl=timedelta(minutes=15),
            restricted_package_name="com.ustp.campushub",
            notification=messaging.AndroidNotification(
                tag=f"product-review-{product_id}", channel_id="campushub_approvals_v1",
                priority="high", default_sound=True, default_vibrate_timings=True,
                icon="ic_stat_campushub", color="#1A1851", visibility="private")),
    )
    return messaging.send(message, app=_firebase_app())


def dispatch_delivery(delivery_id):
    """Lock one delivery/device to serialize sends with reassignment/logout."""
    if not settings.CAMPUSHUB_FCM_ENABLED:
        return "disabled"
    with transaction.atomic():
        delivery = ProductApprovalPush.objects.select_for_update().filter(pk=delivery_id).first()
        if (delivery is None or delivery.status not in {"pending", "failed"} or
                delivery.attempts >= 3 or delivery.retry_at > timezone.now()):
            return "ignored"
        device = PushDeviceRegistration.objects.select_for_update().get(pk=delivery.device_id)
        product = Product.objects.filter(pk=delivery.product_id).first()
        application = SellerRequest.objects.filter(mobile_user_id=delivery.recipient_id).order_by(
            "-created_at", "-pk").first()
        eligible = (device.is_active and device.valid_until > timezone.now() and
                    device.user_id == delivery.recipient_id and
                    device.session_digest == delivery.session_digest and
                    CampusHubUser.objects.filter(pk=delivery.recipient_id,
                        is_active=True, is_suspended=False).exists() and
                    product is not None and product.mobile_seller_id == delivery.recipient_id and
                    not product.is_archived and product.approval_status == delivery.decision and
                    product.approved_at == delivery.approved_at and application is not None and
                    application.status == "approved" and not application.is_suspended)
        if not eligible:
            delivery.status, delivery.error_code = "skipped", "recipient_or_session_changed"
        else:
            delivery.attempts += 1
            try:
                send_to_installation(device.installation_id, product_id=product.pk,
                                     recipient_id=delivery.recipient_id, delivery_id=delivery.pk,
                                     decision=delivery.decision, product_name=product.name)
                delivery.status, delivery.error_code, delivery.sent_at = "sent", "", timezone.now()
            except Exception as error:
                from firebase_admin import messaging
                # Do not log exception text: SDK messages can contain device identifiers.
                code = str(getattr(error, "code", "send_failed"))
                delivery.error_code = code if re.fullmatch(r"[A-Za-z0-9_-]{1,80}", code) else "send_failed"
                delivery.status = "failed"
                delivery.retry_at = timezone.now() + timedelta(minutes=delivery.attempts * 5)
                if isinstance(error, messaging.UnregisteredError) or code == "UNREGISTERED":
                    device.is_active = False
                    device.save(update_fields=["is_active", "updated_at"])
                    delivery.status = "skipped"
                logger.warning("Product review push delivery %s failed (%s).", delivery.pk, type(error).__name__)
        delivery.save(update_fields=["status", "attempts", "error_code", "retry_at", "sent_at"])
        return delivery.status
