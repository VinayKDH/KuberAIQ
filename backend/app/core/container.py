"""DI composition root — wires ports to adapters based on settings."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_service import AiService
from app.application.services.auth_service import AuthService
from app.application.services.billing_service import BillingService
from app.application.services.ca_service import CaService
from app.application.services.collection_service import CollectionService
from app.application.services.compliance_service import ComplianceService
from app.application.services.company_service import CompanyService
from app.application.services.customer_service import CustomerService
from app.application.services.dashboard_service import DashboardService
from app.application.services.invoice_service import InvoiceService
from app.application.services.gstr_report_service import GstrReportService
from app.application.services.payment_service import PaymentService
from app.application.services.product_service import ProductService
from app.application.services.quotation_service import QuotationService
from app.core.config import settings
from app.infrastructure.ai.graph.build import CopilotGraph
from app.infrastructure.ai.azure_openai_llm import AzureOpenAiLlm
from app.infrastructure.ai.mock_llm import MockLlm
from app.infrastructure.auth.entra_auth import EntraAuthProvider
from app.infrastructure.auth.google_auth import GoogleAuthProvider
from app.infrastructure.auth.mock_auth import MockAuthProvider
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.notifications.mock_notifier import MockNotifier
from app.infrastructure.notifications.whatsapp_notifier import WhatsAppNotifier
from app.infrastructure.pdf.reportlab_generator import ReportLabPdfGenerator
from app.infrastructure.storage.local_blob import LocalBlobStorage


def _uow_factory() -> Callable[[], SqlAlchemyUnitOfWork]:
    from app.infrastructure.db.session import AsyncSessionLocal

    def factory() -> SqlAlchemyUnitOfWork:
        session: AsyncSession = AsyncSessionLocal()
        return SqlAlchemyUnitOfWork(session)

    return factory


def _build_storage():
    if settings.use_mock_blob:
        return LocalBlobStorage()
    from app.infrastructure.storage.azure_blob import AzureBlobStorage

    return AzureBlobStorage()


@dataclass
class Container:
    uow_factory: Callable
    storage: object
    notifier: MockNotifier | WhatsAppNotifier
    pdf: ReportLabPdfGenerator
    auth_service: AuthService
    llm: MockLlm | AzureOpenAiLlm
    graph: CopilotGraph
    customer_service: CustomerService
    product_service: ProductService
    invoice_service: InvoiceService
    quotation_service: QuotationService
    gstr_report_service: GstrReportService
    payment_service: PaymentService
    collection_service: CollectionService
    dashboard_service: DashboardService
    compliance_service: ComplianceService
    company_service: CompanyService
    billing_service: BillingService
    ca_service: CaService
    ai_service: AiService


@lru_cache
def build_container() -> Container:
    uow = _uow_factory()
    storage = _build_storage()
    notifier = MockNotifier() if settings.use_mock_whatsapp else WhatsAppNotifier()
    pdf = ReportLabPdfGenerator()
    entra = EntraAuthProvider(uow) if not settings.use_mock_auth else MockAuthProvider()
    google = GoogleAuthProvider(uow) if not settings.use_mock_auth else None
    billing_service = BillingService(uow)
    ca_service = CaService(uow)
    auth_service = AuthService(uow, entra, google, billing_service)
    llm = MockLlm() if settings.use_mock_llm else AzureOpenAiLlm()
    graph = CopilotGraph(llm=llm)

    customer_service = CustomerService(uow, storage, pdf)
    product_service = ProductService(uow)
    invoice_service = InvoiceService(uow, storage, pdf, notifier)
    gstr_report_service = GstrReportService(uow)
    quotation_service = QuotationService(uow, storage, pdf, invoice_service)
    payment_service = PaymentService(uow)
    collection_service = CollectionService(uow, notifier)
    dashboard_service = DashboardService(uow)
    compliance_service = ComplianceService(uow, notifier)
    company_service = CompanyService(uow, billing_service)
    ai_service = AiService(
        graph=graph,
        customer_service=customer_service,
        invoice_service=invoice_service,
        collection_service=collection_service,
        dashboard_service=dashboard_service,
        product_service=product_service,
    )

    return Container(
        uow_factory=uow,
        storage=storage,
        notifier=notifier,
        pdf=pdf,
        auth_service=auth_service,
        llm=llm,
        graph=graph,
        customer_service=customer_service,
        product_service=product_service,
        invoice_service=invoice_service,
        quotation_service=quotation_service,
        gstr_report_service=gstr_report_service,
        payment_service=payment_service,
        collection_service=collection_service,
        dashboard_service=dashboard_service,
        compliance_service=compliance_service,
        company_service=company_service,
        billing_service=billing_service,
        ca_service=ca_service,
        ai_service=ai_service,
    )
