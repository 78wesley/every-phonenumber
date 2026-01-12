import importlib
import os


def register_routes(app, log=False):
    # Dynamically import all route modules and register them if route starts with `rt`
    pages_dir = os.path.dirname(__file__)
    for root, dirs, files in os.walk(pages_dir):
        for file in files:
            if file == "routes.py":
                relative_path = os.path.relpath(root, pages_dir)
                module_name = relative_path.replace(os.sep, ".")
                module = importlib.import_module(f"web.pages.{module_name}.routes")
                if hasattr(module, "rt"):
                    if log:
                        print(f"Registering routes from module: {module_name}")
                        for route in module.rt.routes:
                            methods = ", ".join(route[2])
                            print(f"{route[1]} - [{methods}]")
                    module.rt.to_app(app)