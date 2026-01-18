from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login_access_token():
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    return {"message": "Login endpoint placeholder"}
