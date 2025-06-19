from purch.domains.auth.service import hash_password
from purch.domains.user.repository import UserRepository
from purch.domains.user.schemas import UserCreate, UserResponse

class UserService():

    def __init__(self):
        self.user_repo = UserRepository()
        pass

    def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Register a new user with the provided user data.
        """    
        existing_user = self.user_repo.get_via_username(username=user_data.username)

        # If user already exists, return None
        if existing_user is not None:
            return None

        # If user does not exist, add the user to the repository and return the newly created user response
        user_data.password = hash_password(user_data.password)
        self.user_repo.add(user_data)
        newly_created_user = self.user_repo.get_via_username(username=user_data.username)
        return UserResponse(
            id=newly_created_user.id,
            username=newly_created_user.username,
            first_name=newly_created_user.first_name,
            last_name=newly_created_user.last_name
        )
            
        
