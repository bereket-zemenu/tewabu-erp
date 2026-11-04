from aiogram import Dispatcher
from handlers.common import router as common_router
from handlers.new_design import router as new_design_router
from handlers.cost_calc import router as cost_calc_router
from handlers.simulator import router as simulator_router
from handlers.history import router as history_router
from handlers.orders import router as orders_router
from handlers.dashboard import router as dashboard_router
from handlers.reports import router as reports_router
from handlers.settings import router as settings_router

def setup_routers(dp: Dispatcher) -> None:
    """Register all modular handlers with the Dispatcher."""
    dp.include_router(common_router)
    dp.include_router(new_design_router)
    dp.include_router(cost_calc_router)
    dp.include_router(simulator_router)
    dp.include_router(history_router)
    dp.include_router(orders_router)
    dp.include_router(dashboard_router)
    dp.include_router(reports_router)
    dp.include_router(settings_router)

__all__ = ["setup_routers"]
