"""Script to export the ReDoc documentation page into a standalone HTML file.
   ref: https://github.com/Redocly/redoc/issues/726#issuecomment-645414239
"""

import json
import argparse
from importlib import import_module

parser = argparse.ArgumentParser(description='Generate OpenAPI json spec file for a fastapi app.')
parser.add_argument('--appmodule', type=str, required=True,
                    help='Python module name with the fastapi app, e.g. my_fastapi . Must provide a package scoped app = FastAPI() variable.')
parser.add_argument('--outfile', type=str, 
                    default='fastapi-app-openapi-spec.json',
                    help='Where to write the generated Open API json spec file.')

if __name__ == "__main__":
    cli_settings = parser.parse_args()
    m = import_module(cli_settings.appmodule)
    app = m.app
    with open(cli_settings.outfile, "w") as fd:
        print(json.dumps(app.openapi()), file=fd)
