"""Subscription billing — payment required before company onboarding."""
from __future__ import annotations

import uuid
from datetime import timedelta

from app.application.ports.repositories import SubscriptionRecord, UserRecord
from app.core.datetime_utils import ensure_utc, utc_now
from app.core.config import settings
from app.core.constants import (
    SUBSCRIPTION_PERIOD_DAYS,
    SUBSCRIPTION_PLAN_STARTER,
    SUBSCRIPTION_STARTER_AMOUNT_PAISE,
)
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.domain.enums import SubscriptionStatus
from app.infrastructure.auth.token_service import TokenService
from app.infrastructure.billing.razorpay_client import RazorpayClient


class BillingService:
    def __init__(self, uow_factory, tokens: TokenService | None = None) -> None:
        self._uow_factory = uow_factory
        self._tokens = tokens or TokenService()

    async def ensure_subscription(self, user_id: uuid.UUID) -> SubscriptionRecord:
        async with self._uow_factory() as uow:
            existing = await uow.subscriptions.get_by_user_id(user_id)
            if existing:
                return existing
            record = SubscriptionRecord(
                id=uuid.uuid4(),
                user_id=user_id,
                status=SubscriptionStatus.PENDING,
                plan_code=SUBSCRIPTION_PLAN_STARTER,
                amount_paise=settings.subscription_plan_amount_paise,
            )
            created = await uow.subscriptions.create(record)
            await uow.commit()
            return created

    async def is_active(self, user_id: uuid.UUID) -> bool:
        sub = await self.ensure_subscription(user_id)
        return self._is_subscription_active(sub)

    @staticmethod
    def _is_subscription_active(sub: SubscriptionRecord) -> bool:
        if sub.status != SubscriptionStatus.ACTIVE:
            return False
        if sub.current_period_end and ensure_utc(sub.current_period_end) < utc_now():
            return False
        return True

    async def build_token_response(self, user: UserRecord) -> dict:
        sub = await self.ensure_subscription(user.id)
        return self._tokens.issue_tokens(user, subscription_active=self._is_subscription_active(sub))

    async def get_status(self, user_id: uuid.UUID) -> dict:
        sub = await self.ensure_subscription(user_id)
        active = self._is_subscription_active(sub)
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return {
            "subscription_status": sub.status.value,
            "subscription_active": active,
            "needs_payment": not active,
            "needs_onboarding": active and user.company_id is None,
            "plan_code": sub.plan_code,
            "amount_paise": sub.amount_paise,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        }

    async def create_checkout(self, user_id: uuid.UUID) -> dict:
        if settings.use_mock_billing:
            raise ForbiddenError("Use mock billing activation in development")

        sub = await self.ensure_subscription(user_id)
        if self._is_subscription_active(sub):
            raise ConflictError("Subscription is already active")

        client = RazorpayClient()
        order = await client.create_order(
            amount_paise=sub.amount_paise,
            receipt=f"sub-{user_id}",
            notes={"user_id": str(user_id), "plan": sub.plan_code},
        )
        sub.razorpay_order_id = order["id"]
        async with self._uow_factory() as uow:
            await uow.subscriptions.update(sub)
            await uow.commit()

        return {
            "key_id": settings.razorpay_key_id,
            "order_id": order["id"],
            "amount_paise": sub.amount_paise,
            "currency": "INR",
            "plan_code": sub.plan_code,
        }

    async def verify_payment(
        self,
        user_id: uuid.UUID,
        *,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> dict:
        if settings.use_mock_billing:
            raise ForbiddenError("Mock billing mode — use mock-activate endpoint")

        client = RazorpayClient()
        if not client.verify_payment_signature(
            order_id=order_id, payment_id=payment_id, signature=signature
        ):
            raise ValidationAppError("Invalid payment signature")

        return await self._activate(user_id, order_id=order_id, payment_id=payment_id)

    async def mock_activate(self, user_id: uuid.UUID) -> dict:
        if not settings.use_mock_billing:
            raise ForbiddenError("Mock billing is disabled in production")
        return await self._activate(user_id, order_id=None, payment_id=None)

    async def _activate(
        self,
        user_id: uuid.UUID,
        *,
        order_id: str | None,
        payment_id: str | None,
    ) -> dict:
        async with self._uow_factory() as uow:
            sub = await uow.subscriptions.get_by_user_id(user_id)
            if not sub:
                raise NotFoundError("Subscription not found")
            if order_id and sub.razorpay_order_id and sub.razorpay_order_id != order_id:
                raise ValidationAppError("Order does not match subscription")
            if self._is_subscription_active(sub):
                user = await uow.users.get_by_id(user_id)
                return self._tokens.issue_tokens(user, subscription_active=True)

            now = utc_now()
            sub.status = SubscriptionStatus.ACTIVE
            sub.paid_at = now
            sub.current_period_end = now + timedelta(days=SUBSCRIPTION_PERIOD_DAYS)
            if payment_id:
                sub.razorpay_payment_id = payment_id
            if order_id:
                sub.razorpay_order_id = order_id
            await uow.subscriptions.update(sub)
            user = await uow.users.get_by_id(user_id)
            await uow.commit()

        if not user:
            raise NotFoundError("User not found")
        return self._tokens.issue_tokens(user, subscription_active=True)

    async def handle_webhook(self, body: bytes, signature: str) -> None:
        if settings.use_mock_billing:
            return
        client = RazorpayClient()
        if not client.verify_webhook_signature(body, signature):
            raise ValidationAppError("Invalid webhook signature")

        import json

        payload = json.loads(body)
        event = payload.get("event")
        if event != "payment.captured":
            return
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = entity.get("order_id")
        payment_id = entity.get("id")
        if not order_id or not payment_id:
            return

        async with self._uow_factory() as uow:
            sub = await uow.subscriptions.get_by_order_id(order_id)
            if not sub or self._is_subscription_active(sub):
                return
        await self._activate(sub.user_id, order_id=order_id, payment_id=payment_id)
