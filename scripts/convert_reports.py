#!/usr/bin/env python3
"""Convert old single-file report YAML to new folder-based structure."""

import sys
from pathlib import Path
import yaml


def convert_report(report_file: Path) -> None:
    """Convert a single-file report to folder-based structure."""
    print(f"Converting: {report_file}")
    
    # Read the old report
    with open(report_file, 'r') as f:
        report_data = yaml.safe_load(f)
    
    # Create report folder
    report_id = report_data['id']
    report_folder = report_file.parent / report_id
    report_folder.mkdir(exist_ok=True)
    
    # Extract metadata
    metadata = {
        'id': report_data['id'],
        'title': report_data['title'],
        'description': report_data.get('description'),
        'html_template_path': report_data.get('template', 'report.html.j2'),
    }
    
    if 'email' in report_data:
        metadata['email'] = report_data['email']
    
    if 'schedule' in report_data:
        metadata['schedule'] = report_data['schedule']
    
    if 'layout' in report_data:
        metadata['layout'] = report_data['layout']
    
    if 'tags' in report_data:
        metadata['tags'] = report_data['tags']
    
    # Write metadata
    metadata_file = report_folder / 'metadata.yaml'
    with open(metadata_file, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    print(f"  Created: {metadata_file}")
    
    # Extract and write components
    components = report_data.get('components', [])
    for i, component in enumerate(components, start=1):
        component_file = report_folder / f'{i:02d}_{component["id"]}.yaml'
        with open(component_file, 'w') as f:
            yaml.dump(component, f, default_flow_style=False, sort_keys=False)
        print(f"  Created: {component_file}")
    
    print(f"  ✓ Converted {len(components)} components")


def main():
    """Convert all report files in docker_integration."""
    reports_dir = Path('tests/fixtures/docker_integration/reports')
    
    if not reports_dir.exists():
        print(f"Error: {reports_dir} not found")
        sys.exit(1)
    
    # Find all .yaml files (not folders)
    report_files = [f for f in reports_dir.glob('*.yaml') if f.is_file()]
    
    if not report_files:
        print("No report files to convert")
        return
    
    print(f"Found {len(report_files)} report files to convert\n")
    
    for report_file in report_files:
        convert_report(report_file)
        print()
    
    print(f"✓ Conversion complete! Converted {len(report_files)} reports")


if __name__ == '__main__':
    main()
