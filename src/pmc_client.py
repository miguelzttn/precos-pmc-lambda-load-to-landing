from io import BytesIO
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import urllib3
import logging

class CliqueEconomiaClient:

    CURRENT_URL = "https://mid-dadosabertos.curitiba.pr.gov.br/CliqueEconomia/"
    OLD_URL = "https://dadosabertos.c3sl.ufpr.br/curitiba/CliqueEconomia/"

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        return 
    
    def _handle_get(self, url: str, attempt: int = 1) -> urllib3.response.HTTPResponse | None:
        
        self.logger.debug(f"Making GET request to {url}")

        http = urllib3.PoolManager(timeout=urllib3.Timeout(connect=2.0, read=30.0))

        for attempt_count in range(attempt):
            self.logger.debug(f"Attempt {attempt_count + 1} of {attempt} for URL: {url}")

            try:
                response = http.request('GET', url)
                
                if response.status == 404:
                    self.logger.info(f"File not found at {url} (404).")
                    continue

                if response.status >= 400:
                    self.logger.error(f"HTTP error {response.status} for URL: {url}")
                    continue
                
                return response

            except urllib3.exceptions.HTTPError as e:
                self.logger.error(f"Error during GET request to {url}: {e}")
            
            except Exception as e:
                self.logger.error(f"Unexpected error during GET request to {url}: {e}")
        
        return None


    def _transform_response_into_stream(self, response: urllib3.response.HTTPResponse) -> BytesIO | None:
        
        if not isinstance(response, urllib3.response.HTTPResponse):
            self.logger.error("Invalid response type received.")
            return None
        
        if response.data is None:
            self.logger.error("No response to transform into stream.")
            return None
        
        return BytesIO(response.data)

    def _mount_filenames(self, date_reference: datetime) -> list[str]:
        
        # Grant date reference is >= 2022-06-22 (db beggining)
        if date_reference < datetime(2022, 6, 22).replace(tzinfo=ZoneInfo("America/Sao_Paulo")):
            raise ValueError("Date reference must be on or after 2022-06-22")

        date_str = date_reference.strftime("%Y-%m-%d")
        filenames = [
            f"{date_str}_Clique_Economia_-_Produto_-_Dicionario_de_Dados.csv",
            f"{date_str}_Clique_Economia_-_Produto_-_Base_de_Dados.csv",
            f"{date_str}_Clique_Economia_-_Dicionario_de_Dados.csv",
            f"{date_str}_Clique_Economia_-_Cotacoes_-_Base_de_Dados.csv"
        ]

        # The database was incremental until 2023-07-18, so on that date we have to get the full base file
        if date_reference == datetime(2023, 7, 18).replace(tzinfo=ZoneInfo("America/Sao_Paulo")):
            filenames.append(f"{date_str}_Clique_Economia_-_Base_de_Dados.csv")

        return filenames

    def get_file_stream(self, filename: str, date_reference: datetime) -> BytesIO | None:
        """
        Attempts to retrieve a file stream from multiple URLs.
        This method tries to download a file from a list of predefined URLs (current and old).
        It iterates through the URLs until it successfully retrieves the file or exhausts all options.
        
        :param filename: The name of the file to retrieve from the remote server
        
        :return: A BytesIO stream containing the file content if found, None if the file 
                 could not be retrieved from any of the available URLs
        
        :raises: No exceptions are raised directly, but underlying methods may raise exceptions
        
        Example:
            >>> wrapper = CliqueEconomiaClient()
            >>> stream = wrapper.get_file_stream("	2022-06-23_Clique_Economia_-_Base_de_Dados.csv")
            >>> if stream:
            ...     # Process the stream
            ...     content = stream.read()

        """
        
        urls_to_try = []

        today = datetime.now(tz=ZoneInfo("America/Sao_Paulo")) 
        if date_reference >= today - timedelta(days=(12 * 30)):
            urls_to_try.append(f"{self.CURRENT_URL}{filename}")

        if date_reference < today - timedelta(days=(10 * 30)):
            urls_to_try.append(f"{self.OLD_URL}{filename}")

        for url in urls_to_try:
            response = self._handle_get(url)

            if isinstance(response, type(None)):
                self.logger.info(f"File '{filename}' not found at {url}, trying next URL if available.")
                continue
            
            stream = self._transform_response_into_stream(response)
            return stream
        
        return None
    
    def get_files_by_date(self, date_reference: datetime) -> dict[str, BytesIO | None]:
        """
        
        Retrieves multiple PMC files for a specific date from available sources.
        
        This method attempts to download files corresponding to the provided date reference
        by first generating the appropriate filenames and then retrieving each file's content
        as a stream. Files that cannot be retrieved are logged as warnings and excluded from
        the result.
            date_reference (datetime): The reference date for which to retrieve PMC files.
                This date is used to generate the appropriate filenames based on the PMC
                naming convention.
            dict[str, BytesIO | None]: A dictionary where keys are filenames and values are
                BytesIO stream objects containing the file data. Only successfully retrieved
                files are included in the dictionary. Returns an empty dictionary if no files
                could be retrieved.

        :param date_reference: The reference date for which to retrieve PMC files.
        :return: A dictionary where keys are filenames and values are BytesIO stream objects
                 containing the file data. Only successfully retrieved files are included.

        Example:
            >>> date = datetime(2024, 1, 15)
            >>> files = wrapper.get_files_by_date(date)
            >>> for filename, stream in files.items():
            ...     print(f"Retrieved: {filename}")
        
        Note:
            - Files that fail to download are logged at WARNING level and skipped
            - The method relies on _mount_filenames() to generate the list of expected files
            - Each file is retrieved individually using get_file_stream()
        
        """
        
        filenames = self._mount_filenames(date_reference=date_reference)
        file_streams = {}

        for filename in filenames:
            stream = self.get_file_stream(filename=filename, date_reference=date_reference)
            
            if stream is None:
                self.logger.warning(f"File '{filename}' could not be retrieved from any source.")
                continue

            file_streams[filename] = stream
        
        self.logger.warning(f"Number of files retrieved: {len(file_streams)}")

        return file_streams
    
