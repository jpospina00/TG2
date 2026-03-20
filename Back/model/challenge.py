from sqlmodel import Field, SQLModel


class ChallengeBase(SQLModel):
    module_id: int = Field(foreign_key="module.id")
    level: str
    type: str
    agent_profile: str
    context: str
    opening_message: str


class Challenge(ChallengeBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ChallengeCreate(ChallengeBase):
    pass


class ChallengeRead(ChallengeBase):
    id: int


class ChallengeUpdate(SQLModel):
    agent_profile: str | None = None
    context: str | None = None
    opening_message: str | None = None