from sqlalchemy import Column, ForeignKey, Table

from amt.models.base import Base

users_and_organizations = Table(
    "users_and_organizations",
    Base.metadata,
    Column("organization_id", ForeignKey("organization.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
    Column("user_id", ForeignKey("user.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
)


role_and_organizations = Table(
    "role_and_organizations",
    Base.metadata,
    Column("role_id", ForeignKey("role.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
    Column("organization_id", ForeignKey("organization.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
)

role_and_algorithms = Table(
    "role_and_algorithms",
    Base.metadata,
    Column("role_id", ForeignKey("role.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
    Column("algorithms_id", ForeignKey("algorithm.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
)

role_and_users = Table(
    "role_and_users",
    Base.metadata,
    Column("user_id", ForeignKey("user.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
    Column("role_id", ForeignKey("role.id"), primary_key=True),  # pyright: ignore[reportUnknownArgumentType]
)


#######

# https://amt.prd.apps.digilab.network/organizations/
# https://amt.prd.apps.digilab.network/organizations/demo-amt/algorithms
# https://amt.prd.apps.digilab.network/organizations/demo-amt/members
# https://amt.prd.apps.digilab.network/algorithms/
# https://amt.prd.apps.digilab.network/algorithms/new
# https://amt.prd.apps.digilab.network/algorithm/36/details
# https://amt.prd.apps.digilab.network/algorithm/36/details/system_card
# https://amt.prd.apps.digilab.network/algorithm/36/details/model/inference
# https://amt.prd.apps.digilab.network/algorithm/36/details/system_card/requirements
# https://amt.prd.apps.digilab.network/algorithm/36/details/system_card/data
# https://amt.prd.apps.digilab.network/algorithm/36/details/tasks
# https://amt.prd.apps.digilab.network/algorithm/36/details/system_card/instruments


# Maintainer Organization
# Member Organization
# Viewer Organization

# Maintainer Algorithm
# Member Algorithm
# Viewer Algorithm