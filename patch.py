import importlib.util
from pathlib import Path

# 1. Find the package path WITHOUT executing/importing its code
spec = importlib.util.find_spec("fastapi_mail")

if spec and spec.submodule_search_locations:
    package_dir = Path(spec.submodule_search_locations[0])
    config_path = package_dir / "config.py"
    
    # 2. Read, patch, and save the file
    if config_path.exists():
        content = config_path.read_text()
        
        if "from pydantic import SecretStr" not in content:
            # Prepend the missing import to the top of the file
            patched_content = "from pydantic import SecretStr\n" + content
            config_path.write_text(patched_content)
            print("Successfully patched fastapi-mail config.py!")
        else:
            print("Patch already applied or no longer needed.")
    else:
        print("Error: Could not find config.py inside fastapi-mail.")
else:
    print("Error: fastapi-mail is not installed.")