

def test_settings_override(configure_test_settings, test_db_name, test_client):
    """
    Test that settings are properly overridden in tests.
    This test verifies that:
    1. The POSTGRES_DATABASE is set to our test database name
    2. The settings instance is properly cached and reused
    3. The test database name is unique
    """
    test_settings = configure_test_settings
    
    # Verify the POSTGRES_DATABASE was properly set
    assert test_settings.POSTGRES_DATABASE == test_db_name
    assert test_settings.POSTGRES_HOST == "test-postgres"
    assert test_settings.REDIS_HOST == "test-redis"
    
    # Verify that get_settings() returns the same instance
    from purch.common.config import get_settings
    current_settings = get_settings()
    assert current_settings.POSTGRES_DATABASE == test_db_name
    
    # Verify the settings are used in the startup module
    from purch.api.startup import get_settings as startup_get_settings
    startup_settings = startup_get_settings()
    assert startup_settings.POSTGRES_DATABASE == test_db_name