from pydantic import BaseModel

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from jose import (
    JWTError,
    jwt,
)

from document_service.core.config import (
    settings,
)


# ==========================================================
# BEARER AUTH
# ==========================================================

bearer_scheme = HTTPBearer(
    auto_error=False
)


class AuthenticatedUser(
    BaseModel
):

    id: int

    username: str | None = None

    role: str


# ==========================================================
# CURRENT USER
# ==========================================================

def get_current_user(

    credentials: (
        HTTPAuthorizationCredentials
        | None
    ) = Depends(
        bearer_scheme
    ),

) -> AuthenticatedUser:

    credentials_exception = (
        HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Could not validate credentials"
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )
    )

    if credentials is None:

        raise credentials_exception

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[
                settings.ALGORITHM
            ],
        )

    except JWTError:

        raise credentials_exception

    user_id = payload.get(
        "sub"
    )

    role = payload.get(
        "role"
    )

    username = payload.get(
        "username"
    )

    if (
        user_id is None
        or role is None
    ):

        raise credentials_exception

    try:

        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError,
    ):

        raise credentials_exception

    return AuthenticatedUser(
        id=user_id,
        username=username,
        role=str(role),
    )


# ==========================================================
# ROLE CHECK
# ==========================================================

def require_roles(
    *allowed_roles: str,
):

    def checker(

        current_user: (
            AuthenticatedUser
        ) = Depends(
            get_current_user
        ),

    ) -> AuthenticatedUser:

        if (
            current_user.role
            not in allowed_roles
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "You do not have permission "
                    "to perform this action."
                ),
            )

        return current_user

    return checker


# from pydantic import BaseModel
#
# from fastapi import (
#     Depends,
#     HTTPException,
#     status,
# )
#
# from fastapi.security import (
#     OAuth2PasswordBearer,
# )
#
# from jose import (
#     JWTError,
#     jwt,
# )
#
# from document_service.core.config import (
#     settings,
# )
#
#
# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl=(
#         f"{settings.CATALOG_SERVICE_URL}"
#         "/auth/login"
#     )
# )
#
#
# class AuthenticatedUser(
#     BaseModel
# ):
#
#     id: int
#
#     username: str | None = None
#
#     role: str
#
#
# def get_current_user(
#     token: str = Depends(
#         oauth2_scheme
#     ),
# ) -> AuthenticatedUser:
#
#     credentials_exception = (
#         HTTPException(
#             status_code=(
#                 status.HTTP_401_UNAUTHORIZED
#             ),
#             detail=(
#                 "Could not validate credentials"
#             ),
#             headers={
#                 "WWW-Authenticate": "Bearer"
#             },
#         )
#     )
#
#     try:
#
#         payload = jwt.decode(
#             token,
#             settings.SECRET_KEY,
#             algorithms=[
#                 settings.ALGORITHM
#             ],
#         )
#
#     except JWTError:
#
#         raise credentials_exception
#
#     user_id = payload.get(
#         "sub"
#     )
#
#     role = payload.get(
#         "role"
#     )
#
#     username = payload.get(
#         "username"
#     )
#
#     if (
#         user_id is None
#         or role is None
#     ):
#
#         raise credentials_exception
#
#     try:
#
#         user_id = int(
#             user_id
#         )
#
#     except (
#         TypeError,
#         ValueError,
#     ):
#
#         raise credentials_exception
#
#     return AuthenticatedUser(
#         id=user_id,
#         username=username,
#         role=str(role),
#     )
#
#
# def require_roles(
#     *allowed_roles: str,
# ):
#
#     def checker(
#         current_user: (
#             AuthenticatedUser
#         ) = Depends(
#             get_current_user
#         ),
#     ) -> AuthenticatedUser:
#
#         if (
#             current_user.role
#             not in allowed_roles
#         ):
#
#             raise HTTPException(
#                 status_code=(
#                     status.HTTP_403_FORBIDDEN
#                 ),
#                 detail=(
#                     "You do not have permission "
#                     "to perform this action"
#                 ),
#             )
#
#         return current_user
#
#     return checker