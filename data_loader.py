import pandas as pd
import os
from functions import load_geojson_data
from Job import JobManager
from get_data_from_PileMetrics_API import get_estimate
from cache_manager import ChartDataCache


# Simple singleton implementation
class DataManager:
    _instance = None
    _data = None
    _is_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def load_data(self):
        """Load data if not already loaded"""
        if not self._is_loaded:
            print("Loading data for the first time...")
            try:
                ALL_JOBS = ['1640', '1633',  '1641','1642','1604'] #, '1648'
                # Call your data loading function
                result_MWD, results_CPT = load_geojson_data(ALL_JOBS, reload=False)
                my_jobs = JobManager()
                for jobID, v in result_MWD.items():
                    estimates, location = get_estimate(jobID)
                    my_job = my_jobs.add_job(location)
                    my_job.add_estimates(estimates)
                    # my_job.add_pile_schedule()
                cache_manager = ChartDataCache(result_MWD)

                self._data = {
                    'result_MWD': result_MWD,
                    'results_CPT': results_CPT,
                    'my_jobs': my_jobs,
                    'cache_manager': cache_manager
                }

                self._is_loaded = True
                print(f"Data loaded successfully: {len(result_MWD)} jobs")
            except Exception as e:
                print(f"Error loading data: {e}")
                self._data = {'result_MWD': {}, 'results_CPT': {}, 'my_jobs': None,'cache_manager':None}
                self._is_loaded = True
        return self._data

    def get_data(self):
        """Get data - returns empty dict if not loaded yet"""
        if self._is_loaded:
            return self._data
        else:
            return  {'result_MWD': {}, 'results_CPT': {}, 'my_jobs': None,'cache_manager':None}


# Create global instance
data_manager = DataManager()


def set_cache(cache_instance):
    # For compatibility, not used
    pass


def load_all_data():
    """Load data (forces load if not loaded)"""
    return data_manager.load_data()


def get_data():
    """Get data without forcing load"""
    return data_manager.get_data()


def ensure_data_loaded():
    """Ensure data is loaded, then return it"""
    return data_manager.load_data()


def get_job_data(job_id):
    data = ensure_data_loaded()
    return data['result_MWD'].get(job_id, None)


def get_all_job_ids():
    data = ensure_data_loaded()
    return list(data['result_MWD'].keys())



