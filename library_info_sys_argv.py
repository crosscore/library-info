import requests
import sys

def get_package_size(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        releases = data['releases']
        latest_version = data['info']['version']
        for release in releases[latest_version]:
            if release['packagetype'] == 'sdist':
                return release['size']
    return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <package_name>")
        sys.exit(1)

    package_name = sys.argv[1]
    size = get_package_size(package_name)
    if size:
        print(f"The size of {package_name} is {size} bytes")
    else:
        print(f"Could not find size information for {package_name}")
