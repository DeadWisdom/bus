from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    elastic_cloud_id: str = "ActivityBus:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQwNDRhYzg2ZTZkMzc0MzY1YjNmOGI3OWRkZGQxMzM5NyQxYTJjYjllOTRjZDQ0ZTMxYTViNTgwMmE5MTg1YjczYg=="
    elastic_key: str = ""

    auth_private_key: str = "7FXoa8ULkLFIO6HYA4T3Y6zB_FBj9VyVwYLTNp6bYGvzAmDgrOtAiz4Dwkmh3mEMp2DCrFYOKCrmUybz8YRT"

    google_oauth_client: str = ""
    google_oauth_secret: str = ""
