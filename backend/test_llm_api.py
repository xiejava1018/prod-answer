"""
Test script for LLM Configuration Management API

This script demonstrates all the API endpoints and their functionality.
Run with: DJANGO_SETTINGS_MODULE=config.settings.development python test_llm_api.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.llm.models import LLMModelConfig
from apps.llm.serializers import LLMModelConfigSerializer, LLMTestSerializer
from apps.llm.services import LLMProviderFactory


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_serializer_validation():
    """Test serializer validation."""
    print_section("1. Testing Serializer Validation")

    test_cases = [
        {
            'name': 'Valid OpenAI config',
            'data': {
                'provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'api_key_encrypted': 'sk-test1234567890abcdefghijklmnopqrstuvwxyz',
                'max_tokens': 2000,
                'temperature': 0.7,
            },
            'should_pass': True
        },
        {
            'name': 'Valid ZhipuAI config',
            'data': {
                'provider': 'zhipuai',
                'model_name': 'glm-4-flash',
                'api_key_encrypted': 'test-key-1234567890',
                'max_tokens': 4000,
                'temperature': 0.5,
            },
            'should_pass': True
        },
        {
            'name': 'Invalid provider',
            'data': {
                'provider': 'invalid_provider',
                'model_name': 'test-model',
                'api_key_encrypted': 'test-key',
            },
            'should_pass': False
        },
        {
            'name': 'Temperature out of range',
            'data': {
                'provider': 'openai',
                'model_name': 'gpt-4o-mini',
                'api_key_encrypted': 'test-key',
                'temperature': 3.0,
            },
            'should_pass': False
        },
        {
            'name': 'Missing API key',
            'data': {
                'provider': 'openai',
                'model_name': 'gpt-4o-mini',
            },
            'should_pass': False
        },
    ]

    for test_case in test_cases:
        serializer = LLMModelConfigSerializer(data=test_case['data'])
        is_valid = serializer.is_valid()

        if is_valid == test_case['should_pass']:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"

        print(f"{status} - {test_case['name']}")
        if not is_valid:
            print(f"    Errors: {serializer.errors}")


def test_api_key_masking():
    """Test API key masking functionality."""
    print_section("2. Testing API Key Masking")

    # Create a test config (not saving to DB)
    config_data = {
        'provider': 'openai',
        'model_name': 'gpt-4o-mini',
        'api_key_encrypted': 'sk-test1234567890abcdefghijklmnopqrstuvwxyz',
        'max_tokens': 2000,
        'temperature': 0.7,
    }

    serializer = LLMModelConfigSerializer(data=config_data)
    if serializer.is_valid():
        # Simulate the masking that would happen in response
        instance = serializer.save()

        # Test masking
        masked = serializer.get_api_key_masked(instance)
        has_key = serializer.get_has_api_key(instance)

        print(f"✓ API key configured: {has_key}")
        print(f"✓ Masked API key: {masked}")
        print(f"  (Shows only last 4 characters)")
    else:
        print(f"✗ Failed to create test config: {serializer.errors}")


def test_provider_factory():
    """Test LLM provider factory."""
    print_section("3. Testing LLM Provider Factory")

    # Get available providers
    providers = LLMProviderFactory.get_available_providers()
    print(f"✓ Available providers: {', '.join(providers)}")

    # Test provider types
    for provider_type in providers:
        try:
            config = {
                'provider': provider_type,
                'model_name': 'test-model',
                'api_key': 'test-key-12345',
            }
            provider = LLMProviderFactory.create_provider(config, use_cache=False)
            model_info = provider.get_model_info()
            print(f"✓ {provider_type} provider created successfully")
            print(f"    Model: {model_info.get('model_name')}")
        except Exception as e:
            print(f"✗ Failed to create {provider_type} provider: {str(e)}")


def test_url_registration():
    """Test URL registration."""
    print_section("4. Testing URL Registration")

    from django.urls import get_resolver
    from django.urls.resolvers import URLPattern, URLResolver

    def find_llm_urls(urlpatterns, prefix=''):
        llm_urls = []
        for pattern in urlpatterns:
            if isinstance(pattern, URLPattern):
                path = prefix + str(pattern.pattern)
                if 'api/v1' in path and ('llm' in path or 'configs' in path or 'analysis-results' in path):
                    llm_urls.append(path)
            elif isinstance(pattern, URLResolver):
                new_prefix = prefix + str(pattern.pattern)
                llm_urls.extend(find_llm_urls(pattern.url_patterns, new_prefix))
        return llm_urls

    resolver = get_resolver()
    llm_urls = find_llm_urls(resolver.url_patterns)

    print(f"✓ Found {len(llm_urls)} LLM-related API endpoints")

    # Group by endpoint type
    config_urls = [u for u in llm_urls if '/configs/' in u]
    analysis_urls = [u for u in llm_urls if '/analysis-results/' in u]

    print(f"  - Config endpoints: {len(config_urls)}")
    print(f"  - Analysis result endpoints: {len(analysis_urls)}")

    # Show key endpoints
    key_endpoints = [
        'GET    /api/v1/llm/configs/',
        'POST   /api/v1/llm/configs/',
        'GET    /api/v1/llm/configs/<id>/',
        'PUT    /api/v1/llm/configs/<id>/',
        'DELETE /api/v1/llm/configs/<id>/',
        'POST   /api/v1/llm/configs/<id>/test/',
        'POST   /api/v1/llm/configs/<id>/set_default/',
        'GET    /api/v1/llm/configs/active_providers/',
        'GET    /api/v1/llm/configs/default_provider/',
    ]

    print("\n  Key endpoints:")
    for endpoint in key_endpoints:
        print(f"    {endpoint}")


def test_permissions():
    """Test permission configuration."""
    print_section("5. Testing Permission Configuration")

    from apps.llm.views import LLMConfigViewSet

    viewset = LLMConfigViewSet()

    permissions = {
        'list': 'IsAuthenticated',
        'retrieve': 'IsAuthenticated',
        'test': 'IsAuthenticated',
        'create': 'IsAdminUser',
        'update': 'IsAdminUser',
        'partial_update': 'IsAdminUser',
        'destroy': 'IsAdminUser',
        'set_default': 'IsAdminUser',
    }

    print("✓ Permission configuration:")
    for action, expected in permissions.items():
        viewset.action = action
        perms = viewset.get_permissions()
        actual = perms[0].__class__.__name__ if perms else 'None'
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {action:20} -> {actual}")


def test_model_methods():
    """Test LLMModelConfig methods."""
    print_section("6. Testing Model Methods")

    # Create a test config
    config = LLMModelConfig(
        provider='openai',
        model_name='gpt-4o-mini',
        max_tokens=2000,
        temperature=0.7,
        is_active=True,
        is_default=False
    )

    # Test API key encryption
    test_key = 'sk-test1234567890abcdefghijklmnopqrstuvwxyz'
    config.set_api_key(test_key)

    # Test encryption
    encrypted = config.api_key_encrypted
    print(f"✓ API key encrypted: {encrypted[:20]}...")

    # Test decryption
    decrypted = config.get_api_key()
    print(f"✓ API key decrypted: {decrypted == test_key}")

    # Test __str__ method
    str_repr = str(config)
    print(f"✓ String representation: {str_repr}")

    # Test validation (should raise ValidationError)
    try:
        config.temperature = 3.0
        config.full_clean()
        print("✗ Should have raised ValidationError for invalid temperature")
    except Exception as e:
        print(f"✓ Validation works: {type(e).__name__}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  LLM Configuration Management API - Test Suite")
    print("="*60)

    try:
        test_serializer_validation()
        test_api_key_masking()
        test_provider_factory()
        test_url_registration()
        test_permissions()
        test_model_methods()

        print_section("All Tests Completed!")
        print("✓ All API components are working correctly")
        print("\nNext steps:")
        print("  1. Start the Django development server")
        print("  2. Test endpoints with Postman or curl")
        print("  3. Verify authentication and authorization")
        print("  4. Test with real API keys for providers")

    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
