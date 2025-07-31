import os
import re
from pathlib import Path

from archetypal.idfclass import IDF
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "templates"


# --- Utility to parse IDD definitions and generate stubs ---
class EppyStubGenerator:
    def __init__(self, idd_path: str, output_dir: str, template_dir: str = str(TEMPLATE_DIR)):
        self.idd_path = idd_path
        self.output_dir = output_dir
        self.idf = IDF()
        self.env = Environment(  # noqa: S701
            loader=FileSystemLoader(template_dir),
            trim_blocks=False,
            lstrip_blocks=False,
        )

    def normalize_classname(self, obj_name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "_", obj_name.title())

    def _get_numeric_limits(self, field: dict[str, list[str]]) -> dict[str, str]:
        """Return pydantic Field constraints from an IDD field definition."""
        mapping = {
            "minimum": "ge",
            "minimum>": "gt",
            "maximum": "le",
            "maximum<": "lt",
        }
        limits: dict[str, str] = {}
        for key, arg in mapping.items():
            val = field.get(key, [""])[0]
            if val not in (None, ""):
                limits[arg] = val
        return limits

    def _format_default(self, base_type: str, value: str) -> str | None:
        if value in (None, "", "none"):
            return None
        if base_type == "str" or base_type.startswith("Literal"):
            return repr(value)
        return value

    def get_field_type(self, field: dict[str, list[str]]) -> str:
        field_type = field.get("type", ["alpha"])[0]
        if field_type == "real":
            return "float"
        elif field_type == "integer":
            return "int"
        elif field_type == "choice":
            choices = field.get("key", [])
            if choices:
                return f"Literal[{', '.join(map(repr, choices))}]"
            else:
                return "str"
        else:
            return "str"

    def render_class_stub(self, obj: dict, fields: list[dict[str, list[str]]]) -> str:
        classname = self.normalize_classname(obj["idfobj"])
        class_memo = obj.get("memo", [""])[0]
        stub_fields = []
        for field in fields:
            field_name = self.normalize_classname(field["field"][0])
            base_type = self.get_field_type(field)
            limits = self._get_numeric_limits(field) if base_type in {"int", "float"} else {}
            annotation_type = base_type
            field_call = ""
            if limits:
                args = ", ".join(f"{k}={v}" for k, v in limits.items())
                annotation_type = f"Annotated[{base_type}, Field({args})]"
            default_val = self._format_default(base_type, field.get("default", [""])[0])
            field_args = []
            field_args.extend(f"{k}={v}" for k, v in limits.items())
            if default_val is not None:
                field_args.append(f"default={default_val}")
            if field_args:
                field_call = f"Field({', '.join(field_args)})"
            field_note = field.get("note", [""])[0]
            stub_fields.append({
                "name": field_name,
                "type": annotation_type,
                "note": field_note,
                "field_call": field_call,
            })
        template = self.env.get_template("common/class_stub.pyi.jinja2")
        return template.render(
            classname=classname,
            class_memo=class_memo,
            fields=stub_fields,
        )

    def generate_stubs(self):
        os.makedirs(self.output_dir, exist_ok=True)
        idd_info: list[list[dict]] = self.idf.idd_info

        for obj, *fields in idd_info[1:]:
            stub_content = self.render_class_stub(obj, fields)
            file_name = f"{self.normalize_classname(obj['idfobj'])}.pyi"
            with open(os.path.join(self.output_dir, file_name), "w") as stub_file:
                stub_file.write(stub_content)
        print(f"Stubs generated successfully in {self.output_dir}")


def classname_to_key(classname: str) -> str:
    parts = classname.split("_")
    return ":".join(part.upper() for part in parts)


def generate_overloads(stubs_dir: str, output_file: str, template_dir: str = TEMPLATE_DIR):
    env = Environment(
        autoescape=True,
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    classnames = []
    for file in os.listdir(stubs_dir):
        if file.endswith(".pyi"):
            classname = file[:-4]
            classnames.append(classname)
    overloads = [{"classname": classname, "key": classname_to_key(classname)} for classname in classnames]
    template = env.get_template("common/idf.pyi.jinja2")
    rendered = template.render(classnames=classnames, overloads=overloads)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write(rendered)


# --- Main usage example ---
if __name__ == "__main__":
    # Provide your IDD file path and desired output directory for stubs
    idd_file = "/Applications/EnergyPlus-23-1-0/Energy+.idd"
    stubs_output_dir = "./typings/eppy"

    generator = EppyStubGenerator(idd_file, stubs_output_dir)
    generator.generate_stubs()
    # generate_overloads(stubs_output_dir, "./typings/archetypal/idfclass/idf.pyi")
