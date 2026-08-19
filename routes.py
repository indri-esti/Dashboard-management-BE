from resources.health import HealthResource

from resources.role import RoleResource

from resources.user import UserResource, ReactivateUserResource

from resources.auth import LoginResource, RegisterResource

from resources.profile import ProfileResource


def add_routes(app):

    app.add_route("/", HealthResource())

    app.add_route("/api/roles", RoleResource())

    app.add_route("/api/users", UserResource())

    app.add_route(
        "/api/users/{user_id}",
        UserResource()
    )

    app.add_route(
        "/api/users/{user_id}/reactivate",
        ReactivateUserResource()
    )

    app.add_route(
        "/api/login",
        LoginResource()
    )

    app.add_route(
        "/api/register",
        RegisterResource()
    )

    # PROFILE
    app.add_route(
        "/api/profile",
        ProfileResource()
    )