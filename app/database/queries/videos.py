import sqlite3

from app.database.connection import get_connection

VIDEO_FIELDS = {"title", "file_path"}


def create_patient_video(patient_id: int, data: dict) -> int:
    fields = {
        key: value
        for key, value in data.items()
        if key in VIDEO_FIELDS
    }

    file_path = str(data.get("file_path", "")).strip()
    if not file_path:
        raise ValueError("Video file path is required")
        
    columns = ["patient_id", *fields.keys()]
    placeholders = ", ".join("?" for _ in columns)

    

    with get_connection() as connection:
        try:
            cursor = connection.execute(
                f"""
                INSERT INTO patients_video ({", ".join(columns)})
                VALUES ({placeholders})
                """,
                [patient_id, *fields.values()],
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Patient does not exist for this video.") from exc

        return int(cursor.lastrowid)


def list_patient_videos(patient_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM patients_video
            WHERE patient_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (patient_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def update_patient_video_path(video_id: int, file_path: str) -> None:

    with get_connection() as connection:
        result = connection.execute(
            """
            UPDATE patients_video
            SET file_path =?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (file_path.strip(), video_id),
        )

        if result.rowcount == 0:
            raise ValueError("Video does not exist.")

