from aiogram import Router

from bot.handlers.funnel import router as router_funnel
from bot.handlers.payment import router as router_payment
from bot.handlers.registration import router as router_registration
from bot.handlers.start import router as router_start
from bot.handlers.admin import router as router_admin

router = Router()


router.include_router(router_start)
router.include_router(router_registration)
router.include_router(router_funnel)
router.include_router(router_payment)
router.include_router(router_admin)