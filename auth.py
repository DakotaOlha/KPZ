import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pyodbc


class AuthManager:

    def __init__(self, db_connection):
        self.conn = db_connection
        self.cursor = db_connection.cursor()
        self.current_user: Optional[Dict] = None
        self.session_token: Optional[str] = None

    def login(self, username: str, password: str, ip_address: str = None) -> Dict:
        try:
            # Виклик нової процедури LoginUser
            self.cursor.execute(
                "EXEC LoginUser ?, ?",
                (username, password)
            )

            row = self.cursor.fetchone()

            if not row:
                return {
                    'success': False,
                    'message': "Сервер не повернув дані."
                }

            success = row[0]
            message = row[1]
            role = row[2]
            user_id = row[3]
            username_db = row[4]
            email = row[5]

            if success:
                self.current_user = {
                    'user_id': user_id,
                    'username': username_db,
                    'email': email,
                    'role_name': role
                }
                self.session_token = None  # Немає токенів у твоїй БД

                return {
                    'success': True,
                    'user': self.current_user,
                    'message': message
                }
            else:
                return {
                    'success': False,
                    'message': message
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка: {str(e)}'
            }

    def logout(self) -> bool:
        if not self.session_token:
            return False

        try:
            self.cursor.execute("EXEC sp_Logout ?", (self.session_token,))
            self.conn.commit()

            self.current_user = None
            self.session_token = None

            return True
        except:
            return False

    def validate_session(self, session_token: str) -> bool:
        try:
            self.cursor.execute("EXEC sp_ValidateSession ?", (session_token,))
            result = self.cursor.fetchone()

            if result and result[5] == 1:
                self.current_user = {
                    'user_id': result[0],
                    'username': result[1],
                    'full_name': result[2],
                    'role_name': result[3]
                }
                self.session_token = session_token
                return True
            return False

        except:
            return False

    def has_permission(self, permission_name: str) -> bool:
        if not self.current_user:
            return False

        try:
            query = "SELECT dbo.fn_UserHasPermission(?, ?)"
            self.cursor.execute(query, (self.current_user['user_id'], permission_name))
            result = self.cursor.fetchone()

            return result[0] == 1 if result else False
        except:
            return False

    def get_user_permissions(self) -> List[str]:
        if not self.current_user:
            return []

        try:
            query = "SELECT permission_name FROM dbo.fn_GetUserPermissions(?)"
            self.cursor.execute(query, (self.current_user['user_id'],))

            permissions = [row[0] for row in self.cursor.fetchall()]
            return permissions
        except:
            return []

    def log_action(self, action_type: str, table_name: str,
                   record_id: int = None, old_value: str = None,
                   new_value: str = None, ip_address: str = None):

        if not self.current_user:
            return

        try:
            self.cursor.execute(
                "EXEC sp_LogAction ?, ?, ?, ?, ?, ?, ?",
                (
                    self.current_user['user_id'],
                    action_type,
                    table_name,
                    record_id,
                    old_value,
                    new_value,
                    ip_address
                )
            )
            self.conn.commit()
        except Exception as e:
            print(f"Помилка логування: {e}")

    def is_authenticated(self) -> bool:
        return self.current_user is not None

    def get_current_user(self) -> Optional[Dict]:
        return self.current_user

    def require_permission(self, permission_name: str) -> bool:
        if not self.has_permission(permission_name):
            raise PermissionError(
                f"Недостатньо прав: потрібен дозвіл '{permission_name}'"
            )
        return True


class UserManager:

    def __init__(self, db_connection, auth_manager: AuthManager):
        self.conn = db_connection
        self.cursor = db_connection.cursor()
        self.auth = auth_manager

    def create_user(self, username: str, password: str, email: str,
                   full_name: str, role_name: str) -> Dict:
        try:
            self.auth.require_permission('users.create')

            new_user_id = self.cursor.var(pyodbc.SQL_INTEGER)

            self.cursor.execute(
                "EXEC sp_CreateUser ?, ?, ?, ?, ?, ?, ?",
                (
                    username,
                    password,
                    email,
                    full_name,
                    role_name,
                    self.auth.current_user['user_id'],
                    new_user_id
                )
            )

            result = self.cursor.fetchone()
            self.conn.commit()

            self.auth.log_action(
                'CREATE',
                'Users',
                result[0] if result else None,
                None,
                f"Username: {username}, Role: {role_name}"
            )

            return {
                'success': True,
                'user_id': result[0] if result else None,
                'message': result[1] if result else 'Користувача створено'
            }

        except PermissionError as e:
            return {'success': False, 'message': str(e)}
        except Exception as e:
            return {'success': False, 'message': f'Помилка: {str(e)}'}

    def get_all_users(self) -> List[Dict]:
        try:
            self.auth.require_permission('users.view')

            query = """
                SELECT 
                    id, username, email, full_name, role_display_name,
                    is_active, is_locked, last_login, created_at
                FROM vw_UserDetails
                ORDER BY created_at DESC
            """

            self.cursor.execute(query)

            users = []
            for row in self.cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'full_name': row[3],
                    'role': row[4],
                    'is_active': row[5],
                    'is_locked': row[6],
                    'last_login': row[7],
                    'created_at': row[8]
                })

            return users

        except PermissionError:
            return []
        except Exception as e:
            print(f"Помилка отримання користувачів: {e}")
            return []

    def block_user(self, user_id: int, reason: str = None) -> bool:
        try:
            self.auth.require_permission('users.block')

            self.cursor.execute(
                "UPDATE Users SET is_locked = 1 WHERE id = ?",
                (user_id,)
            )
            self.conn.commit()

            self.auth.log_action(
                'UPDATE',
                'Users',
                user_id,
                'is_locked: 0',
                f'is_locked: 1, Reason: {reason}'
            )

            return True

        except PermissionError:
            return False
        except:
            return False

    def unblock_user(self, user_id: int) -> bool:
        try:
            self.auth.require_permission('users.block')

            self.cursor.execute(
                "UPDATE Users SET is_locked = 0, failed_login_attempts = 0 WHERE id = ?",
                (user_id,)
            )
            self.conn.commit()

            self.auth.log_action('UPDATE', 'Users', user_id, 'is_locked: 1', 'is_locked: 0')

            return True

        except:
            return False

    def delete_user(self, user_id: int) -> bool:
        try:
            self.auth.require_permission('users.delete')

            if user_id == self.auth.current_user['user_id']:
                return False

            self.cursor.execute("DELETE FROM Users WHERE id = ?", (user_id,))
            self.conn.commit()

            self.auth.log_action('DELETE', 'Users', user_id)

            return True

        except:
            return False


class RoleManager:

    def __init__(self, db_connection, auth_manager: AuthManager):
        self.conn = db_connection
        self.cursor = db_connection.cursor()
        self.auth = auth_manager

    def get_all_roles(self) -> List[Dict]:
        try:
            query = """
                SELECT id, role_name, display_name, description, is_active
                FROM Roles
                ORDER BY id
            """

            self.cursor.execute(query)

            roles = []
            for row in self.cursor.fetchall():
                roles.append({
                    'id': row[0],
                    'role_name': row[1],
                    'display_name': row[2],
                    'description': row[3],
                    'is_active': row[4]
                })

            return roles

        except Exception as e:
            print(f"Помилка отримання ролей: {e}")
            return []

    def get_role_permissions(self, role_id: int) -> List[str]:
        try:
            query = """
                SELECT p.permission_name, p.display_name, p.category
                FROM RolePermissions rp
                INNER JOIN Permissions p ON rp.permission_id = p.id
                WHERE rp.role_id = ?
            """

            self.cursor.execute(query, (role_id,))

            permissions = []
            for row in self.cursor.fetchall():
                permissions.append({
                    'name': row[0],
                    'display_name': row[1],
                    'category': row[2]
                })

            return permissions

        except:
            return []


def require_permission(permission_name: str):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'auth') and isinstance(self.auth, AuthManager):
                self.auth.require_permission(permission_name)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator