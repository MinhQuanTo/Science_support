import datetime
import strawberry
import uuid
from typing import List, Optional, Union, Annotated
import gql_ug.GraphTypeDefinitions
from .BaseGQLModel import BaseGQLModel, IDType

from ._GraphResolvers import (
    resolve_id,
    resolve_name,
    resolve_name_en,
    resolve_changedby,
    resolve_created,
    resolve_lastchange,
    resolve_createdby
)

def getLoader(info):
    return info.context["all"]

GroupGQLModel = Annotated["GroupGQLModel", strawberry.lazy(".groupGQLModel")]
UserGQLModel = Annotated["UserGQLModel", strawberry.lazy(".userGQLModel")]

@strawberry.federation.type(
    keys=["id"],
    description="""Entity representing a relation between an user and a group""",
)
class MembershipGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info):
        return getLoader(info).memberships

    id = resolve_id
    changedby = resolve_changedby
    created = resolve_created
    lastchange = resolve_lastchange
    createdby = resolve_createdby

    @strawberry.field(description="""user""")
    async def user(self, info: strawberry.types.Info) -> Optional["UserGQLModel"]:
        # return self.user
        result = await gql_ug.GraphTypeDefinitions.UserGQLModel.resolve_reference(info=info, id=self.user_id)
        return result

    @strawberry.field(description="""group""")
    async def group(self, info: strawberry.types.Info) -> Optional["GroupGQLModel"]:
        # return self.group
        result = await gql_ug.GraphTypeDefinitions.GroupGQLModel.resolve_reference(info=info, id=self.group_id)
        return result

    @strawberry.field(description="""is the membership is still valid""")
    async def valid(self) -> Union[bool, None]:
        return self.valid

    @strawberry.field(description="""date when the membership begins""")
    async def startdate(self) -> Union[datetime.datetime, None]:
        return self.startdate

    @strawberry.field(description="""date when the membership ends""")
    async def enddate(self) -> Union[datetime.datetime, None]:
        return self.enddate

#####################################################################
#
# Special fields for query
#
#####################################################################
from .utils import createInputs
from dataclasses import dataclass
GroupInputWhereFilter = Annotated["GroupInputWhereFilter", strawberry.lazy(".groupGQLModel")]
UserInputWhereFilter = Annotated["UserInputWhereFilter", strawberry.lazy(".userGQLModel")]
@createInputs
@dataclass
class MembershipInputWhereFilter:
    valid: bool
    # from .userGQLModel import UserInputWhereFilter
    # from .groupGQLModel import GroupInputWhereFilter
    group: GroupInputWhereFilter
    user: UserInputWhereFilter

#####################################################################
#
# Mutation section
#
#####################################################################
import datetime

@strawberry.input
class MembershipUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime   
    valid: Optional[bool] = None
    startdate: Optional[datetime.datetime] = None
    enddate: Optional[datetime.datetime] = None

@strawberry.input
class MembershipInsertGQLModel:
    user_id: IDType
    group_id: IDType
    id: Optional[uuid.UUID] = None
    valid: Optional[bool] = True
    startdate: Optional[datetime.datetime] = None
    enddate: Optional[datetime.datetime] = None

@strawberry.type
class MembershipResultGQLModel:
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Result of membership operation""")
    async def membership(self, info: strawberry.types.Info) -> Union[MembershipGQLModel, None]:
        result = await MembershipGQLModel.resolve_reference(info, self.id)
        return result
    
@strawberry.mutation(description="""Update the membership, cannot update group / user""")
async def membership_update(self, 
    info: strawberry.types.Info, 
    membership: "MembershipUpdateGQLModel"
) -> "MembershipResultGQLModel":

    loader = getLoader(info).memberships
    updatedrow = await loader.update(membership)

    result = MembershipResultGQLModel()
    result.msg = "ok"
    result.id = membership.id

    if updatedrow is None:
        result.msg = "fail"
    
    return result


@strawberry.mutation(description="""Inserts new membership""")
async def membership_insert(self, 
    info: strawberry.types.Info, 
    membership: "MembershipInsertGQLModel"
) -> "MembershipResultGQLModel":

    loader = getLoader(info).memberships
    row = await loader.insert(membership)

    result = MembershipResultGQLModel()
    result.msg = "ok"
    result.id = row.id
    
    return result