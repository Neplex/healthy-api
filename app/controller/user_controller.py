"""
User controller
"""

from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restplus import Resource, Namespace, fields, abort

import app.service.user_service as user_service
from app.controller.struct_controller import FEATURE_COLLECTION_MODEL, FEATURE_MODEL
from app.service.struct_service import structures_to_geojson, get_structure

API = Namespace('User', description='User related operations', path='/users')

USER_MODEL = API.model('user', {
    'id': fields.Integer(required=False, readonly=True, description='User identifier'),
    'username': fields.String(required=True, description='Username of the user'),
    'created_on': fields.DateTime(required=False, description='User creation date')
})

USER_PASSWORD_MODEL = API.model('user_password', {
    'username': fields.String(required=True, description='Username of the user'),
    'password': fields.String(required=True, description='User password'),
})

FAVORITE_MODEL = API.model('favorite', {
    'structure_id': fields.Integer(required=True, description='Structure identifier')
})


@API.route('')
class UserListController(Resource):
    """
    Show a list of all users
    """

    @API.doc('list_users', security=None)
    @API.marshal_list_with(USER_MODEL)
    def get(self):
        """List all users"""
        return user_service.get_all_user()

    @API.doc('create_user', security=None)
    @API.expect(USER_PASSWORD_MODEL)
    @API.marshal_with(USER_MODEL, code=201)
    def post(self):
        """Add a new user"""
        user = user_service.User(
            username=API.payload['username'], password=API.payload['password']
        )
        user_service.add_user(user)
        return user, 201


@API.route('/<int:user_id>')
@API.response(404, 'User not found')
@API.param('user_id', 'The user identifier')
class UserController(Resource):
    """
    Show, delete or update a defined user.
    """

    @API.doc('get_structure', security=None)
    @API.marshal_with(USER_MODEL)
    def get(self, user_id):
        """Get the user"""
        return user_service.get_user(user_id)

    @jwt_required
    @API.doc('update_user')
    @API.expect(USER_PASSWORD_MODEL)
    @API.marshal_with(USER_MODEL)
    def put(self, user_id):
        """Update the user"""
        user = user_service.get_user(user_id)
        updated_user = user_service.User(
            id=user_id,
            username=API.payload['username'],
            password_hash=user.password_hash,
            created_on=user.created_on,
            structures=user.structures
        )

        if "password" in API.payload.keys():
            updated_user.password = API.payload['password']

        user_service.update_user(updated_user)

        return updated_user

    @jwt_required
    @API.doc('delete_user')
    @API.response(204, 'User deleted')
    @API.response(401, 'Cannot delete user. An user can only delete itself')
    def delete(self, user_id):
        """Delete a user given its identifier"""
        if user_id != get_jwt_identity():
            abort(401)

        user_service.delete_user(user_id)
        return '', 204


@API.route('/<int:user_id>/structures')
class StructureUserController(Resource):
    """
    Show a list of all structures from a user
    """

    @API.doc('list_resources_from_user', security=None)
    @API.marshal_with(FEATURE_COLLECTION_MODEL)
    def get(self, user_id):
        """List all structures of an user"""
        return structures_to_geojson(user_service.get_all_structure_by_user(user_id))


@API.route('/<int:user_id>/favorites')
class FavoritesUserController(Resource):
    """
    Show a list of all favorites of a user
    """

    @API.doc('list_favorites_of_user', security=None)
    @API.marshal_with(FEATURE_COLLECTION_MODEL)
    def get(self, user_id):
        """List all favorites of an user"""
        return structures_to_geojson(user_service.get_favorites_by_user(user_id))

    @jwt_required
    @API.doc('add_favorite_to_user', security=None)
    @API.expect(FAVORITE_MODEL)
    @API.marshal_with(FEATURE_MODEL, skip_none=True)
    def post(self, user_id):
        """Add a new favorite for user"""
        structure_id = API.payload['structure_id']
        user_service.add_favorite_to_user(user_id, structure_id)
        return structures_to_geojson(get_structure(structure_id))


@API.route('/<int:user_id>/favorites/<int:favorite_id>')
class FavoriteUserDeleteController(Resource):
    """
    Delete a specific favorite of an user
    """
    @jwt_required
    @API.doc('delete_favorite')
    @API.response(204, 'Favorite deleted')
    @API.response(401, 'Cannot delete favorite. A favorite can only be deleted by its user')
    def delete(self, user_id, favorite_id):
        """Delete a user given its identifier"""
        if user_id == get_jwt_identity():
            user_service.delete_favorite(user_id, favorite_id)
            return '', 204

        abort(401)
        return ''
