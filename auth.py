# auth.py  ← FINAL VERSION – NO AUTH + NO ERRORS
from typing import Annotated
from fastapi import Depends

# Dummy Pydantic model (this is what fixes the crash)
from pydantic import BaseModel

class User(BaseModel):
    username: str = "public"

# Dummy dependency that returns the user
async def get_current_user():
    return User()

# Shortcut you can use everywhere
CurrentUser = Annotated[User, Depends(get_current_user)]