# amt.algoritmeregister.openapi.v1_0.client.openapi_client.AlgoritmesInOntwikkelingApi

All URIs are relative to _/aanleverapi/v1_0_

| Method                                                                                        | HTTP request                                                                         | Description                                   |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------- |
| [**archive_algorithm_version**](AlgoritmesInOntwikkelingApi.md#archive_algorithm_version)     | **PUT** /organizations/{organisation_id}/algorithms/{algorithm_id}/archive_version   | Archive Algorithm Version                     |
| [**create_one_algorithm**](AlgoritmesInOntwikkelingApi.md#create_one_algorithm)               | **POST** /organizations/{organisation_id}/algorithms                                 | Maak een nieuw algoritme.                     |
| [**get_all_algorithms**](AlgoritmesInOntwikkelingApi.md#get_all_algorithms)                   | **GET** /organizations/{organisation_id}/algorithms                                  | Haal alle beschikbare algoritmes op.          |
| [**get_one_algorithm**](AlgoritmesInOntwikkelingApi.md#get_one_algorithm)                     | **GET** /organizations/{organisation_id}/algorithms/{algorithm_id}                   | Haal de nieuwste versie van één algoritme op. |
| [**unarchive_algorithm_version**](AlgoritmesInOntwikkelingApi.md#unarchive_algorithm_version) | **PUT** /organizations/{organisation_id}/algorithms/{algorithm_id}/unarchive_version | Unarchive Algorithm Version                   |
| [**update_one_algorithm**](AlgoritmesInOntwikkelingApi.md#update_one_algorithm)               | **PUT** /organizations/{organisation_id}/algorithms/{algorithm_id}                   | Update een algoritme.                         |

# **archive_algorithm_version**

> object archive_algorithm_version(organisation_id, algorithm_id, archive_version_request)

Archive Algorithm Version

### Example

- OAuth Authentication (OAuth2AuthorizationCodeBearer):

```python
import amt.algoritmeregister.openapi.v1_0.client.openapi_client
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.archive_version_request import ArchiveVersionRequest
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
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.AlgoritmesInOntwikkelingApi(api_client)
    organisation_id = 'organisation_id_example' # str |
    algorithm_id = 'algorithm_id_example' # str |
    archive_version_request = amt.algoritmeregister.openapi.v1_0.client.openapi_client.ArchiveVersionRequest() # ArchiveVersionRequest |

    try:
        # Archive Algorithm Version
        api_response = api_instance.archive_algorithm_version(organisation_id, algorithm_id, archive_version_request)
        print("The response of AlgoritmesInOntwikkelingApi->archive_algorithm_version:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AlgoritmesInOntwikkelingApi->archive_algorithm_version: %s\n" % e)
```

### Parameters

| Name                        | Type                                                  | Description | Notes |
| --------------------------- | ----------------------------------------------------- | ----------- | ----- |
| **organisation_id**         | **str**                                               |             |
| **algorithm_id**            | **str**                                               |             |
| **archive_version_request** | [**ArchiveVersionRequest**](ArchiveVersionRequest.md) |             |

### Return type

**object**

### Authorization

[OAuth2AuthorizationCodeBearer](../README.md#OAuth2AuthorizationCodeBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description         | Response headers |
| ----------- | ------------------- | ---------------- |
| **200**     | Successful Response | -                |
| **422**     | Validation Error    | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_one_algorithm**

> NewAlgorithmResponse create_one_algorithm(organisation_id, algorithm_in)

Maak een nieuw algoritme.

Het aanroepen van dit endpoint creeërt een nieuw algoritme.

### Example

- OAuth Authentication (OAuth2AuthorizationCodeBearer):

```python
import amt.algoritmeregister.openapi.v1_0.client.openapi_client
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.algorithm_in import AlgorithmIn
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.new_algorithm_response import NewAlgorithmResponse
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
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.AlgoritmesInOntwikkelingApi(api_client)
    organisation_id = 'organisation_id_example' # str |
    algorithm_in = amt.algoritmeregister.openapi.v1_0.client.openapi_client.AlgorithmIn() # AlgorithmIn |

    try:
        # Maak een nieuw algoritme.
        api_response = api_instance.create_one_algorithm(organisation_id, algorithm_in)
        print("The response of AlgoritmesInOntwikkelingApi->create_one_algorithm:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AlgoritmesInOntwikkelingApi->create_one_algorithm: %s\n" % e)
```

### Parameters

| Name                | Type                              | Description | Notes |
| ------------------- | --------------------------------- | ----------- | ----- |
| **organisation_id** | **str**                           |             |
| **algorithm_in**    | [**AlgorithmIn**](AlgorithmIn.md) |             |

### Return type

[**NewAlgorithmResponse**](NewAlgorithmResponse.md)

### Authorization

[OAuth2AuthorizationCodeBearer](../README.md#OAuth2AuthorizationCodeBearer)

### HTTP request headers

- **Content-Type**: application/json
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

# **get_all_algorithms**

> List[AlgorithmSummary] get_all_algorithms(organisation_id)

Haal alle beschikbare algoritmes op.

Geeft een samenvatting van de algoritmes terug waar u bewerkingsrechten voor heeft.

### Example

- OAuth Authentication (OAuth2AuthorizationCodeBearer):

```python
import amt.algoritmeregister.openapi.v1_0.client.openapi_client
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.algorithm_summary import AlgorithmSummary
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
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.AlgoritmesInOntwikkelingApi(api_client)
    organisation_id = 'organisation_id_example' # str |

    try:
        # Haal alle beschikbare algoritmes op.
        api_response = api_instance.get_all_algorithms(organisation_id)
        print("The response of AlgoritmesInOntwikkelingApi->get_all_algorithms:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AlgoritmesInOntwikkelingApi->get_all_algorithms: %s\n" % e)
```

### Parameters

| Name                | Type    | Description | Notes |
| ------------------- | ------- | ----------- | ----- |
| **organisation_id** | **str** |             |

### Return type

[**List[AlgorithmSummary]**](AlgorithmSummary.md)

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

# **get_one_algorithm**

> AnyOfTheAlgorithmStandards get_one_algorithm(organisation_id, algorithm_id)

Haal de nieuwste versie van één algoritme op.

Verkrijg de nieuwste gegevens van één algoritme. Dit is niet per se gepubliceerd.

### Example

- OAuth Authentication (OAuth2AuthorizationCodeBearer):

```python
import amt.algoritmeregister.openapi.v1_0.client.openapi_client
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.any_of_the_algorithm_standards import AnyOfTheAlgorithmStandards
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
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.AlgoritmesInOntwikkelingApi(api_client)
    organisation_id = 'organisation_id_example' # str |
    algorithm_id = 'algorithm_id_example' # str |

    try:
        # Haal de nieuwste versie van één algoritme op.
        api_response = api_instance.get_one_algorithm(organisation_id, algorithm_id)
        print("The response of AlgoritmesInOntwikkelingApi->get_one_algorithm:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AlgoritmesInOntwikkelingApi->get_one_algorithm: %s\n" % e)
```

### Parameters

| Name                | Type    | Description | Notes |
| ------------------- | ------- | ----------- | ----- |
| **organisation_id** | **str** |             |
| **algorithm_id**    | **str** |             |

### Return type

[**AnyOfTheAlgorithmStandards**](AnyOfTheAlgorithmStandards.md)

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

# **unarchive_algorithm_version**

> object unarchive_algorithm_version(organisation_id, algorithm_id, archive_version_request)

Unarchive Algorithm Version

### Example

- OAuth Authentication (OAuth2AuthorizationCodeBearer):

```python
import amt.algoritmeregister.openapi.v1_0.client.openapi_client
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.archive_version_request import ArchiveVersionRequest
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
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.AlgoritmesInOntwikkelingApi(api_client)
    organisation_id = 'organisation_id_example' # str |
    algorithm_id = 'algorithm_id_example' # str |
    archive_version_request = amt.algoritmeregister.openapi.v1_0.client.openapi_client.ArchiveVersionRequest() # ArchiveVersionRequest |

    try:
        # Unarchive Algorithm Version
        api_response = api_instance.unarchive_algorithm_version(organisation_id, algorithm_id, archive_version_request)
        print("The response of AlgoritmesInOntwikkelingApi->unarchive_algorithm_version:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AlgoritmesInOntwikkelingApi->unarchive_algorithm_version: %s\n" % e)
```

### Parameters

| Name                        | Type                                                  | Description | Notes |
| --------------------------- | ----------------------------------------------------- | ----------- | ----- |
| **organisation_id**         | **str**                                               |             |
| **algorithm_id**            | **str**                                               |             |
| **archive_version_request** | [**ArchiveVersionRequest**](ArchiveVersionRequest.md) |             |

### Return type

**object**

### Authorization

[OAuth2AuthorizationCodeBearer](../README.md#OAuth2AuthorizationCodeBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description         | Response headers |
| ----------- | ------------------- | ---------------- |
| **200**     | Successful Response | -                |
| **422**     | Validation Error    | -                |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_one_algorithm**

> AlgorithmActionResponse update_one_algorithm(organisation_id, algorithm_id, algorithm_in)

Update een algoritme.

Sla de nieuwe algoritme-informatie op. Hiermee is het nog niet gepubliceerd.

### Example

- OAuth Authentication (OAuth2AuthorizationCodeBearer):

```python
import amt.algoritmeregister.openapi.v1_0.client.openapi_client
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.algorithm_action_response import AlgorithmActionResponse
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.algorithm_in import AlgorithmIn
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
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.AlgoritmesInOntwikkelingApi(api_client)
    organisation_id = 'organisation_id_example' # str |
    algorithm_id = 'algorithm_id_example' # str |
    algorithm_in = amt.algoritmeregister.openapi.v1_0.client.openapi_client.AlgorithmIn() # AlgorithmIn |

    try:
        # Update een algoritme.
        api_response = api_instance.update_one_algorithm(organisation_id, algorithm_id, algorithm_in)
        print("The response of AlgoritmesInOntwikkelingApi->update_one_algorithm:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AlgoritmesInOntwikkelingApi->update_one_algorithm: %s\n" % e)
```

### Parameters

| Name                | Type                              | Description | Notes |
| ------------------- | --------------------------------- | ----------- | ----- |
| **organisation_id** | **str**                           |             |
| **algorithm_id**    | **str**                           |             |
| **algorithm_in**    | [**AlgorithmIn**](AlgorithmIn.md) |             |

### Return type

[**AlgorithmActionResponse**](AlgorithmActionResponse.md)

### Authorization

[OAuth2AuthorizationCodeBearer](../README.md#OAuth2AuthorizationCodeBearer)

### HTTP request headers

- **Content-Type**: application/json
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
