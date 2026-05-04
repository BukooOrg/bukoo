"""
Auth routes:
- register
- verify email
- credential login
- Google OAuth login.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.application.dtos.auth_dto import (
    RegisterCommand,
    ResendVerificationCommand,
    VerifyEmailCommand,
)
from app.application.use_cases.auth.login import LoginUseCase
from app.application.use_cases.auth.register_customer import RegisterCustomerUseCase
from app.application.use_cases.auth.resend_email_verification import (
    ResendEmailVerificationUseCase,
)
from app.application.use_cases.auth.verify_email import VerifyEmailUseCase
from app.core.util import set_auth_cookie
from app.presentation.dependencies.deps import (
    AccountRepo,
    CredentialAuthFactory,
    DbSession,
    EmailNotificationService,
    GoogleAuthFactory,
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
    ResendVerificationRequest,
    ResendVerificationResponse,
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


@router.post("/login", response_model=TokenResponse, operation_id="credentialLogin")
async def credential_login(
    body: LoginRequest,
    response: Response,
    db_session: DbSession,
    factory: CredentialAuthFactory,
    token_svc: TokenService,
) -> TokenResponse:
    use_case = LoginUseCase(db_session=db_session, factory=factory, token_svc=token_svc)
    result = await use_case.execute({"email": body.email, "password": body.password})
    set_auth_cookie(response, result.access_token)
    return TokenResponse(access_token=result.access_token)


@router.post(
    "/login/google", response_model=TokenResponse, operation_id="loginWithGoogle"
)
async def google_login(
    body: GoogleLoginRequest,
    response: Response,
    db_session: DbSession,
    factory: GoogleAuthFactory,
    token_svc: TokenService,
) -> TokenResponse:
    use_case = LoginUseCase(db_session=db_session, factory=factory, token_svc=token_svc)
    result = await use_case.execute(
        {"code": body.code, "redirect_uri": body.redirect_uri or ""}
    )
    set_auth_cookie(response, result.access_token)
    return TokenResponse(access_token=result.access_token)


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    operation_id="resendEmailVerification",
)
async def resend_verification(
    body: ResendVerificationRequest,
    db_session: DbSession,
    user_repo: UserRepo,
    verification_token_repo: VerificationTokenRepo,
    hasher: PasswordHasher,
    email_svc: EmailNotificationService,
) -> ResendVerificationResponse:
    use_case = ResendEmailVerificationUseCase(
        db_session=db_session,
        user_repo=user_repo,
        verification_token_repo=verification_token_repo,
        hasher=hasher,
        email_svc=email_svc,
    )
    result = await use_case.execute(ResendVerificationCommand(email=body.email))
    return ResendVerificationResponse(email=result.email, message=result.message)
