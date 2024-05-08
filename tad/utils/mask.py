from typing import Any


class DataMasker:
    def __init__(self, mask_value: str = "***MASKED***", mask_keywords: list[str] | None = None):
        if mask_keywords is None:
            mask_keywords = []
        self.mask_value = mask_value

        # default keywords to mask
        self.keywords: list[str] = ["password", "secret", "database_uri"]
        self.keywords.extend(mask_keywords or [])

    def mask_data(  # noqa: C901
        self, data: str | list[Any] | dict[Any, Any] | set[Any]
    ) -> str | list[Any] | dict[Any, Any] | set[Any]:
        if isinstance(data, dict):
            masked_dict: dict[str | int, str | int] = {}
            for key, value in data.items():
                if isinstance(key, str):
                    for keyword in self.keywords:
                        if keyword in key.lower():
                            masked_dict[key] = self.mask_value
                            break
                    else:
                        masked_dict[key] = value
                else:
                    masked_dict[key] = value
            return masked_dict

        elif isinstance(data, list):
            masked_list: list[str | int] = []
            item: str | int
            for item in data:
                if isinstance(item, str):
                    for keyword in self.keywords:
                        if keyword in item.lower():
                            masked_list.append(self.mask_value)
                            break
                    else:
                        masked_list.append(item)
                else:
                    masked_list.append(item)

            return masked_list
        elif isinstance(data, set):
            masked_set: set[str | int] = set()

            item: str | int
            for item in data:
                if isinstance(item, str):
                    for keyword in self.keywords:
                        if keyword in item.lower():
                            masked_set.add(self.mask_value)
                            break
                    else:
                        masked_set.add(item)
                else:
                    masked_set.add(item)
            return masked_set
        else:
            for keyword in self.keywords:
                if keyword in data.lower():
                    return self.mask_value
            return data
