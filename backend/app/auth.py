from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db
from .security import verify_password, hash_password
from .user import User, UserRole, WorkerProfile, ClientProfile



router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterResponse(BaseModel):
    id: int
    email: str
    role: str



class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


async def authenticate_user(email: str, password: str, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user



@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),               # "worker" or "client"
    address: str = Form(...),
    face_photo: UploadFile = File(...),
    id_front_photo: UploadFile = File(...),
    id_rear_photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # Validate role
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Unique email/phone
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    result = await db.execute(select(User).where(User.phone == phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone already registered")

    # Create user
    user = User(
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role=user_role,
    )
    db.add(user)
    await db.flush()  # get user.id without full commit

    # Create profile
    if user_role == UserRole.worker:
        worker_profile = WorkerProfile(
            user_id=user.id,
            location=address,   # use location as address for now
            verified=False,
        )
        db.add(worker_profile)
    else:
        client_profile = ClientProfile(
            user_id=user.id,
            location=address,
        )
        db.add(client_profile)

    # Save files on disk: uploads/user_<id>/
    import os, shutil

    base_dir = os.path.join("uploads", f"user_{user.id}")
    os.makedirs(base_dir, exist_ok=True)

    def save_upload(upload: UploadFile, filename: str):
        path = os.path.join(base_dir, filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

    save_upload(face_photo, "face.jpg")
    save_upload(id_front_photo, "id_front.jpg")
    save_upload(id_rear_photo, "id_rear.jpg")

    await db.commit()
    return RegisterResponse(id=user.id, email=user.email, role=user.role.value)



@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # OAuth2PasswordRequestForm has fields: username, password
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(
        {"sub": str(user.id), "role": user.role.value}
    )
    return Token(access_token=access_token)



# ------- New dependencies below -------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )
    return current_user
