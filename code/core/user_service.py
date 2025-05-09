from fastapi import Depends, status
from asyncpg import Connection

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

    async def create_user(self, user: UserRequest) -> User:
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
        if user.email:
            existing_user = await self.db.fetchrow("SELECT * FROM users WHERE email = $1", user.email)
            if existing_user:
                raise Hack2mException(status_code=status.HTTP_400_BAD_REQUEST, message="User already exists")

        # Check if session_id already exists
        if user.session_id:
            existing_session = await self.db.fetchrow("SELECT * FROM users WHERE session_id = $1", user.session_id)
            if existing_session:
                raise Hack2mException(status_code=status.HTTP_400_BAD_REQUEST, message="Session already exists")

        # Insert the new user into the database
        new_user = await self.db.fetchrow(
            """
            INSERT INTO users (name, email, password, session_id)
            VALUES ($1, $2, $3, $4) RETURNING uuid, name, email, session_id
            """,
            user.name,
            user.email,
            user.password,
            user.session_id
        )
        if not new_user:
            raise Hack2mException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to create user"
            )
        return User(**new_user)

    async def find_user_by_email(self, email: str) -> User:
        """Finds a user by an email

        Args:
            email (str): the email to search

        Returns:
            User: the User object with the user if found else None
        """
        user = await self.db.fetchrow("SELECT * FROM users WHERE email = $1", email)
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

    async def link_session_to_user(self, session_id: str, user: UserRequest) -> None:
        """
        Link an anonymous session to a real user when they sign up.

        Args:
            session_id (str): The session ID to link
            user_id (UUID): The user ID to link to

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
        new_user = await self.find_user_by_email(user.email)
        if not new_user:
            # Link the anonymous user
            linked_user = await self.db.fetchrow(
                """
                UPDATE users
                SET email = $1, name = $2
                WHERE session_id = $3
                RETURNING uuid, name, email, session_id
                """,
                user.email,
                user.name,
                session_id
            )
            new_user = User(**linked_user)

        # Update all records in scores and history tables to use user_id instead of session_id
        await self.db.execute(
            """
            UPDATE scores
            SET user_id = $1, session_id = NULL
            WHERE session_id = $2
            """,
            new_user.uuid,
            session_id
        )

        await self.db.execute(
            """
            UPDATE history
            SET user_id = $1, session_id = NULL
            WHERE session_id = $2
            """,
            new_user.uuid,
            session_id
        )
