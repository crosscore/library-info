import requests
import time
import subprocess
from typing import List, Tuple
from requests.exceptions import RequestException

class RateLimitException(Exception):
    pass

def get_installed_packages() -> List[str]:
    result = subprocess.run(["pip", "list"], capture_output=True, text=True)
    lines = result.stdout.split('\n')[2:]  # Skip the header lines
    return [line.split()[0] for line in lines if line.strip()]

def get_package_size(package_name: str) -> int:
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        releases = data['releases']
        latest_version = data['info']['version']
        for release in releases[latest_version]:
            if release['packagetype'] == 'sdist':
                return release['size']
    elif response.status_code == 429:  # Too Many Requests
        raise RateLimitException("Rate limit exceeded")
    return 0

def get_multiple_package_sizes(package_list: List[str], delay: float = 1.0, retry_delay: float = 60.0, max_retries: int = 3) -> List[Tuple[str, int]]:
    package_sizes = []
    for package in package_list:
        retries = 0
        while retries < max_retries:
            try:
                size = get_package_size(package)
                package_sizes.append((package, size))
                print(f"{package}: {format_size(size)}")
                time.sleep(delay)  # Wait before next request
                break
            except RateLimitException:
                retries += 1
                if retries < max_retries:
                    print(f"Rate limit hit. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to retrieve size for {package} after {max_retries} attempts")
            except RequestException as e:
                print(f"Error retrieving size for {package}: {e}")
                break
    return sorted(package_sizes, key=lambda x: x[1], reverse=True)

def format_size(size_in_bytes: int) -> str:
    kb_size = size_in_bytes / 1024
    mb_size = kb_size / 1024
    gb_size = mb_size / 1024
    if gb_size >= 1:
        return f"{size_in_bytes:,} bytes ({gb_size:.2f} GB)"
    elif mb_size >= 1:
        return f"{size_in_bytes:,} bytes ({mb_size:.2f} MB)"
    else:
        return f"{size_in_bytes:,} bytes ({kb_size:.2f} KB)"

def main():
    # インストールされているパッケージのリストを取得
    libraries = get_installed_packages()
    print(f"Found {len(libraries)} installed packages.")

    delay_between_requests = 0.5 # 各リクエスト間の待機時間（秒）
    retry_delay = 30.0  # レート制限時の待機時間（秒）
    max_retries = 3  # 最大リトライ回数

    sorted_sizes = get_multiple_package_sizes(libraries, delay_between_requests, retry_delay, max_retries)

    print("\n--- Package sizes in descending order ---")
    total_size = 0
    for package, size in sorted_sizes:
        print(f"{package}: {format_size(size)}")
        total_size += size

    print(f"\nTotal size of all packages: {format_size(total_size)}")

if __name__ == "__main__":
    main()
