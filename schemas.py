from pydantic import ConfigDict, Field, BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=120)

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    username: str | None = Field(default = None, min_length=3, max_length=50)
    email: EmailStr | None = Field(default = None, max_length=120)
    image_file: str | None = Field(default=None, max_length=200)

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    id: int
    image_file: str | None
    image_path: str

class UserPrivate(UserPublic):
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TagCreate(BaseModel):
    tagname: str = Field(min_length=1, max_length=50)

class TagResponse(TagCreate):
    model_config = ConfigDict(from_attributes=True)
    id:int


class NoteBase(BaseModel):
    heading: str = Field(min_length=3, max_length=50)
    body: str = Field(min_length=3)

class NoteCreate(NoteBase):
    tags: list[str] = Field(default=[])

class NoteResponse(NoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date_created: datetime

    author: UserPublic
    tags: list[TagResponse]

class NoteUpdate(BaseModel):
    heading: str | None = Field(default=None, min_length=3, max_length=50)
    body: str | None = Field(default=None, min_length=3)