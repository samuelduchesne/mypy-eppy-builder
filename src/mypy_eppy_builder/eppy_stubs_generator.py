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
            field_type = self.get_field_type(field)
            field_note = field.get("note", [""])[0]
            field_default = field.get("default", [""])[0]
            stub_fields.append({
                "name": field_name,
                "type": field_type,
                "note": field_note,
                "default": field_default,
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
    generate_overloads(stubs_output_dir, "./typings/archetypal/idfclass/idf.pyi")
