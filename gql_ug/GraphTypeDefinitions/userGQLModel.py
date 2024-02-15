import datetime
import strawberry
import asyncio
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

# Function to retrieve loader objects from GraphQL context, for data fetching.
def getLoader(info):
    return info.context["all"]

# Function to retrieve the current user object from GraphQL context.
def getUser(info):
    return info.context["user"]

# Annotations for lazy loading of GraphQL models to avoid circular dependencies.
MembershipGQLModel = Annotated["MembershipGQLModel", strawberry.lazy(".membershipGQLModel")]
RoleGQLModel = Annotated["RoleGQLModel", strawberry.lazy(".roleGQLModel")]
GroupGQLModel = Annotated["GroupGQLModel", strawberry.lazy(".groupGQLModel")]

# Import permission class for GDPR data access control.
from ..GraphPermissions import UserGDPRPermission

# Defines a GraphQL model for a user, including schema and data fetching logic.
@strawberry.federation.type(keys=["id"], description="""Entity representing a user""")
class UserGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info):
        # Retrieves the user-specific loader.
        return getLoader(info).users

    # Field resolvers for user properties.
    id = resolve_id
    name = resolve_name
    changedby = resolve_changedby
    created = resolve_created
    lastchange = resolve_lastchange
    createdby = resolve_createdby

    @strawberry.field(description="""User's family name (like Obama)""")
    def surname(self) -> str:
        # Directly returns the surname property of the user.
        return self.surname

    @strawberry.field(description="""User's email""")
    def email(self) -> Union[str, None]:
        # Directly returns the email property of the user.
        return self.email

    @strawberry.field(description="""User's validity (if their are member of institution)""")
    def valid(self) -> bool:
        # Directly returns the validity status of the user.
        return self.valid

    @strawberry.field(description="""GDPRInfo for permision test""", permission_classes=[UserGDPRPermission])
    def GDPRInfo(self, info: strawberry.types.Info) -> Union[str, None]:
        # Example GDPR info fetching logic, using permission classes for access control.
        actinguser = getUser(info)
        print(actinguser)
        return "GDPRInfo"

    @strawberry.field(description="""List of groups, where the user is member""")
    async def membership(
        self, info: strawberry.types.Info
    ) -> List["MembershipGQLModel"]:
        # Asynchronously fetches and returns memberships associated with the user.
        loader = getLoader(info).memberships
        result = await loader.filter_by(user_id=self.id)
        return list(result)

    @strawberry.field(description="""List of roles, which the user has""")
    async def roles(self, info: strawberry.types.Info) -> List["RoleGQLModel"]:
        # Asynchronously fetches and returns roles associated with the user.
        loader = getLoader(info).roles
        result = await loader.filter_by(user_id=self.id)
        return result

    @strawberry.field(
        description="""List of groups given type, where the user is member"""
    )
    async def member_of(
        self, grouptype_id: IDType, info: strawberry.types.Info
    ) -> List["GroupGQLModel"]:
        # Asynchronously fetches and returns groups of a specific type associated with the user.
        loader = getLoader(info).memberships
        rows = await loader.filter_by(user_id=self.id)# , grouptype_id=grouptype_id)
        results = (gql_ug.GraphTypeDefinitions.GroupGQLModel.resolve_reference(info, row.group_id) for row in rows)
        results = await asyncio.gather(*results)
        results = filter(lambda item: item.grouptype_id == grouptype_id, results)
        return results

#####################################################################
#
# Special fields for query
#
#####################################################################

from .utils import createInputs
from dataclasses import dataclass
#MembershipInputWhereFilter = Annotated["MembershipInputWhereFilter", strawberry.lazy(".membershipGQLModel")]
# Define input data structures for filtering users in queries.
@createInputs
@dataclass
class UserInputWhereFilter:
    # Defines fields for filtering user queries.
    name: str
    surname: str
    email: str
    fullname: str
    valid: bool
    from .membershipGQLModel import MembershipInputWhereFilter
    memberships: MembershipInputWhereFilter

# Define GraphQL fields for querying users, including pagination and filtering.
@strawberry.field(description="""Returns a list of users (paged)""")
async def user_page(
    self, info: strawberry.types.Info, skip: int = 0, limit: int = 10,
    where: Optional[UserInputWhereFilter] = None
) -> List[UserGQLModel]:
    # Asynchronously fetches and returns a paginated list of users, optionally filtered.
    wheredict = None if where is None else strawberry.asdict(where)
    loader = getLoader(info).users
    result = await loader.page(skip, limit, where=wheredict)
    return result

@strawberry.field(description="""Finds an user by their id""")
async def user_by_id(
    self, info: strawberry.types.Info, id: IDType
) -> Union[UserGQLModel, None]:
    # Asynchronously fetches and returns a user by their ID.
    result = await UserGQLModel.resolve_reference(info=info, id=id)
    return result

@strawberry.field(
    description="""Finds an user by letters in name and surname, letters should be atleast three"""
)
async def user_by_letters(
    self,
    info: strawberry.types.Info,
    validity: Union[bool, None] = None,
    letters: str = "",
) -> List[UserGQLModel]:
    # Asynchronously fetches and returns users based on substring search in name and surname, with optional validity filter.
    loader = getLoader(info).users

    if len(letters) < 3:
        return []
    stmt = loader.getSelectStatement()
    model = loader.getModel()
    stmt = stmt.where((model.name + " " + model.surname).like(f"%{letters}%"))
    if validity is not None:
        stmt = stmt.filter_by(valid=True)

    result = await loader.execute_select(stmt)
    return result

from gql_ug.GraphResolvers import UserByRoleTypeAndGroupStatement

@strawberry.field(description="""Finds users who plays in a group a roletype""")
async def users_by_group_and_role_type(
    self,
    info: strawberry.types.Info,
    group_id: IDType,
    role_type_id: IDType,
) -> List[UserGQLModel]:
    # result = await resolveUserByRoleTypeAndGroup(session,  group_id, role_type_id)
    loader = getLoader(info).users
    result = await loader.execute_select(UserByRoleTypeAndGroupStatement)
    return result


#####################################################################
#
# Mutation section
#
#####################################################################
import datetime

# Define GraphQL mutations for updating and inserting user data.
@strawberry.input
class UserUpdateGQLModel:
    # Input model for user updates.
    id: IDType
    lastchange: datetime.datetime  # razitko
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    valid: Optional[bool] = None

@strawberry.input
class UserInsertGQLModel:
    # Input model for inserting new users
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    valid: Optional[bool] = None

@strawberry.type
class UserResultGQLModel:
    # GraphQL model for the result of user operations.
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Result of user operation""")
    async def user(self, info: strawberry.types.Info) -> Union[UserGQLModel, None]:
        # Asynchronously fetches and returns the user associated with an operation result.
        result = await UserGQLModel.resolve_reference(info, self.id)
        return result

# Mutations for user updates and insertions, handling the operation logic and returning the result.
@strawberry.mutation
async def user_update(self, info: strawberry.types.Info, user: UserUpdateGQLModel) -> UserResultGQLModel:
    #print("user_update", flush=True)
    #print(user, flush=True)
    loader = getLoader(info).users
    
    updatedrow = await loader.update(user)
    #print("user_update", updatedrow, flush=True)
    result = UserResultGQLModel()
    result.id = user.id

    if updatedrow is None:
        result.msg = "fail"
    else:
        result.msg = "ok"
    print("user_update", result.msg, flush=True)
    return result

@strawberry.mutation
async def user_insert(self, info: strawberry.types.Info, user: UserInsertGQLModel) -> UserResultGQLModel:
    loader = getLoader(info).users
    
    row = await loader.insert(user)

    result = UserResultGQLModel()
    result.id = row.id
    result.msg = "ok"
    
    return result
