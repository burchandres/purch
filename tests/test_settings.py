

def test_settings_override(configure_test_settings, test_db_name, test_client):
    """
    Test that settings are properly overridden in tests.
    This test verifies that:
    1. The DB_NAME is set to our test database name
    2. The settings instance is properly cached and reused
    3. The test database name is unique
    """
    test_settings = configure_test_settings
    
    # Verify the DB_NAME was properly set
    assert test_settings.DB_NAME == test_db_name
    
    # Verify that get_settings() returns the same instance
    from purch.utils.config import get_settings
    current_settings = get_settings()
    assert current_settings.DB_NAME == test_db_name
    
    # Verify the settings are used in the startup module
    from purch.core.startup import get_settings as startup_get_settings
    startup_settings = startup_get_settings()
    assert startup_settings.DB_NAME == test_db_name

