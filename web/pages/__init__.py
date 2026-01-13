import importlib
import os


def register_routes(app, debug: bool = False):
    # Dynamically import all route modules and register them if route starts with `rt`
    pages_dir = os.path.dirname(__file__)
    for root, _, files in os.walk(pages_dir):
        for file in files:
            if file == "routes.py":
                relative_path = os.path.relpath(root, pages_dir)
                module_name = relative_path.replace(os.sep, ".")
                module = importlib.import_module(f"web.pages.{module_name}.routes")
                if hasattr(module, "rt"):
                    if debug:
                        print(f"Registering routes from module: {module_name}")
                        for route in module.rt.routes:
                            if route[2]:
                                methods = ", ".join(str(method) for method in route[2])
                                print(f"{route[1]} - [{methods}]")
                    module.rt.to_app(app)