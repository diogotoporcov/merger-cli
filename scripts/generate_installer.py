import argparse
import re
import sys
from pathlib import Path

import tomli
from jinja2 import Template


def parse_version(version_str):
    # Map X.Y.Z-type.A to W.X.Y.Z (where W=X, X=Y, Y=Z, Z=A).
    # If no suffix is present, Z defaults to 0.
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-[a-zA-Z]+\.(\d+))?$', version_str)
    if match:
        major, minor, patch, build = match.groups()
        if build is None:
            build = "0"
        return f"{major}.{minor}.{patch}.{build}"
    
    # Fallback for other formats if any
    return version_str

def main():
    parser = argparse.ArgumentParser(description="Generate installer source files from templates.")
    parser.add_argument("--sha256", help="SHA256 hash for the Homebrew formula.")
    parser.add_argument("--tag-name", help="Tag name for the Homebrew formula.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    pyproject_path = root / "packages" / "merger-cli" / "pyproject.toml"
    
    if not pyproject_path.exists():
        print(f"Error: {pyproject_path} not found.")
        sys.exit(1)

    with open(pyproject_path, "rb") as f:
        pyproject = tomli.load(f)
        
    project = pyproject["project"]
    version = project["version"]
    description = project.get("description", "")
    homepage = project.get("urls", {}).get("Homepage", "")
    license_name = "GPL-3.0-or-later"
    # Currently defaults to GPL-3.0-or-later for installer templates.
    
    msi_version = parse_version(version)
    
    tag_name = args.tag_name or f"v{version}"
    sha256 = args.sha256 or "REPLACE_WITH_ACTUAL_SHA256"

    print(f"Original version: {version}")
    print(f"MSI version: {msi_version}")
    print(f"Description: {description}")
    
    # Template rendering
    templates = [
        ("packaging/merger.wxs.j2", "packaging/merger.wxs"),
        ("Formula/merger-cli.rb.j2", "Formula/merger-cli.rb"),
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
            msi_version=msi_version,
            description=description,
            homepage=homepage,
            tag_name=tag_name,
            sha256=sha256,
            license=license_name
        )
        
        output_path = root / t_out
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_content)
            
        print(f"Generated {output_path}")

    if errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
