"""DI composition root — wires ports to adapters based on settings."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_service import AiService
from app.application.services.collection_service import CollectionService
from app.application.services.customer_service import CustomerService
from app.application.services.dashboard_service import DashboardService
from app.application.services.invoice_service import InvoiceService
from app.application.services.payment_service import PaymentService
from app.core.config import settings
from app.infrastructure.ai.graph.build import CopilotGraph
from app.infrastructure.ai.mock_llm import MockLlm
from app.infrastructure.auth.mock_auth import MockAuthProvider
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.notifications.mock_notifier import MockNotifier
from app.infrastructure.pdf.reportlab_generator import ReportLabPdfGenerator
from app.infrastructure.storage.local_blob import LocalBlobStorage


def _uow_factory() -> Callable[[], SqlAlchemyUnitOfWork]:
    from app.infrastructure.db.session import AsyncSessionLocal

    def factory() -> SqlAlchemyUnitOfWork:
        session: AsyncSession = AsyncSessionLocal()
        return SqlAlchemyUnitOfWork(session)

    return factory


@dataclass
class Container:
    uow_factory: Callable
    storage: LocalBlobStorage
    notifier: MockNotifier
    pdf: ReportLabPdfGenerator
    auth: MockAuthProvider
    llm: MockLlm
    graph: CopilotGraph
    customer_service: CustomerService
    invoice_service: InvoiceService
    payment_service: PaymentService
    collection_service: CollectionService
    dashboard_service: DashboardService
    ai_service: AiService


@lru_cache
def build_container() -> Container:
    uow = _uow_factory()

    if settings.use_mock_blob:
        storage = LocalBlobStorage()
    else:
        storage = LocalBlobStorage()  # fallback until Azure adapter wired

    notifier = MockNotifier() if settings.use_mock_whatsapp else MockNotifier()
    pdf = ReportLabPdfGenerator()
    auth = MockAuthProvider()
    llm = MockLlm() if settings.use_mock_llm else MockLlm()
    graph = CopilotGraph(llm=llm)

    customer_service = CustomerService(uow)
    invoice_service = InvoiceService(uow, storage, pdf, notifier)
    payment_service = PaymentService(uow)
    collection_service = CollectionService(uow, notifier)
    dashboard_service = DashboardService(uow)
    ai_service = AiService(
        graph=graph,
        customer_service=customer_service,
        invoice_service=invoice_service,
        collection_service=collection_service,
        dashboard_service=dashboard_service,
    )

    return Container(
        uow_factory=uow,
        storage=storage,
        notifier=notifier,
        pdf=pdf,
        auth=auth,
        llm=llm,
        graph=graph,
        customer_service=customer_service,
        invoice_service=invoice_service,
        payment_service=payment_service,
        collection_service=collection_service,
        dashboard_service=dashboard_service,
        ai_service=ai_service,
    )
