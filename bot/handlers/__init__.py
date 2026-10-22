from aiogram import Router

from bot.handlers.funnel import router as router_funnel
from bot.handlers.payment import router as router_payment
from bot.handlers.registration import router as router_registration
from bot.handlers.start import router as router_start

router = Router()


router.include_router(router_start)
router.include_router(router_registration)
router.include_router(router_funnel)
router.include_router(router_payment)