"""
Auth routes:
- register
- credential login
- Google OAuth login.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.auth_dto import RegisterCommand
from app.application.use_cases.auth.login import LoginUseCase
from app.application.use_cases.auth.register import RegisterUseCase
from app.presentation.dependencies.deps import (
    CredentialStrategy,
    DbSession,
    EmailNotificationService,
    GoogleStrategy,
    PasswordHasher,
    TokenService,
    UserRepo,
)
from app.presentation.schemas.auth_schema import (
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=TokenResponse, status_code=201, operation_id="register"
)
async def register(
    body: RegisterRequest,
    db_session: DbSession,
    user_repo: UserRepo,
    hasher: PasswordHasher,
    token_svc: TokenService,
    email_svc: EmailNotificationService,
) -> TokenResponse:
    use_case = RegisterUseCase(
        db_session=db_session,
        user_repo=user_repo,
        hasher=hasher,
        token_svc=token_svc,
        email_svc=email_svc,
    )
    result = await use_case.execute(
        RegisterCommand(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
    )
    return TokenResponse(access_token=result.access_token)


@router.post("/login", response_model=TokenResponse, operation_id="login")
async def login(
    body: LoginRequest,
    db_session: DbSession,
    strategy: CredentialStrategy,
    token_svc: TokenService,
) -> TokenResponse:
    use_case = LoginUseCase(
        db_session=db_session, strategy=strategy, token_svc=token_svc
    )
    result = await use_case.execute({"email": body.email, "password": body.password})
    return TokenResponse(access_token=result.access_token)


@router.post(
    "/login/google", response_model=TokenResponse, operation_id="loginWithGoogle"
)
async def google_login(
    body: GoogleLoginRequest,
    db_session: DbSession,
    strategy: GoogleStrategy,
    token_svc: TokenService,
) -> TokenResponse:
    use_case = LoginUseCase(
        db_session=db_session, strategy=strategy, token_svc=token_svc
    )
    result = await use_case.execute(
        {"code": body.code, "redirect_uri": body.redirect_uri or ""}
    )
    return TokenResponse(access_token=result.access_token)
