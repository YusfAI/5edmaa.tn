from datetime import datetime, timedelta
from typing import Optional , List , Dict , Any 

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .auth_schemas import SimpleRegisterRequest
from .config import settings
from .database import get_db
from .security import verify_password, hash_password
from .user import User, UserRole, WorkerProfile, ClientProfile , VerificationStatus



router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class ClientMeResponse(BaseModel):
    id: int
    email: str
    phone: str
    role: str

    full_name: Optional[str] = None
    company_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

    verified: bool  # NEW


class WorkerMeResponse(BaseModel):
    # User info
    id: int
    email: str
    phone: str
    role: str  # "worker"

    # Profile info
    bio: Optional[str] = None
    categories: Optional[List[str]] = None
    hourly_rate: Optional[float] = None
    location: Optional[str] = None
    availability: Optional[Dict[str, Any]] = None
    portfolio_urls: Optional[List[str]] = None

    # Status flags
    verified: bool
    premium_until: Optional[datetime] = None
    rating: Optional[float] = None


class ClientProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None


class WorkerProfileUpdate(BaseModel):
    bio: Optional[str] = None
    categories: Optional[List[str]] = None
    hourly_rate: Optional[float] = None
    location: Optional[str] = None
    availability: Optional[Dict[str, object]] = None
    portfolio_urls: Optional[List[str]] = None

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



@router.post("/register/simple", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_simple(
    data: SimpleRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Simplified registration endpoint for JSON payloads (no file uploads)"""
    from .wallet import Wallet  # local import: wallet.py imports from .auth, avoid circular import

    # Validate role
    try:
        user_role = UserRole(data.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Check unique email/phone
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    result = await db.execute(select(User).where(User.phone == data.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone already registered")

    # Create user
    user = User(
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=user_role,
    )
    db.add(user)
    await db.flush()

    # Create profile
    if user_role == UserRole.worker:
        worker_profile = WorkerProfile(
            user_id=user.id,
            location=data.address,
            verified=False,
        )
        db.add(worker_profile)
    else:
        client_profile = ClientProfile(
            user_id=user.id,
            location=data.address,
        )
        db.add(client_profile)

    # Create wallet
    wallet = Wallet(user_id=user.id, balance=0.0)
    db.add(wallet)

    await db.commit()
    return RegisterResponse(id=user.id, email=user.email, role=user.role.value)


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
    from .wallet import Wallet  # local import: wallet.py imports from .auth, avoid circular import

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

    db.add(Wallet(user_id=user.id, balance=0.0))

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


async def get_verified_worker(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.worker:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workers only",
        )

    result = await db.execute(
        select(User)
        .options(selectinload(User.worker_profile))
        .where(User.id == current_user.id)
    )
    user = result.scalar_one()

    if (
        not user.worker_profile
        or user.worker_profile.status != VerificationStatus.approved
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Worker account not approved yet",
        )

    return user


async def get_verified_client(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clients only",
        )

    result = await db.execute(
        select(User)
        .options(selectinload(User.client_profile))
        .where(User.id == current_user.id)
    )
    user = result.scalar_one()

    if (
        not user.client_profile
        or user.client_profile.status != VerificationStatus.approved
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client account not approved yet",
        )

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



@router.put("/worker/profile", response_model=WorkerProfileUpdate)
async def update_worker_profile(
    data: WorkerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.worker:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can update worker profile",
        )

    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    if data.bio is not None:
        profile.bio = data.bio
    if data.categories is not None:
        profile.categories = data.categories
    if data.hourly_rate is not None:
        profile.hourly_rate = data.hourly_rate
    if data.location is not None:
        profile.location = data.location
    if data.availability is not None:
        profile.availability = data.availability
    if data.portfolio_urls is not None:
        profile.portfolio_urls = data.portfolio_urls

    # Editing a rejected profile resubmits it for review
    if profile.status == VerificationStatus.rejected:
        profile.status = VerificationStatus.pending
        profile.rejection_reason = None

    await db.commit()
    await db.refresh(profile)

    return WorkerProfileUpdate(
        bio=profile.bio,
        categories=profile.categories,
        hourly_rate=float(profile.hourly_rate) if profile.hourly_rate is not None else None,
        location=profile.location,
        availability=profile.availability,
        portfolio_urls=profile.portfolio_urls,
    )


@router.put("/client/profile", response_model=ClientProfileUpdate)
async def update_client_profile(
    data: ClientProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != UserRole.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can update client profile",
        )

    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Client profile not found")

    if data.full_name is not None:
        profile.full_name = data.full_name
    if data.company_name is not None:
        profile.company_name = data.company_name
    if data.bio is not None:
        profile.bio = data.bio
    if data.location is not None:
        profile.location = data.location

    # Editing a rejected profile resubmits it for review
    if profile.status == VerificationStatus.rejected:
        profile.status = VerificationStatus.pending
        profile.rejection_reason = None

    await db.commit()
    await db.refresh(profile)

    return ClientProfileUpdate(
        full_name=profile.full_name,
        company_name=profile.company_name,
        bio=profile.bio,
        location=profile.location,
    )


@router.get("/worker/me", response_model=WorkerMeResponse)
async def get_worker_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Only workers can call this
    if current_user.role != UserRole.worker:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workers can access this endpoint",
        )

    # Load worker profile
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    return WorkerMeResponse(
        id=current_user.id,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role.value,
        bio=profile.bio,
        categories=profile.categories,
        hourly_rate=float(profile.hourly_rate) if profile.hourly_rate is not None else None,
        location=profile.location,
        availability=profile.availability,
        portfolio_urls=profile.portfolio_urls,
        verified=profile.verified,
        premium_until=profile.premium_until,
        rating=float(profile.rating) if profile.rating is not None else None,
    )

@router.get("/client/me", response_model=ClientMeResponse)
async def get_client_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Only clients can call this
    if current_user.role != UserRole.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only clients can access this endpoint",
        )

    # Load client profile
    result = await db.execute(
        select(ClientProfile).where(ClientProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=404, detail="Client profile not found")

    return ClientMeResponse(
    	id=current_user.id,
    	email=current_user.email,
    	phone=current_user.phone,
    	role=current_user.role.value,
    	full_name=profile.full_name,
    	company_name=profile.company_name,
    	bio=profile.bio,
    	location=profile.location,
    	verified=profile.verified,  # NEW
)

class UserResponse(BaseModel):
    id: int
    email: str
    phone: str
    role: str

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role.value
    )
