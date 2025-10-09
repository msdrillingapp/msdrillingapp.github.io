import pandas as pd
import requests
# from convert_locala_coordinates_to_global import convert_easting_northing_to_lonlat_unit

jwt_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6OSwiaWF0IjoxNzU1Njc1MTA3LCJleHAiOjE3ODcyMTExMDd9.mPayiVpvTOjkaUwHe04_a6-CrXuTWIg0gchId2iUlHM'

def get_estimate(job:str):
    # project_url =f'https://piletrack-api-production.pilemetrics.com/api/projects?populate=company&populate=location&populate=configuration.areas&populate=configuration.tolerances&populate=pileTypes.estimate&populate=capConfiguration&populate=image&filters%5B%24and%5D%5B0%5D%5BprojectStatus%5D%5B%24eq%5D=scheduled&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B0%5D%5Btitle%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B1%5D%5Bdescription%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B2%5D%5Blocation%5D%5Bname%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B3%5D%5Blocation%5D%5BformattedAddress%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B4%5D%5Blocation%5D%5Blocality%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B5%5D%5BprojectManager%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B6%5D%5BjobId%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B7%5D%5Bclient%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B8%5D%5BprojectOwner%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B9%5D%5BgeneralContractor%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B10%5D%5BindustrySector%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B11%5D%5BstructuralEngineer%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B12%5D%5BgeotechnicalEngineer%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B13%5D%5BthirdPartyTesting%5D%5B%24containsi%5D=1642&pagination%5Bpage%5D=1&pagination%5BpageSize%5D=20&sort=createdAt%3Adesc'
    # project_url = f'https://piletrack-api-production.pilemetrics.com/api/projects?populate=company&populate=location&populate=configuration.areas&populate=configuration.tolerances&populate=pileTypes.estimate&populate=capConfiguration&populate=image&filters%5B%24and%5D%5B0%5D%5BprojectStatus%5D%5B%24eq%5D=scheduled&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B0%5D%5Btitle%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B1%5D%5Bdescription%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B2%5D%5Blocation%5D%5Bname%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B3%5D%5Blocation%5D%5BformattedAddress%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B4%5D%5Blocation%5D%5Blocality%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B5%5D%5BprojectManager%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B6%5D%5BjobId%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B7%5D%5Bclient%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B8%5D%5BprojectOwner%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B9%5D%5BgeneralContractor%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B10%5D%5BindustrySector%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B11%5D%5BstructuralEngineer%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B12%5D%5BgeotechnicalEngineer%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B13%5D%5BthirdPartyTesting%5D%5B%24containsi%5D={job}&pagination%5Bpage%5D=1&pagination%5BpageSize%5D=20&sort=createdAt%3Adesc'
    project_url = f"https://piletrack-api-production.pilemetrics.com/api/projects?populate=company&populate=location&populate=configuration.areas&populate=configuration.tolerances&populate=pileTypes.estimate&populate=capConfiguration&populate=image&filters%5B%24and%5D%5B0%5D%5BprojectStatus%5D%5B%24eq%5D=scheduled&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B0%5D%5BjobName%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B1%5D%5Bdescription%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B2%5D%5Blocation%5D%5Bname%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B3%5D%5Blocation%5D%5BformattedAddress%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B4%5D%5Blocation%5D%5Blocality%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B5%5D%5BprojectManager%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B6%5D%5BjobNumber%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B7%5D%5Bclient%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B8%5D%5BprojectOwner%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B9%5D%5BgeneralContractor%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B10%5D%5BindustrySector%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B11%5D%5BstructuralEngineer%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B12%5D%5BgeotechnicalEngineer%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B13%5D%5BthirdPartyTesting%5D%5B%24containsi%5D={job}&pagination%5Bpage%5D=1&pagination%5BpageSize%5D=20&sort=createdAt%3Adesc"
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    # Make the GET request
    response = requests.get(project_url, headers=headers)

    data = pd.DataFrame()
    # Check for success
    pileType_list = []
    color_list = []
    dict_estimate = {}
    if response.status_code == 200:
        project_data = response.json()
        pileTypes = project_data['data'][0]['pileTypes']
        location = project_data['data'][0]['location']
        location['JobID'] = job  #project_data['data'][0]['jobId']
        location['documentId'] = project_data['data'][0]['documentId']
        location['client'] = project_data['data'][0]['client']
        location['jobName'] = project_data['data'][0]['jobName']
        location['startDate'] = project_data['data'][0]['startDate']
        location['description'] = project_data['data'][0]['description']
        pageSize  =project_data['meta']['pagination']['pageSize']
        documentID = project_data['data'][0]['documentId']
        df_pileTypes = pd.DataFrame.from_records(pileTypes)
        df_pileTypes.drop(axis=1,columns='id',inplace=True)
        df_pileTypes.rename(columns={'title':'type'},inplace=True)
        try:
            df_schedule = get_pile_schedule(documentID,pageSize)
        except:
            df_schedule =[]

        if len(df_schedule)>0:
            df_schedule = df_schedule.merge(df_pileTypes[['type','productCode','color_rrggbb']], on='type',how='left')
            # eastings = list(df_schedule['easting'].values)
            # northings = list(df_schedule['northing'].values)
            # try:
            #     lat,lon = convert_easting_northing_to_lonlat_unit(location['longitude'],location['latitude'],eastings, northings)
            #     df_schedule['latitude_'] = lat
            #     df_schedule['longitude_'] = lon
            # except:
            #     pass

        for p in pileTypes:
            piletype = p.get('title','')
            pileType_list.append(piletype)
            color_list.append(p.get('color_rrggbb',''))
            dict_estimate[piletype] = p.get('estimate',{})
            try:
                dict_estimate[piletype].update({'colorCode':p.get('color_rrggbb','')})
                dict_estimate[piletype].update({'diameter':p.get('diameter','')})
            except:
                print('issue with pyletype:' + piletype)
                pass
        return dict_estimate,location,df_schedule

    else:
        print(f"Failed to fetch project. Status: {response.status_code}, Message: {response.text}")
        return None


def get_pile_schedule(documentID:str,n_pages):

    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }
    df = pd.DataFrame()
    keep = True
    i = 1
    while keep:
        project_url =f"https://piletrack-api-production.pilemetrics.com/api/piles?filters[project][documentId][$eq]={documentID}&populate=location&populate=asBuilt&sort=pileId:asc&pagination[page]={i}&pagination[pageSize]={n_pages}"
        # Make the GET request
        response = requests.get(project_url, headers=headers)
        if response.status_code == 200:
            project_data = response.json()
            tmp = pd.DataFrame.from_records(project_data['data'])
            df = pd.concat([df,tmp],ignore_index=True)
            if len(tmp)==0:
                keep = False
            i += 1
        else:
            print(f"Failed to fetch project. Status: {response.status_code}, Message: {response.text}")
            keep = False
            break

    if len(df)>0:
        df = df.drop('drawingMediaUID', axis=1)
        try:
            df_expanded = pd.json_normalize(df['location'])
            df_expanded.drop('id',axis=1,inplace=True)
            df = pd.concat([df.drop('location', axis=1), df_expanded], axis=1)
            df = df.dropna(axis=1, how='all')
        except:
            df['longitude'] = None
            df['latitude'] = None

    return df

if __name__ == "__main__":
    for job in ['1653']:
        estimates,location,df_schedule = get_estimate(job)
        # df_schedule.to_csv('C:\Inventzia_Dennis\Estimates\pile_schedule'+job+'.csv')
        print()