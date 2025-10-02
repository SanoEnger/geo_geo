from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from jose import JWTError, jwt  # ИСПРАВЛЕННЫЙ ИМПОРТ
from datetime import datetime, timedelta

app = FastAPI(
    title="Auth Service",
    description="Сервис аутентификации и авторизации",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Модели данных
class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Заглушка для базы данных
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Administrator",
        "hashed_password": "fakehashedpassword"
    }
}

def verify_password(plain_password, hashed_password):
    """Валидация пароля (заглушка)"""
    return plain_password == "password"  # В реальности использовать bcrypt

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:  # ИСПРАВЛЕННЫЙ EXCEPT
        raise credentials_exception
        
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/")
async def root():
    return {"message": "Auth Service работает!", "status": "success"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}

@app.post("/api/login")
async def login_for_access_token(username: str, password: str):
    user = authenticate_user(fake_users_db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/register")
async def register_user(username: str, email: str, password: str):
    if username in fake_users_db:
        raise HTTPException(400, "Username already registered")
    # В реальности здесь будет хэширование пароля и сохранение в БД
    return {"message": "User registered successfully", "username": username}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)