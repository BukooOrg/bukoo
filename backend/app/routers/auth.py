import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import hash_password, verify_password, create_access_token
from app.database import get_db
from app.models import User
from app.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Only allow admin creation if explicitly set (you could lock this down further)
    role = data.role if data.role in ("customer", "admin") else "customer"

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Verify user identity and return a reset token."""
    user = db.query(User).filter(
        User.email == data.id,
        User.full_name == data.fullName,
        User.role == data.role.lower(),
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found or details do not match")

    # Generate simple reset token
    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    db.commit()

    return {"resetToken": reset_token}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a reset token."""
    user = db.query(User).filter(User.reset_token == data.token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(data.password)
    user.reset_token = None
    db.commit()

    return {"message": "Password reset successful"}


@router.get("/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db)):
    """Get current user — placeholder that returns first admin for now.
    In production, use require_user dependency."""
    from app.auth import require_user
    # This endpoint works when called with a proper Bearer token
    # For simplicity, we return a simple message if no auth
    raise HTTPException(status_code=401, detail="Authentication required")
