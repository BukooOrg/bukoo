from fastapi import FastAPI

from app.core.config import get_configs
from app.presentation.api import router

from .setup import AppFactory


def create_app() -> FastAPI:
    configs = get_configs()
    return AppFactory.create_application(router=router, configs=configs)


app = create_app()
