"""ORM models — import all so Alembic autogenerate sees metadata."""
from app.infrastructure.db.models.audit import AuditLogModel
from app.infrastructure.db.models.ai_session import AiSessionModel, AiSessionTurnModel
from app.infrastructure.db.models.ai_usage_log import AiUsageLogModel
from app.infrastructure.db.models.company import CompanyModel, InvoiceCounterModel
from app.infrastructure.db.models.ca_firm import CaFirmModel
from app.infrastructure.db.models.ca_client_assignment import CaClientAssignmentModel
from app.infrastructure.db.models.ca_client_task import CaClientTaskModel
from app.infrastructure.db.models.compliance import CompanyComplianceStatusModel, ComplianceObligationModel
from app.infrastructure.db.models.customer import CustomerModel
from app.infrastructure.db.models.expense import ExpenseModel
from app.infrastructure.db.models.invoice import InvoiceItemModel, InvoiceModel
from app.infrastructure.db.models.payment import PaymentModel
from app.infrastructure.db.models.product import ProductModel
from app.infrastructure.db.models.stock_movement import StockMovementModel
from app.infrastructure.db.models.quotation import QuotationItemModel, QuotationModel
from app.infrastructure.db.models.recurring_invoice import RecurringInvoiceTemplateModel
from app.infrastructure.db.models.reminder import ReminderModel
from app.infrastructure.db.models.staff_invitation import StaffInvitationModel
from app.infrastructure.db.models.subscription import SubscriptionModel
from app.infrastructure.db.models.user import UserModel

__all__ = [
    "AuditLogModel",
    "AiSessionModel",
    "AiSessionTurnModel",
    "AiUsageLogModel",
    "CaClientAssignmentModel",
    "CaClientTaskModel",
    "CaFirmModel",
    "ExpenseModel",
    "CompanyComplianceStatusModel",
    "ComplianceObligationModel",
    "CustomerModel",
    "InvoiceCounterModel",
    "InvoiceItemModel",
    "InvoiceModel",
    "PaymentModel",
    "ProductModel",
    "StockMovementModel",
    "QuotationItemModel",
    "QuotationModel",
    "RecurringInvoiceTemplateModel",
    "ReminderModel",
    "StaffInvitationModel",
    "SubscriptionModel",
    "UserModel",
]
