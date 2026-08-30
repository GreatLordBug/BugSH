import requests

def get_nws_alerts_by_ugc(ugc_county_code: str):
    url = f"https://api.weather.gov/alerts/active?zone={ugc_county_code}"
    
    # The NWS API requires a custom User-Agent identifying your application
    headers = {
        "User-Agent": "BugSH Shell Request",
        "Accept": "application/geo+json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            alerts = data.get("features", [])
            
            print(f"Found {len(alerts)} active alert(s) for {ugc_county_code}:\n")
            for alert in alerts:
                props = alert.get("properties", {})
                print(f"Event: {props.get('event')}")
                print(f"Severity: {props.get('severity')}")
                print(f"Headline: {props.get('headline')}")
                print(f"Description: {props.get('description')}\n")
                print("-" * 40)
        else:
            print(f"Error fetching alerts: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")