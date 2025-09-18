from abc import ABC
from typing import Any, Dict, List


class DataProcessing(ABC):
    """
    Abstract base class for data processing.
    This class provides a template for processing data and retrieving it in JSON format.
    Subclasses must implement the `__process_data__` method to define specific data processing logic.
    Attributes:
        __data__ (List[Dict[str, Any]]): Internal storage for processed data.
    Methods:
        get_json() -> List[Dict[str, Any]]:
            Returns the processed data in JSON format. If the data has not been processed yet,
            it calls the `__process_data__` method to process and store the data.
        __process_data__():
            Abstract method that must be implemented by subclasses to process data.
            Raises NotImplementedError if not overridden.
    """

    def __init__(self):
        self.__data__: List[Dict[str, Any]] = None

    def get_json(self) -> List[Dict[str, Any]]:
        """
        Returns the processed data as a list of JSON-compatible dictionaries.

        If the internal data has not been processed yet, it processes the data first.

        Returns:
            List[Dict[str, Any]]: The processed data in JSON format.
        """
        if self.__data__ is None:
            self.__data__ = self.__process_data__()
        return self.__data__

    def __process_data__(self):
        raise NotImplementedError("Subclasses must implement this method")
