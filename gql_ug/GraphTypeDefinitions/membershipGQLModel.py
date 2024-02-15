import datetime
import strawberry
import uuid
from typing import List, Optional, Union, Annotated
import gql_ug.GraphTypeDefinitions
from .BaseGQLModel import BaseGQLModel, IDType

# Imports resolver functions for various fields of the GraphQL model.
from ._GraphResolvers import (
    resolve_id,
    resolve_name,
    resolve_name_en,
    resolve_changedby,
    resolve_created,
    resolve_lastchange,
    resolve_createdby
)

# Function to retrieve the loader from the GraphQL context, used for fetching data.
def getLoader(info):
    return info.context["all"]

# Annotations for lazy loading of GraphQL models to prevent circular dependencies.
GroupGQLModel = Annotated["GroupGQLModel", strawberry.lazy(".groupGQLModel")]
UserGQLModel = Annotated["UserGQLModel", strawberry.lazy(".userGQLModel")]

# Defines a GraphQL model for a Membership entity, including its fields and resolvers.
@strawberry.federation.type(
    keys=["id"],
    description="""Entity representing a relation between an user and a group""",
)
class MembershipGQLModel(BaseGQLModel):
    # Class method to get the loader specific for memberships.
    @classmethod
    def getLoader(cls, info):
        return getLoader(info).memberships

    # Field resolvers for the Membership model.
    id = resolve_id
    changedby = resolve_changedby
    created = resolve_created
    lastchange = resolve_lastchange
    createdby = resolve_createdby

    # Async resolver for the user field, returning a UserGQLModel or None.
    @strawberry.field(description="""user""")
    async def user(self, info: strawberry.types.Info) -> Optional["UserGQLModel"]:
        # return self.user
        result = await gql_ug.GraphTypeDefinitions.UserGQLModel.resolve_reference(info=info, id=self.user_id)
        return result

    # Async resolver for the group field, returning a GroupGQLModel or None.
    @strawberry.field(description="""group""")
    async def group(self, info: strawberry.types.Info) -> Optional["GroupGQLModel"]:
        # return self.group
        result = await gql_ug.GraphTypeDefinitions.GroupGQLModel.resolve_reference(info=info, id=self.group_id)
        return result

    # Field for checking if the membership is still valid.
    @strawberry.field(description="""is the membership is still valid""")
    async def valid(self) -> Union[bool, None]:
        return self.valid

    # Field for the start date of the membership.
    @strawberry.field(description="""date when the membership begins""")
    async def startdate(self) -> Union[datetime.datetime, None]:
        return self.startdate

    # Field for the end date of the membership.
    @strawberry.field(description="""date when the membership ends""")
    async def enddate(self) -> Union[datetime.datetime, None]:
        return self.enddate

#####################################################################
#
# Special fields for query
#
#####################################################################
# Special fields for query filtering.
from .utils import createInputs
from dataclasses import dataclass
GroupInputWhereFilter = Annotated["GroupInputWhereFilter", strawberry.lazy(".groupGQLModel")]
UserInputWhereFilter = Annotated["UserInputWhereFilter", strawberry.lazy(".userGQLModel")]

# Dataclass for filtering memberships in queries.
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

# Mutation input model for updating a membership.
@strawberry.input
class MembershipUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime   
    valid: Optional[bool] = None
    startdate: Optional[datetime.datetime] = None
    enddate: Optional[datetime.datetime] = None

# Mutation input model for inserting a new membership.
@strawberry.input
class MembershipInsertGQLModel:
    user_id: IDType
    group_id: IDType
    id: Optional[uuid.UUID] = None
    valid: Optional[bool] = True
    startdate: Optional[datetime.datetime] = None
    enddate: Optional[datetime.datetime] = None

# GraphQL model for the result of a membership operation.
@strawberry.type
class MembershipResultGQLModel:
    id: IDType = None
    msg: str = None

    # Resolver for fetching the membership operation result.
    @strawberry.field(description="""Result of membership operation""")
    async def membership(self, info: strawberry.types.Info) -> Union[MembershipGQLModel, None]:
        result = await MembershipGQLModel.resolve_reference(info, self.id)
        return result

# Mutation for updating a membership.
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

# Mutation for inserting a new membership.
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
