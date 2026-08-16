from typing import Callable, Dict, List

from collectors.base import Resource


class CollectorManager:
    """
    Manages OCI resource collectors.
    """

    def __init__(self):
        self.collectors: Dict[str, Callable] = {}

    def register(self, service_name: str, collector: Callable):
        """
        Register a collector for a service.
        """
        self.collectors[service_name] = collector

    def collect_all(self, config) -> Dict[str, List[Resource]]:
        """
        Execute all registered collectors.
        """

        resources_by_service = {}

        for service_name, collector in self.collectors.items():

            print(f"Collecting {service_name} resources...")

            try:
                resources = collector(config)

                resources_by_service[service_name] = resources

                print(
                    f"{service_name}: "
                    f"{len(resources)} resources found"
                )

            except Exception as exc:
                print(
                    f"ERROR collecting {service_name}: {exc}"
                )

                resources_by_service[service_name] = []

        return resources_by_service
