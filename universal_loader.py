import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import dropbox
from dropbox.exceptions import AuthError
from dotenv import load_dotenv
load_dotenv()

from enum import Enum

# class syntax
class DataSource(Enum):
    json = 1
    postgres = 2
    dropbox = 3
class DataLoader(ABC):
    """Abstract base class for data loaders"""

    @abstractmethod
    def load_data(self, source: str) -> Any:
        """Load data from the specified source"""
        pass

    @abstractmethod
    def list_sources(self) -> List[str]:
        """List available data sources"""
        pass


class JSONDataLoader(DataLoader):
    """Data loader for JSON files"""

    def __init__(self, base_path: str = "./data"):
        self.base_path = base_path
        if not os.path.exists(base_path):
            os.makedirs(base_path)

    def load_data(self, source: str) -> Any:
        """Load data from JSON file"""
        file_path = os.path.join(self.base_path, source)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file_path}: {e}")

    def list_sources(self) -> List[str]:
        """List all JSON files in the base directory"""
        return [f for f in os.listdir(self.base_path) if f.endswith('.json')]


class PostgreSQLDataLoader(DataLoader):
    """Data loader for PostgreSQL database"""

    def __init__(self, host: str, database: str, user: str, password: str, port: int = 5432):
        self.connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port
        }
        self._test_connection()

    def _get_connection(self):
        """Establish database connection"""
        return psycopg2.connect(**self.connection_params, cursor_factory=RealDictCursor)

    def _test_connection(self):
        """Test database connection"""
        try:
            conn = self._get_connection()
            conn.close()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    def load_data(self, source: str) -> List[Dict]:
        """Load data from a database table or view"""
        query = f"SELECT * FROM {source};"

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise ValueError(f"Error executing query on table {source}: {e}")

    def load_data_with_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Load data using a custom SQL query"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            raise ValueError(f"Error executing custom query: {e}")


    def list_sources(self) -> List[str]:
        """List all tables in the database"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    return [row['table_name'] for row in cursor.fetchall()]
        except Exception as e:
            raise ValueError(f"Error listing tables: {e}")


class DropboxDataLoader(DataLoader):
    """Data loader for Dropbox files"""

    def __init__(self, access_token: str):
        self.dbx = dropbox.Dropbox(access_token)
        self._test_connection()

    def _test_connection(self):
        """Test Dropbox connection"""
        try:
            self.dbx.users_get_current_account()
        except AuthError:
            raise ConnectionError("Invalid Dropbox access token")

    def load_data(self, source: str) -> Any:
        """Load data from Dropbox file"""
        try:
            # Download file metadata and content
            metadata, response = self.dbx.files_download(source)

            # Check if it's a JSON file
            if source.lower().endswith('.json'):
                content = response.content.decode('utf-8')
                return json.loads(content)
            else:
                # Return raw content for non-JSON files
                return response.content

        except dropbox.exceptions.ApiError as e:
            raise FileNotFoundError(f"File not found on Dropbox: {source}. Error: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Dropbox file {source}: {e}")

    def list_sources(self, path: str = "") -> List[str]:
        """List files in Dropbox directory"""
        try:
            result = self.dbx.files_list_folder(path)
            return [entry.name for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)]
        except dropbox.exceptions.ApiError as e:
            raise ValueError(f"Error listing Dropbox directory {path}: {e}")


class UniversalDataLoader:
    """Universal data loader that can handle multiple data sources"""

    def __init__(self):
        self.loaders = {}

    def register_loader(self, name: DataSource, loader: DataLoader):
        """Register a new data loader"""
        self.loaders[name] = loader

    def load_data(self, loader_name: str, source: str) -> Any:
        """Load data using specified loader"""
        if loader_name not in self.loaders:
            raise ValueError(f"Loader '{loader_name}' not registered. Available loaders: {list(self.loaders.keys())}")

        return self.loaders[loader_name].load_data(source)

    def list_sources(self, loader_name: str) -> List[str]:
        """List available sources for specified loader"""
        if loader_name not in self.loaders:
            raise ValueError(f"Loader '{loader_name}' not registered")

        return self.loaders[loader_name].list_sources()

    def get_available_loaders(self) -> List[str]:
        """Get list of registered loaders"""
        return list(self.loaders.keys())


# Example usage
if __name__ == "__main__":
    # Create universal loader
    universal_loader = UniversalDataLoader()
    database_psw = os.environ.get('DB_SECRET')
    database_host = os.environ.get('DB_HOST')

    # # Register JSON loader
    # json_loader = JSONDataLoader("./data")
    # universal_loader.register_loader("json", json_loader)
    # ===========================================================================
    # Example: Register PostgreSQL loader (uncomment and configure)
    postgres_loader = PostgreSQLDataLoader(
        host=database_host,
        database="msdrilling",
        user="msdrilling_user",
        password=database_psw,
        port="5432"
    )

    universal_loader.register_loader(DataSource.postgres, postgres_loader)

    query_ts = """SELECT 
    "PileID",
    MAX("Strokes") as max_strokes,
    MIN("Depth") as min_depth,
    MIN("Time") as first_time
    FROM public.pile_timeseries
    WHERE "JobNumber" = 1650
    GROUP BY "PileID"
    ORDER BY "PileID";"""
    db_ts = postgres_loader.load_data_with_query(query=query_ts)

    # db_data = universal_loader.load_data("postgres", "pile_metadata")
    query = """SELECT "JobNumber", "PileID", "Archived", "Area", "CageColor", "Client", "Comments", "CycleTime", "DelayReason", "DelayTime", "DesignJobNumber", "DesignNotes", "DesignPileID", "Drawing", "DrillEndTime", "DrillNotes", "DrillStartTime", "DrillTime", "Elevation", "Filename", "GeneralContractor", "GroutEndTime", "GroutStartTime", "GroutTime", "GroutVolume", "HasDesign", "HydraulicFlow", "InstallEndTime", "InstallStartTime", "InstallTime", "JobID", "JobName", "Location", "LocationID", "MaxStroke", "MoveDistance", "MoveTime", "MoveVelocity", "Operator", "OverBreak", "PileArea", "PileCap", "PileCode", "PileCutoff", "PileDiameter", "PileLength", "PileStatus", "PileType", "PileVolume", "PowerPackID", "ProductCode", "Project", "PumpCalibration", "PumpID", "RigID", "StartDepth", "TargetPileLength", "TipElevation", "ToolID", "ToolOutTime", "ToolWeight", "TopOfCage", "TopOfCap", "TurntableID", "TurntableWeight", "XEasting", "YNorthing", ST_AsText(coordinates) as coordinates
                        FROM public.pile_metadata; """
    data_ = postgres_loader.load_data_with_query(query=query)

    # =====================================================================
    # Example: Register Dropbox loader (uncomment and configure)
    # dropbox_loader = DropboxDataLoader("your_access_token_here")
    # universal_loader.register_loader("dropbox", dropbox_loader)

    # Example usage with JSON
    try:
        # Create sample JSON file
        sample_data = {"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]}
        with open("./data/sample.json", "w") as f:
            json.dump(sample_data, f)

        # Load data using JSON loader
        data = universal_loader.load_data(DataSource.json, "sample.json")
        print("Loaded data:", data)


        # List available JSON files
        sources = universal_loader.list_sources("json")
        print("Available JSON files:", sources)

    except Exception as e:
        print(f"Error: {e}")