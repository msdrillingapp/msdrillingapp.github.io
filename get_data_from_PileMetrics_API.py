import pandas as pd
import requests

jwt_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6OSwiaWF0IjoxNzU1Njc1MTA3LCJleHAiOjE3ODcyMTExMDd9.mPayiVpvTOjkaUwHe04_a6-CrXuTWIg0gchId2iUlHM'

def get_estimate(job:str):
    # project_url =f'https://piletrack-api-production.pilemetrics.com/api/projects?populate=company&populate=location&populate=configuration.areas&populate=configuration.tolerances&populate=pileTypes.estimate&populate=capConfiguration&populate=image&filters%5B%24and%5D%5B0%5D%5BprojectStatus%5D%5B%24eq%5D=scheduled&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B0%5D%5Btitle%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B1%5D%5Bdescription%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B2%5D%5Blocation%5D%5Bname%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B3%5D%5Blocation%5D%5BformattedAddress%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B4%5D%5Blocation%5D%5Blocality%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B5%5D%5BprojectManager%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B6%5D%5BjobId%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B7%5D%5Bclient%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B8%5D%5BprojectOwner%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B9%5D%5BgeneralContractor%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B10%5D%5BindustrySector%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B11%5D%5BstructuralEngineer%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B12%5D%5BgeotechnicalEngineer%5D%5B%24containsi%5D=1642&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B13%5D%5BthirdPartyTesting%5D%5B%24containsi%5D=1642&pagination%5Bpage%5D=1&pagination%5BpageSize%5D=20&sort=createdAt%3Adesc'
    project_url =f'https://piletrack-api-production.pilemetrics.com/api/projects?populate=company&populate=location&populate=configuration.areas&populate=configuration.tolerances&populate=pileTypes.estimate&populate=capConfiguration&populate=image&filters%5B%24and%5D%5B0%5D%5BprojectStatus%5D%5B%24eq%5D=scheduled&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B0%5D%5Btitle%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B1%5D%5Bdescription%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B2%5D%5Blocation%5D%5Bname%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B3%5D%5Blocation%5D%5BformattedAddress%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B4%5D%5Blocation%5D%5Blocality%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B5%5D%5BprojectManager%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B6%5D%5BjobId%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B7%5D%5Bclient%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B8%5D%5BprojectOwner%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B9%5D%5BgeneralContractor%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B10%5D%5BindustrySector%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B11%5D%5BstructuralEngineer%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B12%5D%5BgeotechnicalEngineer%5D%5B%24containsi%5D={job}&filters%5B%24and%5D%5B1%5D%5B%24or%5D%5B13%5D%5BthirdPartyTesting%5D%5B%24containsi%5D={job}&pagination%5Bpage%5D=1&pagination%5BpageSize%5D=20&sort=createdAt%3Adesc'

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
        location['JobID'] = job #project_data['data'][0]['jobId']
        location['documentId'] = project_data['data'][0]['documentId']
        location['client'] = project_data['data'][0]['client']
        location['title'] = project_data['data'][0]['title']
        location['startDate'] = project_data['data'][0]['startDate']

        for p in pileTypes:
            piletype = p.get('title','')
            pileType_list.append(piletype)
            color_list.append(p.get('color_rrggbb',''))
            dict_estimate[piletype] = p.get('estimate',{})
            dict_estimate[piletype].update({'colorCode':p.get('color_rrggbb','')})
            dict_estimate[piletype].update({'diameter':p.get('diameter','')})
        return dict_estimate,location


    else:
        print(f"Failed to fetch project. Status: {response.status_code}, Message: {response.text}")
        return None


if __name__ == "__main__":
    estimates,location = get_estimate('1633')
    print()