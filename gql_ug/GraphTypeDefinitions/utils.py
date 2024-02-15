import typing
import sys
import strawberry
from dataclasses import dataclass
import datetime
import logging

# Initialize a global dictionary to map Python types to GraphQL input types for filtering
inputTypeGQLMapper = {}

# Decorator function to create GraphQL input types for filtering based on class annotations
def createInputs(cls):
    # Extract class name to use in defining new GraphQL types
    clsname = cls.__name__
    print(f"GQL definitions for {clsname}")
    #whereName = clsname + "_where"

    # Define names for the dynamically generated input types for logical operations
    whereName = clsname
    orName = clsname + "_or"
    andName = clsname + "_and"

    # Extract field names and their types from the class for generating filter inputs
    fieldNames = [field_name for field_name in cls.__annotations__]
    opNames = [clsname + "_" + field_name for field_name in fieldNames]
    types = [field for field in cls.__annotations__.values()]

    # Helper function to generate custom input types for each field, supporting various operations
    def createCustomInput(field, name, baseType = str):
        result = inputTypeGQLMapper.get(baseType, None)
        if result is None:
            print(30*"#")
            print(f"New GQL type for {baseType.__name__}")
            if (baseType.__name__ == typing.Annotated.__name__):
                print(30*"#", "Annotated")
                return baseType
            logging.info(f"New GQL type for {baseType}")
            print(f"New GQL type for {baseType}")
            result = type(name, (object,), {})
            result.__annotations__ = {
                op: typing.Optional[baseType] for op in ["_eq", "_le", "_lt", "_ge", "_gt"]
            }
            for op in ["_eq", "_le", "_lt", "_ge", "_gt"]:
                setattr(result, op, strawberry.field(name=op, description="operation for select.filter() method", default=None))           
            result = strawberry.input(result, description=f"Expression on attribute '{field}'. Only one constrain allowed.")
        else:
            logging.info(f"Using GQL type for {(baseType)} ({result})")
            print(f"Using GQL type for {(baseType)} ({result})")
        return   result

    # Create custom input types for all fields in the class.
    inputTypes = [
        createCustomInput(field, name, baseType)
        for field, name, baseType in zip(fieldNames, opNames, types)
    ]

    # Creates a dictionary mapping field names to their custom input types, marking them as optional.
    inputTypesDict = {
        fieldName: typing.Optional[inputType]
        for fieldName, inputType in zip(fieldNames, inputTypes)
    }

    #print("inputTypesDict")
    #print(inputTypesDict)

    # Define functions to create 'Or', 'And', and 'Where' operations based on the custom input types.
    def createOr():
        result = type(orName, (object,), {})
        anotations = {
            "_and": typing.Optional[typing.List[andName]],
            **inputTypesDict
        }
        result.__annotations__ = anotations
        for op in anotations.keys():
            setattr(result, op, 
                strawberry.field(name=op, description="Filter method", default=None)
            )
        return result  
        
    orOp = strawberry.input(createOr(), description=f"Or operator definition on {clsname}")
    #print("orOp")
    #print(orOp)

    def createAnd():
        result = type(andName, (object,), {})
        anotations = {
            "_or": typing.Optional[typing.List[orName]],
            **inputTypesDict
        }
        result.__annotations__ = anotations
        for op in anotations.keys():
            setattr(result, op, 
                strawberry.field(name=op, description="Filter method", default=None)
            )
        return result

    andOp = strawberry.input(createAnd(), description=f"And operator definition on {clsname}")
    #print("andOp")
    #print(andOp)

    def createWhereOp():
        result = type(whereName, (object,), {})
        anotations = {
            "_or": typing.Optional[typing.List[orOp]],
            "_and": typing.Optional[typing.List[andOp]],
            **inputTypesDict
        }
        result.__annotations__ = anotations
        for op in anotations.keys():
            setattr(result, op, 
                strawberry.field(name=op, description="Filter method", default=None)
            )
            
        return result  

    whereOp = strawberry.input(createWhereOp(), description=f"Operators definition on {clsname}")
    #print("topOp")
    #print(topOp)
       
    # Register the generated types in the global namespace and input type mapper
    result = [whereOp, andOp, orOp, *inputTypes]
    this = sys.modules[__name__]
    for r in result:
        setattr(this, r.__name__, r)

    #return [topOp, andOp, orOp, *inputTypes]

    #register new type
    inputTypeGQLMapper[whereOp] = whereOp
    return whereOp
    #return inputTypes

# Define custom Strawberry input types for basic data types to support various filter operations
@strawberry.input(description="Str filter methods, only one constrain allowed")
class StrFilter:
    _eq: typing.Optional[str] = strawberry.field(name="_eq", description="operation for select.filter() method", default=None)
    _le: typing.Optional[str] = strawberry.field(name="_le", description="operation for select.filter() method", default=None)
    _lt: typing.Optional[str] = strawberry.field(name="_lt", description="operation for select.filter() method", default=None)
    _ge: typing.Optional[str] = strawberry.field(name="_ge", description="operation for select.filter() method", default=None)
    _gt: typing.Optional[str] = strawberry.field(name="_gt", description="operation for select.filter() method", default=None)
    _like: typing.Optional[str] = strawberry.field(name="_like", description="operation for select.filter() method", default=None)
    _ilike: typing.Optional[str] = strawberry.field(name="_ilike", description="operation for select.filter() method", default=None)
    _startswith: typing.Optional[str] = strawberry.field(name="_startswith", description="operation for select.filter() method", default=None)
    _endswith: typing.Optional[str] = strawberry.field(name="_endswith", description="operation for select.filter() method", default=None)

@strawberry.input(description="Datetime filter methods, only one constrain allowed")
class DatetimeFilter:
    _eq: typing.Optional[datetime.datetime] = strawberry.field(name="_eq", description="operation for select.filter() method", default=None)
    _le: typing.Optional[datetime.datetime] = strawberry.field(name="_le", description="operation for select.filter() method", default=None)
    _lt: typing.Optional[datetime.datetime] = strawberry.field(name="_lt", description="operation for select.filter() method", default=None)
    _ge: typing.Optional[datetime.datetime] = strawberry.field(name="_ge", description="operation for select.filter() method", default=None)
    _gt: typing.Optional[datetime.datetime] = strawberry.field(name="_gt", description="operation for select.filter() method", default=None)

@strawberry.input(description="Integer filter methods, only one constrain allowed")
class IntFilter:
    _eq: typing.Optional[int] = strawberry.field(name="_eq", description="operation for select.filter() method", default=None)
    _le: typing.Optional[int] = strawberry.field(name="_le", description="operation for select.filter() method", default=None)
    _lt: typing.Optional[int] = strawberry.field(name="_lt", description="operation for select.filter() method", default=None)
    _ge: typing.Optional[int] = strawberry.field(name="_ge", description="operation for select.filter() method", default=None)
    _gt: typing.Optional[int] = strawberry.field(name="_gt", description="operation for select.filter() method", default=None)
    _in: typing.Optional[typing.List[int]] = strawberry.field(name="_in", description="operation for select.filter() method", default=None)

@strawberry.input(description="Integer filter methods, only one constrain allowed")
class BoolFilter:
    _eq: typing.Optional[bool] = strawberry.field(name="_eq", description="operation for select.filter() method", default=None)

import uuid
uuid.UUID
@strawberry.input(description="Integer filter methods, only one constrain allowed")
class UuidFilter:
    _eq: typing.Optional[uuid.UUID] = strawberry.field(name="_eq", description="operation for select.filter() method", default=None)
    _in: typing.Optional[typing.List[uuid.UUID]] = strawberry.field(name="_in", description="operation for select.filter() method", default=None)

# Register custom filter types for UUID, int, str, datetime, and bool types in the global mapper
inputTypeGQLMapper[uuid.UUID] = UuidFilter
inputTypeGQLMapper[int] = IntFilter
inputTypeGQLMapper[str] = StrFilter
inputTypeGQLMapper[datetime.datetime] = DatetimeFilter
inputTypeGQLMapper[bool] = BoolFilter
