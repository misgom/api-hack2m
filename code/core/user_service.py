from asyncpg import Connection
from bcrypt import hashpw, gensalt, checkpw
from fastapi import status
from typing import Optional

from error.exceptions import Hack2mException
from log.logger import get_logger
from model.api.requests import UserRequest
from model.user import User


logger = get_logger("user_service")

class UserService:
    """
    User service class to handle user-related operations.
    """

    def __init__(self, db: Connection):
        """Initialize the UserService with a database connection."""
        self.db = db
        self.user_or_password_error = "User or password is incorrect"

    async def authenticate_user(
            self,
            name: Optional[str],
            password: str
        ) -> User:
        """Authenticate a user with the given credentials.
        This method checks if the user exists in the database and verifies the password.

        Args:
            name (Optional[str]): the name of the user to authenticate
            email (Optional[str]): the email of the user to authenticate
            password (str): the password of the user to authenticate
        Returns:
            User: the authenticated user object
        """
        if not name:
            logger.error("Name is required for authentication")
            raise Hack2mException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Name is required"
            )
        row = await self.db.fetchrow(
            """
            SELECT uuid, name, email, session_id, password FROM users
            WHERE name = $1
            """,
            name
        )
        logger.info(f"User {row} found in database")
        if not row:
            logger.error("User not found")
            raise Hack2mException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.user_or_password_error
            )
        user = User(**row)

        if not checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            logger.error("Invalid password")
            raise Hack2mException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message=self.user_or_password_error
            )
        logger.info(f"User {user.name} authenticated successfully")
        return user

    async def create_user(
            self,
            name: str,
            email: str,
            password: str,
            session_id: Optional[str] = None
        ) -> User:
        """
        Create a new user in the database.

        Args:
            user (UserRequest): The user data to create.

        Returns:
            User: The created user object.
        Raises:
            Hack2mException: If the user already exists or if there is an error during user creation.
        """
        # Check if the user already exists
        if email:
            existing_user = await self.db.fetchrow("SELECT * FROM users WHERE email = $1", email)
            if existing_user:
                raise Hack2mException(status_code=status.HTTP_400_BAD_REQUEST, message="User already exists")
        if name:
            existing_user = await self.db.fetchrow("SELECT * FROM users WHERE name = $1", name)
            if existing_user:
                raise Hack2mException(status_code=status.HTTP_400_BAD_REQUEST, message="User already exists")

        hashed_password = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

        # Insert the new user into the database
        new_user = await self.db.fetchrow(
            """
            INSERT INTO users (name, email, password, session_id)
            VALUES ($1, $2, $3, $4) RETURNING uuid, name, email, session_id
            """,
            name,
            email,
            hashed_password,
            session_id
        )
        if not new_user:
            raise Hack2mException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to create user"
            )
        return User(**new_user)

    async def create_anonymous_user(self, user: UserRequest) -> User:
        """Create an anonymous user in the database.

        Args:
            user (UserRequest): the user data to create.

        Returns:
            User: the created user object.
        """
        # Check if the user already exists
        existing_user = await self.db.fetchrow("SELECT * FROM users WHERE session_id = $1", user.session_id)
        if existing_user:
            return User(**existing_user)

        # Insert the new user into the database
        new_user = await self.db.fetchrow(
            """
            INSERT INTO users (name, session_id, is_anonymous)
            VALUES ($1, $2, true) RETURNING uuid, name, email, session_id, password, is_anonymous
            """,
            user.name,
            user.session_id
        )
        if not new_user:
            logger.error(f"Failed to create anonymous user {user.session_id}")
            raise Hack2mException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to create anonymous user"
            )
        return User(**new_user)

    async def find_user_by_name(self, name: str) -> User:
        """Finds a user by their name

        Args:
            name (str): the name to search

        Returns:
            User: the User object with the user if found else None
        """
        user = await self.db.fetchrow("SELECT uuid, name, email, session_id FROM users WHERE name = $1", name)
        logger.info(f"Retrieved user {user} for name {name}")
        if not user:
            return None
        return User(**user)

    async def find_user_by_email(self, email: str) -> User:
        """Finds a user by an email

        Args:
            email (str): the email to search

        Returns:
            User: the User object with the user if found else None
        """
        user = await self.db.fetchrow("SELECT uuid, name, email, session_id FROM users WHERE email = $1", email)
        logger.info(f"Retrieved user {user} for email {email}")
        if not user:
            return None
        return User(**user)

    async def find_user_by_session_id(self, session_id: str) -> User:
        """Finds a user by the session_id

        Args:
            session_id (str): the session_id of the user to find

        Returns:
            User: the User object if found, None otherwise
        """
        logger.info(f"Searching user by session {session_id}")
        user_session = await self.db.fetchrow(
            """
            SELECT * FROM users
            WHERE session_id = $1
            """,
            session_id)
        if not user_session:
            logger.info(f"User not found {session_id}")
            return None
        return User(**user_session)

    async def link_session_to_user(
            self,
            session_id: str,
            user: str,
            password: str
    ) -> None:
        """
        Link an anonymous session to a real user when they sign up.

        Args:
            session_id (str): The session ID to link
            user (str): The user name to link to
            password (str): The password of the user to link to

        Raises:
            Hack2mException: If the session or user doesn't exist
        """
        # Check if session exists
        logger.info(f"Searching user session {session_id} for linking account")
        session_user = await self.db.fetchrow("SELECT * FROM users WHERE session_id = $1", session_id)
        logger.info(session_user)
        if not session_user:
            logger.error(f"User with session_id {session_id} not found")
            raise Hack2mException(status_code=status.HTTP_404_NOT_FOUND, message="Session not found")

        # Check if user exists
        user_exists = await self.find_user_by_name(user)
        if user_exists:
            logger.error(f"Trying lo link an existent user {user}")
            raise Hack2mException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="User already exists"
            )
        hashed_password = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
        # Link the anonymous user
        linked_user = await self.db.fetchrow(
            """
            UPDATE users
            SET name = $1, password = $2, is_anonymous = false,
                updated_at = CURRENT_TIMESTAMP
            WHERE session_id = $3
            RETURNING uuid, name, email, session_id
            """,
            user,
            hashed_password,
            session_id
        )
        new_user = User(**linked_user)

        # Update all records in scores and history tables to use user_id instead of session_id
        await self.db.execute(
            """
            UPDATE scores
            SET user_id = $1, session_id = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = $2
            """,
            new_user.uuid,
            session_id
        )

        await self.db.execute(
            """
            UPDATE history
            SET user_id = $1, session_id = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = $2
            """,
            new_user.uuid,
            session_id
        )
