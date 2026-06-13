"""ORM models — import all so Alembic autogenerate sees metadata."""
from app.infrastructure.db.models.audit import AuditLogModel
from app.infrastructure.db.models.company import CompanyModel, InvoiceCounterModel
from app.infrastructure.db.models.ca_client_assignment import CaClientAssignmentModel
from app.infrastructure.db.models.compliance import CompanyComplianceStatusModel, ComplianceObligationModel
from app.infrastructure.db.models.customer import CustomerModel
from app.infrastructure.db.models.invoice import InvoiceItemModel, InvoiceModel
from app.infrastructure.db.models.payment import PaymentModel
from app.infrastructure.db.models.product import ProductModel
from app.infrastructure.db.models.quotation import QuotationItemModel, QuotationModel
from app.infrastructure.db.models.reminder import ReminderModel
from app.infrastructure.db.models.subscription import SubscriptionModel
from app.infrastructure.db.models.user import UserModel

__all__ = [
    "AuditLogModel",
    "CaClientAssignmentModel",
    "CompanyComplianceStatusModel",
    "ComplianceObligationModel",
    "CustomerModel",
    "InvoiceCounterModel",
    "InvoiceItemModel",
    "InvoiceModel",
    "PaymentModel",
    "ProductModel",
    "QuotationItemModel",
    "QuotationModel",
    "ReminderModel",
    "SubscriptionModel",
    "UserModel",
]
