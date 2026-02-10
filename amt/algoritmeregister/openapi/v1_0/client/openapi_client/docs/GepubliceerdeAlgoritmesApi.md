# amt.algoritmeregister.openapi.v1_0.client.openapi_client.GepubliceerdeAlgoritmesApi

All URIs are relative to _/aanleverapi/v1_0_

| Method                                                                                       | HTTP request                                                                 | Description                                        |
| -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------- |
| [**get_one_published_algorithm**](GepubliceerdeAlgoritmesApi.md#get_one_published_algorithm) | **GET** /organizations/{organisation_id}/published-algorithms/{algorithm_id} | Haal de gepubliceerde versie van één algoritme op. |

# **get_one_published_algorithm**

> AnyOfTheAlgorithmStandards get_one_published_algorithm(organisation_id, algorithm_id)

Haal de gepubliceerde versie van één algoritme op.

Verkrijg de gepubliceerde versie van één algoritme.

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
    api_instance = amt.algoritmeregister.openapi.v1_0.client.openapi_client.GepubliceerdeAlgoritmesApi(api_client)
    organisation_id = 'organisation_id_example' # str |
    algorithm_id = 'algorithm_id_example' # str |

    try:
        # Haal de gepubliceerde versie van één algoritme op.
        api_response = api_instance.get_one_published_algorithm(organisation_id, algorithm_id)
        print("The response of GepubliceerdeAlgoritmesApi->get_one_published_algorithm:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GepubliceerdeAlgoritmesApi->get_one_published_algorithm: %s\n" % e)
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
