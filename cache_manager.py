import pickle
from functools import lru_cache
import pandas as pd
import os
from collections import OrderedDict

class ChartDataCache:
    def __init__(self, result_MWD_data,reload:bool=False):
        self.result_MWD = result_MWD_data
        self.reload = reload
        self.date_availability = self._load_or_compute_dates()
        self.preprocessed_data = self._precompute_resampled_data()

    def _resample(self, df,resample_unit='1T'):
        """Resample data to resample_unit intervals using appropriate aggregation"""
        if df.empty:
            return df

        # Set time as index for resampling
        df_resampled = df.set_index('Time').copy()

        # Resample to 1-minute intervals with different aggregation methods
        resampled = pd.DataFrame()

        # For Depth - use last value (most recent measurement)
        resampled['Depth'] = df_resampled['Depth'].resample(resample_unit).last()

        # For Strokes - use mean (average over the minute)
        resampled['Strokes'] = df_resampled['Strokes'].resample(resample_unit).mean()

        # For Torque - use mean (average over the minute)
        resampled['Torque'] = df_resampled['Torque'].resample(resample_unit).mean()

        # Keep PileID - use first value
        resampled['PileID'] = df_resampled['PileID'].resample(resample_unit).first()

        # Reset index and drop NaN values
        resampled = resampled.reset_index().dropna()

        return resampled


    def _precompute_resampled_data(self):
        """Precompute 1-minute resampled data for all jobs"""
        cache_file = 'data/preprocessed_chart_data.pkl'
        if not self.reload:
            try:
                if os.path.exists(cache_file):
                    with open(cache_file, 'rb') as f:
                        print("Loading precomputed resampled data from cache...")
                        return pickle.load(f)
            except:
                self.reload = True
        if self.reload:
            print("Precomputing resampled data...")
            preprocessed_data = {}

            for job in self.result_MWD.keys():
                properties_df = self.result_MWD[job][0].copy()
                pile_data = self.result_MWD[job][1].copy()
                pile_data = pile_data[job]
                # Pre-filter properties
                filtered_props = properties_df[
                    (properties_df['PileCode'] == 'Production Pile') &
                    (properties_df['PileStatus'] == 'Complete')
                    ].copy()

                # Precompute piles by rig
                piles_by_rig = {
                    r: list(filtered_props[filtered_props['RigID'] == r]['PileID'].values)
                    for r in filtered_props['RigID'].unique()
                }

                # Preprocess and resample all pile data for this job
                job_preprocessed = {
                    'piles_by_rig': piles_by_rig,
                    'precomputed_days': {}
                }

                # First pass: collect all pile data and their start times
                date_pile_times = {}  # {date: {pile_id: start_time}}

                for pile_id, days_data in pile_data.items():
                    for date, day_data in days_data.items():
                        if date not in date_pile_times:
                            date_pile_times[date] = {}

                        # Convert to DataFrame and process time
                        try:
                            df = pd.DataFrame(day_data)
                        except:
                            continue


                        df['Time'] = pd.to_datetime(df['Time'], format='%d.%m.%Y %H:%M:%S')

                        # Get the start time (minimum time) for this pile on this date
                        start_time = df['Time'].min()
                        date_pile_times[date][pile_id] = start_time

                # Second pass: process and store data, then sort by start time
                for pile_id, days_data in pile_data.items():
                    for date, day_data in days_data.items():
                        if date not in job_preprocessed['precomputed_days']:
                            job_preprocessed['precomputed_days'][date] = {}

                        # Convert to DataFrame and process time
                        try:
                            df = pd.DataFrame(day_data)
                        except:
                            continue
                        df['Time'] = pd.to_datetime(df['Time'], format='%d.%m.%Y %H:%M:%S')
                        df.sort_values('Time', inplace=True)
                        df['PileID'] = pile_id

                        # RESAMPLE TO 1-MINUTE INTERVALS
                        resampled_df = self._resample(df, resample_unit='30s')
                        job_preprocessed['precomputed_days'][date][pile_id] = resampled_df


                # Sort each date's piles by their start time using OrderedDict
                for date in job_preprocessed['precomputed_days']:
                    # Get piles for this date and sort them by start time
                    piles = job_preprocessed['precomputed_days'][date]
                    sorted_pile_ids = sorted(
                        piles.keys(),
                        key=lambda pid: date_pile_times[date].get(pid, pd.Timestamp.max)
                    )

                    # Create an ordered dictionary
                    sorted_piles = OrderedDict()
                    for pile_id in sorted_pile_ids:
                        sorted_piles[pile_id] = piles[pile_id]

                    job_preprocessed['precomputed_days'][date] = sorted_piles

                preprocessed_data[job] = job_preprocessed
            # Save to cache
            os.makedirs('data', exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(preprocessed_data, f)

            print("Resampled data precomputation complete!")
            return preprocessed_data

    def _precompute_all_data(self):
        """Precompute and cache all data processing for lightning-fast access"""
        cache_file = 'data/preprocessed_chart_data.pkl'

        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except:
            pass

        # Compute if cache doesn't exist or is corrupted
        preprocessed_data = {}

        for job in self.result_MWD.keys():
            properties_df = self.result_MWD[job][0].copy()
            pile_data = self.result_MWD[job][1].copy()
            pile_data = pile_data[job]
            # Pre-filter properties
            filtered_props = properties_df[
                (properties_df['PileCode'] == 'Production Pile') &
                (properties_df['PileStatus'] == 'Complete')
                ].copy()

            # Precompute piles by rig
            piles_by_rig = {
                r: list(filtered_props[filtered_props['RigID'] == r]['PileID'].values)
                for r in filtered_props['RigID'].unique()
            }

            # Preprocess all pile data for this job
            job_preprocessed = {
                'piles_by_rig': piles_by_rig,
                'precomputed_days': {}
            }

            # Preprocess data for each date and pile
            for pile_id, days_data in pile_data.items():
                for date, day_data in days_data.items():
                    if date not in job_preprocessed['precomputed_days']:
                        job_preprocessed['precomputed_days'][date] = {}

                    # Preprocess the data once
                    df = pd.DataFrame(day_data)
                    df['Time'] = pd.to_datetime(df['Time'], format='%d.%m.%Y %H:%M:%S')
                    df.sort_values('Time', inplace=True)
                    df['PileID'] = pile_id

                    job_preprocessed['precomputed_days'][date][pile_id] = df

            preprocessed_data[job] = job_preprocessed

        # Save to cache
        os.makedirs('data', exist_ok=True)
        with open(cache_file, 'wb') as f:
            pickle.dump(preprocessed_data, f)

        return preprocessed_data

    @lru_cache(maxsize=100)
    def get_piles_by_rig(self, job_number):
        job_str = str(job_number)
        if job_str not in self.result_MWD:
            return {}

        properties_df = self.result_MWD[job_str][0].copy()
        properties_df = properties_df[(properties_df['PileCode'] == 'Production Pile') &
                                      (properties_df['PileStatus'] == 'Complete')]
        return {
            r: list(properties_df[properties_df['RigID'] == r]['PileID'].values)
            for r in properties_df['RigID'].unique()
        }

    def _precompute_date_availability(self):
        date_availability = {}
        for job in self.result_MWD.keys():
            # properties = self.result_MWD[job][0].copy()
            pile_data = self.result_MWD[job][1].copy()
            pile_data =pile_data[job]
            available_dates = set()
            for pile_id, days_data in pile_data.items():
                available_dates.update(days_data.keys())
            date_availability[job] = available_dates

        # Create directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        with open('data/date_availability.pkl', 'wb') as f:
            pickle.dump(date_availability, f)

        return date_availability

    def _load_or_compute_dates(self):
        if self.reload:
            self._precompute_date_availability()
        else:
            try:
                with open('data/date_availability.pkl', 'rb') as f:
                    return pickle.load(f)
            except FileNotFoundError:
                return self._precompute_date_availability()

    def is_date_available(self, job, date):
        return date in self.date_availability.get(str(job), set())

    def get_job_data(self, job_number):
        job_str = str(job_number)
        propertie,pile_data,_ = self.result_MWD.get(job_str, (None, {}))
        return propertie,pile_data

    def get_pile_data_for_date(self, job_number, pile_id, date):
        job_str = str(job_number)
        if job_str not in self.result_MWD:
            return None

        pile_data = self.result_MWD[job_str][1][job_str].get(pile_id, {})
        return pile_data.get(date)

    def find_keys_for_value(self,dictionary, target_value):
        return [key for key, value_list in dictionary.items() if target_value in value_list]
    def get_precomputed_rig_data(self, job_number, selected_date):
        """Get precomputed 1-minute resampled data with individual pile tracking"""
        job_str = str(job_number)

        if job_str not in self.preprocessed_data:
            return None

        job_data = self.preprocessed_data[job_str]

        if selected_date not in job_data['precomputed_days']:
            return None

        # result = {
        #     'piles_by_rig': job_data['piles_by_rig'],
        #     'rig_pile_dataframes': {}  # rig_id -> dict of {pile_id: dataframe}
        # }
        ordered_piles = list(job_data['precomputed_days'][selected_date].keys())
        mydic = {}
        mydic_df = {}
        for pileid in ordered_piles:
            rigid = next((key for key, lst in job_data['piles_by_rig'].items() if pileid in lst), None)
            # rigid = self.find_keys_for_value(job_data['piles_by_rig'],pileid)
            if rigid in mydic:
                mydic[rigid].append(pileid)
                mydic_df[rigid].append({pileid:job_data['precomputed_days'][selected_date][pileid]})
            else:
                mydic[rigid] = [pileid]
                mydic_df[rigid] = [{pileid:job_data['precomputed_days'][selected_date][pileid]}]

        result = {
            'piles_by_rig': mydic,
            'rig_pile_dataframes': mydic_df  # rig_id -> dict of {pile_id: dataframe}
        }
        # for rig_id, pile_ids in job_data['piles_by_rig'].items():
        #     pile_data_dict = {}
        #     for pile_id in pile_ids:
        #         if pile_id in job_data['precomputed_days'][selected_date]:
        #             df = job_data['precomputed_days'][selected_date][pile_id]
        #             if not df.empty:
        #                 pile_data_dict[pile_id] = df


            # if pile_data_dict:
            #     result['rig_pile_dataframes'][rig_id] = pile_data_dict

        return result