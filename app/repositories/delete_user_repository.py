from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis import AIAnalysis
from app.models.medical_record import MedicalRecord
from app.models.user import User


async def delete_user_and_related_data(
    db: AsyncSession,
    user: User,
) -> None:
    # 해당 회원이 생성한 AI 분석 데이터 삭제
    await db.execute(
        delete(AIAnalysis).where(
            AIAnalysis.created_by == user.id,
        )
    )

    # 해당 회원이 생성한 진료기록 삭제
    # 진료기록에 종속된 AI 분석은 FK CASCADE로 함께 삭제
    await db.execute(
        delete(MedicalRecord).where(
            MedicalRecord.created_by == user.id,
        )
    )

    # 회원 정보 삭제
    await db.delete(user)

    await db.flush()