from typing import Any, Literal, Union

from openqa_client.client import OpenQA_Client


Method = Union[
    Literal["GET"], Literal["POST"], Literal["PUT"], Literal["DELETE"]
]


class NoWaitClient(OpenQA_Client):
    """
    Custom OpenQA_Client that uses no retries and zero wait times by default.
    """

    def openqa_request(
        self,
        method: Method,
        path: str,
        params: Any = None,
        retries: int = 0,
        wait: int = 0,
        data: Any = None,
    ):
        if (
            params is not None
            and not isinstance(params, dict)
            and not isinstance(params, str)
        ):
            params = params.__dict__
        if (
            data is not None
            and not isinstance(data, dict)
            and not isinstance(data, str)
        ):
            data = data.__dict__

        return super().openqa_request(
            method, path, params=params, retries=retries, wait=wait, data=data
        )
