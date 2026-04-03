import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

def get_metadata():
    root = Path(__file__).resolve().parents[1]
    pyproject_path = root / "packages" / "merger-cli" / "pyproject.toml"
    
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
        
    project = pyproject["project"]
    version = project["version"]
    description = project.get("description", "")
    homepage = project.get("urls", {}).get("Homepage", "")
    
    # MSI Version mapping: X.Y.Z-type.A -> X.Y.Z.A
    msi_version = version
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-[a-zA-Z]+\.(\d+))?$', version)
    if match:
        major, minor, patch, build = match.groups()
        msi_version = f"{major}.{minor}.{patch}.{build or 0}"
        
    return {
        "version": version,
        "msi_version": msi_version,
        "description": description,
        "homepage": homepage
    }

def text_to_rtf(text):
    rtf = r'{\rtf1\ansi\deff0{\fonttbl{\f0 Arial;}}\f0\fs20 '
    text = text.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
    text = text.replace('\n', '\\par\n')
    rtf += text + '}'
    return rtf

def generate_license_rtf():
    root = Path(__file__).resolve().parents[1]
    license_path = root / "LICENSE"
    if license_path.exists():
        with open(license_path, "r", encoding="utf-8") as f:
            license_text = f.read()
        rtf_content = text_to_rtf(license_text)
        rtf_path = root / "packaging" / "license.rtf"
        with open(rtf_path, "w", encoding="ascii", errors="ignore") as f:
            f.write(rtf_content)
        return rtf_path
    return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rtf":
        res = generate_license_rtf()
        if res:
            print(res)
    else:
        meta = get_metadata()
        for k, v in meta.items():
            print(f"{k}={v}")
