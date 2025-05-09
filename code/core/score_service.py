from asyncpg import Connection
from uuid import UUID
from typing import Optional
from fastapi import status

from error.exceptions import Hack2mException
from log.logger import get_logger

logger = get_logger("score")

class ScoreService:
    """
    Service to handle scoring operations for challenges.
    """

    def __init__(self, db: Connection):
        """Initialize the ScoreService with a database connection."""
        self.db = db

    async def get_challenge_score(
            self,
            challenge_id: UUID,
            user_id: Optional[UUID] = None,
            session_id: Optional[str] = None
    ) -> int:
        """
        Get the current score for a challenge.

        Args:
            challenge_id: The challenge ID
            user_id: The user ID (if logged in)
            session_id: The session ID (if anonymous)

        Returns:
            The current score for the challenge
        """
        if not user_id and not session_id:
            raise Hack2mException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Either user_id or session_id must be provided"
            )

        query = """
            SELECT score FROM scores
            WHERE challenge_id = $1
            AND (user_id = $2 OR session_id = $3)
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = await self.db.fetchrow(query, challenge_id, user_id, session_id)
        return result['score'] if result else None

    async def record_attempt(
            self,
            challenge_id: UUID,
            challenge_points: int,
            user_id: Optional[UUID] = None,
            session_id: Optional[str] = None
        ) -> int:
        """
        Record an attempt and update the score.

        Args:
            challenge_id: The challenge ID
            user_id: The user ID (if logged in)
            session_id: The session ID (if anonymous)

        Returns:
            The updated score
        """
        if not user_id and not session_id:
            raise Hack2mException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Either user_id or session_id must be provided"
            )

        # Get the challenge points
        challenge = await self.db.fetchrow(
            "SELECT points FROM challenges WHERE uuid = $1",
            challenge_id
        )
        if not challenge:
            raise Hack2mException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Challenge not found"
            )

        # Get current score
        current_score = await self.get_challenge_score(challenge_id, user_id, session_id) or challenge_points

        # If this is the first attempt, set score to challenge points
        if current_score == challenge_points:
            new_score = challenge_points
        else:
            # Subtract 1 point for each attempt
            if round(challenge_points/2) >= current_score:
                return current_score
            new_score = current_score - 1

        # Record the new score
        await self.db.execute(
            """
            INSERT INTO scores (user_id, session_id, challenge_id, score)
            VALUES ($1, $2, $3, $4)
            """,
            user_id,
            session_id,
            challenge_id,
            new_score
        )

        return new_score

    async def record_failed_flag_attempt(
            self,
            challenge_id: UUID,
            challenge_points: int,
            user_id: Optional[UUID] = None,
            session_id: Optional[str] = None
        ) -> int:
        """
        Record a failed flag attempt and update the score.

        Args:
            challenge_id: The challenge ID
            user_id: The user ID (if logged in)
            session_id: The session ID (if anonymous)

        Returns:
            The updated score
        """
        if not user_id and not session_id:
            raise Hack2mException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Either user_id or session_id must be provided"
            )

        # Get current score
        current_score = await self.get_challenge_score(challenge_id, user_id, session_id) or challenge_points
        if round(challenge_points/2) <= current_score:
            return current_score
        # Subtract 1 point for failed flag attempt
        new_score = current_score - 1

        # Record the new score
        await self.db.execute(
            """
            INSERT INTO scores (user_id, session_id, challenge_id, score)
            VALUES ($1, $2, $3, $4)
            """,
            user_id,
            session_id,
            challenge_id,
            new_score
        )

        return new_score

    async def record_completion(
            self,
            challenge_id: UUID,
            challenge_points: int,
            user_id: Optional[UUID] = None,
            session_id: Optional[str] = None
        ) -> int:
        """
        Record challenge completion and finalize the score.

        Args:
            challenge_id: The challenge ID
            user_id: The user ID (if logged in)
            session_id: The session ID (if anonymous)

        Returns:
            The final score
        """
        if not user_id and not session_id:
            raise Hack2mException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Either user_id or session_id must be provided"
            )

        # Get current score
        current_score = await self.get_challenge_score(challenge_id, user_id, session_id)
        if not current_score:
            logger.info(challenge_points)
            # Record the final score
            await self.db.execute(
                """
                INSERT INTO scores (user_id, session_id, challenge_id, score, is_final)
                VALUES ($1, $2, $3, $4, true)
                """,
                user_id,
                session_id,
                challenge_id,
                challenge_points
            )
        else:
            await self.db.execute(
                """
                UPDATE scores
                SET is_final = TRUE
                WHERE uuid = (
                    SELECT uuid
                    FROM scores
                    WHERE user_id = $1 OR session_id = $2
                    ORDER BY created_at DESC
                    LIMIT 1
                )
                """,
                user_id,
                session_id
            )

        return current_score

    async def get_status(self, user_id: UUID, session_id: str) -> list:
        """Get the status of a user or session.

        Args:
            user_id (UUID): The user ID
            session_id (str): The session ID

        Returns:
            dict: The status of the user or session
        """
        if not user_id and not session_id:
            raise Hack2mException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Either user_id or session_id must be provided"
            )

        query = """
            SELECT u.name, c.key, s.score, s.is_final
            FROM scores s
                JOIN users u ON s.user_id = u.uuid OR s.session_id = u.session_id
                JOIN challenges c ON s.challenge_id = c.uuid
            WHERE (s.user_id = $1 OR s.session_id = $2)
            ORDER BY s.created_at DESC
        """
        result = await self.db.fetch(query, user_id, session_id)
        return [dict(row) for row in result]

    async def get_leaderboard(self) -> list:
        """Get the leaderboard

        Returns:
            dict: the leaderboard
        """
        score = await self.db.fetch(
            """
            SELECT u.name name, SUM(s.score) score
            FROM scores s
                JOIN users u ON s.user_id = u.uuid OR s.session_id = u.session_id
            WHERE s.is_final = TRUE
            GROUP BY u.name
            ORDER BY SUM(s.score) DESC
            """,
        )
        current_score = [ {"name": row.get('name'), "score": row.get('score')} for row in score]
        return current_score
