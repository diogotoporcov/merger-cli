import re
import sys
from pathlib import Path

import tomli
from jinja2 import Template


def parse_version(version_str):
    # Mapping X.Y.Z-type.A to W.X.Y.Z where W=X, X=Y, Y=Z, Z=A
    # If no suffix, Z=0
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-[a-zA-Z]+\.(\d+))?$', version_str)
    if match:
        major, minor, patch, build = match.groups()
        if build is None:
            build = "0"
        return f"{major}.{minor}.{patch}.{build}"
    
    # Fallback for other formats if any
    return version_str

def main():
    root = Path(__file__).resolve().parents[1]
    pyproject_path = root / "packages" / "merger-cli" / "pyproject.toml"
    
    if not pyproject_path.exists():
        print(f"Error: {pyproject_path} not found.")
        sys.exit(1)

    with open(pyproject_path, "rb") as f:
        pyproject = tomli.load(f)
        
    version = pyproject["project"]["version"]
    msi_version = parse_version(version)
    
    print(f"Original version: {version}")
    print(f"MSI version: {msi_version}")
    
    # Template rendering
    templates = [
        ("packaging/merger.wxs.j2", "packaging/merger.wxs"),
    ]
    
    errors = 0
    for t_in, t_out in templates:
        template_path = root / t_in
        if not template_path.exists():
            print(f"Error: Template not found at {template_path}")
            errors += 1
            continue

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
            
        template = Template(template_content)
        rendered_content = template.render(
            version=version,
            msi_version=msi_version
        )
        
        output_path = root / t_out
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_content)
            
        print(f"Generated {output_path}")

    if errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
