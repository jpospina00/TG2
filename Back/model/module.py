from sqlmodel import Field, SQLModel


class ModuleBase(SQLModel):
    name: str


class Module(ModuleBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ModuleRead(ModuleBase):
    id: int