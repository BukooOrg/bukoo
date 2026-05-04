"""
Auth routes:
- register
- verify email
- credential login
- Google OAuth login.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.auth_dto import RegisterCommand, VerifyEmailCommand
from app.application.use_cases.auth.login import LoginUseCase
from app.application.use_cases.auth.register_customer import RegisterCustomerUseCase
from app.application.use_cases.auth.verify_email import VerifyEmailUseCase
from app.presentation.dependencies.deps import (
    AccountRepo,
    CredentialStrategy,
    DbSession,
    EmailNotificationService,
    GoogleStrategy,
    PasswordHasher,
    TokenService,
    UserRepo,
    VerificationTokenRepo,
)
from app.presentation.schemas.auth_schema import (
    GoogleLoginRequest,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    operation_id="register",
)
async def register(
    body: RegisterRequest,
    db_session: DbSession,
    user_repo: UserRepo,
    verification_token_repo: VerificationTokenRepo,
    hasher: PasswordHasher,
    email_svc: EmailNotificationService,
) -> RegisterResponse:
    use_case = RegisterCustomerUseCase(
        db_session=db_session,
        user_repo=user_repo,
        verification_token_repo=verification_token_repo,
        hasher=hasher,
        email_svc=email_svc,
    )
    result = await use_case.execute(
        RegisterCommand(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            date_of_birth=body.date_of_birth,
        )
    )
    return RegisterResponse(
        id=result.id,
        email=result.email,
        full_name=result.full_name,
        status=result.status,
        created_at=result.created_at,
    )


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    operation_id="verifyEmail",
)
async def verify_email(
    body: VerifyEmailRequest,
    db_session: DbSession,
    user_repo: UserRepo,
    verification_token_repo: VerificationTokenRepo,
    account_repo: AccountRepo,
    hasher: PasswordHasher,
) -> VerifyEmailResponse:
    use_case = VerifyEmailUseCase(
        db_session=db_session,
        user_repo=user_repo,
        verification_token_repo=verification_token_repo,
        account_repo=account_repo,
        hasher=hasher,
    )
    result = await use_case.execute(VerifyEmailCommand(email=body.email, otp=body.otp))
    return VerifyEmailResponse(email=result.email, message=result.message)


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
