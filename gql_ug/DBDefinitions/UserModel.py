import sqlalchemy
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from .UUID import UUIDColumn, UUIDFKey
from .Base import BaseModel

class UserModel(BaseModel):
    """Spravuje data spojena s uzivatelem"""

    __tablename__ = "users"

    id = UUIDColumn()
    name = Column(String)
    surname = Column(String)

    @hybrid_property
    def fullname(self):
        return self.name + " " + self.surname

    email = Column(String)
    valid = Column(Boolean, default=True)
    startdate = Column(DateTime)
    enddate = Column(DateTime)

    memberships = relationship("MembershipModel", back_populates="user", foreign_keys="MembershipModel.user_id")
    roles = relationship("RoleModel", back_populates="user", foreign_keys="RoleModel.user_id")
    # groups = relationship("GroupModel", 
    #     secondary="join(MembershipModel, GroupModel, GroupModel.id==MembershipModel.group_id)",
    #     primaryjoin="UserModel.id==MembershipModel.user_id",
    #     secondaryjoin="GroupModel.id==MembershipModel.group_id",
    #     uselist=True,
    #     viewonly=True
    # )

    created = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    lastchange = Column(DateTime, server_default=sqlalchemy.sql.func.now())
    createdby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)
    changedby = UUIDFKey(nullable=True)#Column(ForeignKey("users.id"), index=True, nullable=True)


