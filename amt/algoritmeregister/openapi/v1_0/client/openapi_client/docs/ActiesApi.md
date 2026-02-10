# amt.algoritmeregister.openapi.v1_0.client.openapi_client.ActiesApi

All URIs are relative to _/aanleverapi/v1_0_

| Method                                                                              | HTTP request                                                                            | Description                              |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ---------------------------------------- |
| [**get_one_preview_url**](ActiesApi.md#get_one_preview_url)                         | **GET** /organizations/{organisation_id}/algorithms/{algorithm_id}/preview              | Bekijk een preview van een algoritme.    |
| [**release_one_algorithm**](ActiesApi.md#release_one_algorithm)                     | **PUT** /organizations/{organisation_id}/algorithms/{algorithm_id}/release              | Geef een algoritme vrij voor publicatie. |
| [**retract_one_published_algorithm**](ActiesApi.md#retract_one_published_algorithm) | **DELETE** /organizations/{organisation_id}/published-algorithms/{algorithm_id}/retract | Verberg een algoritme.                   |

# **get_one_preview_url**

> PreviewUrl get_one_preview_url(organisation_id, algorithm_id)

Bekijk een preview van een algoritme.

Krijg een URL waarmee de laatste gegevens van een algoritme kunnen worden bekeken.

### Example

- OAuth Authentication (OAuth2AuthorizationCodeBearer):

```python
import amt.algoritmeregister.openapi.v1_0.client.openapi_client
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.preview_url import PreviewUrl
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /aanleverapi/v1_0
# See configuration.py for a list of all supported configuration parameters.
configuration = amt.algoritmeregister.openapi.v1_0.client.openapi_client.Configuration(
    host = "/aanleverapi/v1_0"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with amt.algoritmeregister.openapi.v1_0.client.openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.ActiesApi(api_client)
    organisation_id = 'organisation_id_example' # str |
    algorithm_id = 'algorithm_id_example' # str |

    try:
        # Bekijk een preview van een algoritme.
        api_response = api_instance.get_one_preview_url(organisation_id, algorithm_id)
        print("The response of ActiesApi->get_one_preview_url:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ActiesApi->get_one_preview_url: %s\n" % e)
```

### Parameters

| Name                | Type    | Description | Notes |
| ------------------- | ------- | ----------- | ----- |
| **organisation_id** | **str** |             |
| **algorithm_id**    | **str** |             |

### Return type

[**PreviewUrl**](PreviewUrl.md)

### Authorization

[OAuth2AuthorizationCodeBearer](../README.md#OAuth2AuthorizationCodeBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description             | Response headers |
| ----------- | ----------------------- | ---------------- |
| **200**     | Successful Response     | -                |
| **401**     | Authentication Error    | -                |
| **404**     | Not Found Error         | -                |
| **429**     | Too Many Requests Error | -                |
| **422**     | Validation Error        | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **release_one_algorithm**

> AlgorithmActionResponse release_one_algorithm(organisation_id, algorithm_id)

Geef een algoritme vrij voor publicatie.

Geef de laatste gegevens van een algoritme vrij, zodat BZK ze kan gaan inspecteren, en uiteindelijk publiceren.

### Example

- OAuth Authentication (OAuth2AuthorizationCodeBearer):

```python
import amt.algoritmeregister.openapi.v1_0.client.openapi_client
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.algorithm_action_response import AlgorithmActionResponse
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /aanleverapi/v1_0
# See configuration.py for a list of all supported configuration parameters.
configuration = amt.algoritmeregister.openapi.v1_0.client.openapi_client.Configuration(
    host = "/aanleverapi/v1_0"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with amt.algoritmeregister.openapi.v1_0.client.openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.ActiesApi(api_client)
    organisation_id = 'organisation_id_example' # str |
    algorithm_id = 'algorithm_id_example' # str |

    try:
        # Geef een algoritme vrij voor publicatie.
        api_response = api_instance.release_one_algorithm(organisation_id, algorithm_id)
        print("The response of ActiesApi->release_one_algorithm:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ActiesApi->release_one_algorithm: %s\n" % e)
```

### Parameters

| Name                | Type    | Description | Notes |
| ------------------- | ------- | ----------- | ----- |
| **organisation_id** | **str** |             |
| **algorithm_id**    | **str** |             |

### Return type

[**AlgorithmActionResponse**](AlgorithmActionResponse.md)

### Authorization

[OAuth2AuthorizationCodeBearer](../README.md#OAuth2AuthorizationCodeBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description             | Response headers |
| ----------- | ----------------------- | ---------------- |
| **200**     | Successful Response     | -                |
| **401**     | Authentication Error    | -                |
| **404**     | Not Found Error         | -                |
| **429**     | Too Many Requests Error | -                |
| **409**     | Conflict Error          | -                |
| **422**     | Validation Error        | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **retract_one_published_algorithm**

> object retract_one_published_algorithm(organisation_id, algorithm_id)

Verberg een algoritme.

Verberg een algoritme, zodat deze niet meer publiek toegankelijk is.

### Example

- OAuth Authentication (OAuth2AuthorizationCodeBearer):

```python
import amt.algoritmeregister.openapi.v1_0.client.openapi_client
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to /aanleverapi/v1_0
# See configuration.py for a list of all supported configuration parameters.
configuration = amt.algoritmeregister.openapi.v1_0.client.openapi_client.Configuration(
    host = "/aanleverapi/v1_0"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
with amt.algoritmeregister.openapi.v1_0.client.openapi_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.ActiesApi(api_client)
    organisation_id = 'organisation_id_example' # str |
    algorithm_id = 'algorithm_id_example' # str |

    try:
        # Verberg een algoritme.
        api_response = api_instance.retract_one_published_algorithm(organisation_id, algorithm_id)
        print("The response of ActiesApi->retract_one_published_algorithm:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ActiesApi->retract_one_published_algorithm: %s\n" % e)
```

### Parameters

| Name                | Type    | Description | Notes |
| ------------------- | ------- | ----------- | ----- |
| **organisation_id** | **str** |             |
| **algorithm_id**    | **str** |             |

### Return type

**object**

### Authorization

[OAuth2AuthorizationCodeBearer](../README.md#OAuth2AuthorizationCodeBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

### HTTP response details

| Status code | Description             | Response headers |
| ----------- | ----------------------- | ---------------- |
| **200**     | Successful Response     | -                |
| **401**     | Authentication Error    | -                |
| **404**     | Not Found Error         | -                |
| **429**     | Too Many Requests Error | -                |
| **422**     | Validation Error        | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
